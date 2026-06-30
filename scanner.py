"""
scanner.py — ArbitrageIQ Background Scanner
Run independently of Streamlit:
    python scanner.py --interval 10

Scans exchanges every N minutes, saves to DB, sends Telegram alerts.
"""

import asyncio
import argparse
import logging
import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from src.exchanges import ExchangeManager
from src.arbitrage import ArbitrageDetector
from src.notifications import NotificationManager
from src.config import Config
from database import DatabaseManager

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scanner.log', encoding='utf-8'),
        logging.StreamHandler(open(1, "w", encoding="utf-8", closefd=False))
    ]
)
logger = logging.getLogger(__name__)

# ── Coins to scan ─────────────────────────────────────────────────────────────
SCAN_SYMBOLS = [
    # Major — wide coverage
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP',
    # Mid-cap — wider spreads
    'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK',
    'NEAR', 'INJ', 'ARB', 'OP', 'APT',
    'SUI', 'TRX', 'ATOM', 'FIL', 'LTC',
    # Small-cap — best arbitrage potential
    'SAND', 'MANA', 'AXS', 'AAVE', 'CRV',
    'SNX', 'UNI', 'MKR', 'DOGE', 'ETC',
]


def format_telegram_alert(opp: dict, scan_time: str) -> str:
    """Format a rich Telegram alert message"""
    profit_emoji = "🟢" if opp['net_profit_pct'] >= 1.0 else "🟡"
    arrow = "→"

    msg = (
        f"{profit_emoji} *ARBITRAGE OPPORTUNITY*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Pair:* `{opp['symbol']}/USDT`\n"
        f"*Route:* `{opp['buy_exchange'].upper()}` {arrow} `{opp['sell_exchange'].upper()}`\n"
        f"\n"
        f"💰 *Prices*\n"
        f"  Buy:  `${opp['buy_price']:,.4f}` on {opp['buy_exchange']}\n"
        f"  Sell: `${opp['sell_price']:,.4f}` on {opp['sell_exchange']}\n"
        f"\n"
        f"📊 *Metrics*\n"
        f"  Spread:      `{opp['spread_pct']:.3f}%`\n"
        f"  Fees:        `{opp['fees_pct']:.3f}%`\n"
        f"  *Net Profit: `{opp['net_profit_pct']:.3f}%`*\n"
        f"  Per coin:    `${opp['profit_per_btc']:.4f}`\n"
        f"  Volume:      `${opp['volume']:,.0f}`\n"
        f"\n"
        f"🕐 `{scan_time}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_ArbitrageIQ · yemifatodu.online_"
    )
    return msg


def format_summary_alert(opportunities: list, scan_time: str, elapsed: float) -> str:
    """Format a scan summary if no opportunities found"""
    msg = (
        f"📡 *SCAN COMPLETE — No Opportunities*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Symbols scanned: `{len(SCAN_SYMBOLS)}`\n"
        f"Exchanges: `5` (Binance, KuCoin, Bybit, OKX, Gate)\n"
        f"Opportunities: `0`\n"
        f"Duration: `{elapsed:.1f}s`\n"
        f"🕐 `{scan_time}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Next scan scheduled automatically_"
    )
    return msg


async def run_scan(
    exchange_manager: ExchangeManager,
    detector: ArbitrageDetector,
    notifier: NotificationManager,
    database: DatabaseManager,
    threshold: float,
    notify: bool,
    silent_if_none: bool = True
):
    """Run a single scan cycle"""
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    t_start = time.time()

    logger.info(f"-- SCAN STARTED -- {scan_time}")

    try:
        # Fetch prices
        price_data = await exchange_manager.get_prices_batch(SCAN_SYMBOLS)
        total_prices = sum(len(v) for v in price_data.values())
        logger.info(f"Fetched {total_prices} prices across {len(price_data)} symbols")

        # Detect opportunities
        opportunities = detector.detect_opportunities(price_data)
        elapsed = time.time() - t_start

        if opportunities:
            logger.info(f"[OK] {len(opportunities)} opportunities found in {elapsed:.1f}s")

            for opp in opportunities:
                # Save to DB
                database.save_opportunity(opp)
                logger.info(
                    f"  {opp['symbol']} | {opp['buy_exchange']} → {opp['sell_exchange']} "
                    f"| Net: {opp['net_profit_pct']:.3f}%"
                )

                # Send Telegram alert
                if notify and Config.TELEGRAM_TOKEN and Config.TELEGRAM_CHAT_ID:
                    msg = format_telegram_alert(opp, scan_time)
                    notifier.send_telegram_alert(msg)
                    time.sleep(0.5)  # avoid Telegram rate limit

        else:
            logger.info(f"[INFO] No opportunities above {threshold}% threshold ({elapsed:.1f}s)")

            # Send summary only if configured
            if notify and not silent_if_none and Config.TELEGRAM_TOKEN:
                msg = format_summary_alert(opportunities, scan_time, elapsed)
                notifier.send_telegram_alert(msg)

        return len(opportunities)

    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        return 0


def main():
    parser = argparse.ArgumentParser(description='ArbitrageIQ Background Scanner')
    parser.add_argument('--interval',    type=int,   default=10,
                        help='Scan interval in minutes (default: 10)')
    parser.add_argument('--threshold',   type=float, default=0.15,
                        help='Minimum net profit %% (default: 0.15)')
    parser.add_argument('--notify',      action='store_true', default=True,
                        help='Send Telegram alerts (default: True)')
    parser.add_argument('--silent-none', action='store_true', default=True,
                        help='Skip Telegram alert when no opportunities found')
    parser.add_argument('--once',        action='store_true',
                        help='Run once and exit (no loop)')
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("  ArbitrageIQ Background Scanner")
    logger.info(f"  Interval:  {args.interval} minutes")
    logger.info(f"  Threshold: {args.threshold}%")
    logger.info(f"  Telegram:  {'ON' if args.notify and Config.TELEGRAM_TOKEN else 'OFF'}")
    logger.info(f"  Symbols:   {len(SCAN_SYMBOLS)}")
    logger.info("=" * 50)

    # Init components
    exchange_manager = ExchangeManager()
    detector         = ArbitrageDetector(threshold=args.threshold)
    notifier         = NotificationManager()
    database         = DatabaseManager()

    interval_sec = args.interval * 60

    if args.once:
        # Single scan
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        count = loop.run_until_complete(
            run_scan(exchange_manager, detector, notifier, database,
                     args.threshold, args.notify, args.silent_none)
        )
        loop.close()
        logger.info(f"Single scan complete. {count} opportunities found.")
        return

    # Continuous loop
    scan_count = 0
    total_opps = 0

    while True:
        scan_count += 1
        logger.info(f"\n{'='*50}")
        logger.info(f"SCAN #{scan_count}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            count = loop.run_until_complete(
                run_scan(exchange_manager, detector, notifier, database,
                         args.threshold, args.notify, args.silent_none)
            )
            total_opps += count
        finally:
            loop.close()

        next_scan = datetime.fromtimestamp(time.time() + interval_sec)
        logger.info(f"Total opportunities so far: {total_opps}")
        logger.info(f"Next scan at: {next_scan.strftime('%H:%M:%S')}")
        logger.info(f"Sleeping {args.interval} minutes...")

        time.sleep(interval_sec)


if __name__ == '__main__':
    main()
