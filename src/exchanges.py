import ccxt
import asyncio
import logging
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger(__name__)

# ── Nigeria-accessible exchanges only ─────────────────────────────────────────
# Removed: kraken (IP blocked), coinbase (geo issues), bitfinex (unreliable)
# Kept: binance, kucoin, bybit + added okx and gateio (both work well from NG)

# ── Confirmed tradeable symbols on Binance/KuCoin/Bybit ──────────────────────
SAFE_SYMBOLS = {
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'DOGE',
    'AVAX', 'MATIC', 'LTC', 'LINK', 'UNI', 'ATOM', 'ETC',
    'TRX', 'FIL', 'NEAR', 'APT', 'OP', 'ARB', 'SUI', 'INJ',
    'SAND', 'MANA', 'AXS', 'AAVE', 'SNX', 'CRV', 'MKR'
}


class ExchangeManager:
    def __init__(self):
        self.exchanges = self._initialize_exchanges()
        self._markets_loaded = {}

    def _initialize_exchanges(self):
        """Initialize Nigeria-friendly exchanges with rate limiting"""
        return [
            ccxt.binance({'enableRateLimit': True}),
            ccxt.kucoin({'enableRateLimit': True}),
            ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}}),
            ccxt.okx({'enableRateLimit': True}),
            ccxt.gate({'enableRateLimit': True}),
        ]

    def _load_markets(self, exchange):
        """Load and cache markets for an exchange"""
        if exchange.id not in self._markets_loaded:
            try:
                exchange.load_markets()
                self._markets_loaded[exchange.id] = True
            except Exception as e:
                logger.warning(f"Could not load markets for {exchange.id}: {e}")
                self._markets_loaded[exchange.id] = False
        return self._markets_loaded.get(exchange.id, False)

    def _get_pair(self, exchange, symbol: str) -> Optional[str]:
        """Get the correct trading pair format for each exchange"""
        # OKX uses BTC/USDT:USDT format for some pairs — use spot
        pair = f"{symbol}/USDT"

        # Validate symbol exists on this exchange
        try:
            if not self._load_markets(exchange):
                return None
            if pair not in exchange.markets:
                # Try alternative quote currencies
                for quote in ['BUSD', 'USD', 'USDC']:
                    alt = f"{symbol}/{quote}"
                    if alt in exchange.markets:
                        return alt
                return None
            return pair
        except Exception:
            return None

    def _fetch_ticker_sync(self, exchange, symbol: str) -> Optional[Dict]:
        """Synchronous ticker fetch with full validation"""
        try:
            pair = self._get_pair(exchange, symbol)
            if not pair:
                return None

            ticker = exchange.fetch_ticker(pair)

            if not ticker or not ticker.get('last'):
                return None

            # Filter out low-volume pairs
            volume_usd = (ticker.get('quoteVolume') or
                          (ticker.get('volume', 0) * ticker['last']))
            if volume_usd < Config.MIN_VOLUME:
                return None

            return {
                'exchange': exchange.id,
                'symbol':   symbol,
                'price':    ticker['last'],
                'volume':   volume_usd,
                'bid':      ticker.get('bid'),
                'ask':      ticker.get('ask'),
                'timestamp': ticker.get('datetime', '')
            }

        except ccxt.BadSymbol:
            return None
        except ccxt.NetworkError as e:
            logger.warning(f"Network error on {exchange.id} for {symbol}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error fetching {symbol} from {exchange.id}: {e}")
            return None

    async def fetch_price(self, exchange, symbol: str) -> Optional[Dict]:
        """Async wrapper — runs sync ccxt call in thread executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._fetch_ticker_sync, exchange, symbol
        )

    async def get_prices_batch(self, symbols: List[str]) -> Dict:
        """
        Fetch prices from all exchanges concurrently.
        Filters to SAFE_SYMBOLS automatically to avoid bad pair errors.
        """
        # Only scan symbols we know are tradeable
        clean_symbols = [s for s in symbols if s.upper() in SAFE_SYMBOLS]

        if not clean_symbols:
            logger.warning("No valid symbols after filtering. Using default safe list.")
            clean_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']

        results = {}
        tasks = [
            self.fetch_price(exchange, symbol)
            for exchange in self.exchanges
            for symbol in clean_symbols
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                logger.debug(f"Task exception: {response}")
                continue
            if response:
                symbol = response['symbol']
                if symbol not in results:
                    results[symbol] = []
                results[symbol].append(response)

        # Log summary
        found = sum(len(v) for v in results.values())
        logger.info(f"Fetched {found} prices across {len(results)} symbols")

        return results

    def get_exchange_names(self) -> List[str]:
        """Return list of active exchange names for display"""
        return [ex.id for ex in self.exchanges]