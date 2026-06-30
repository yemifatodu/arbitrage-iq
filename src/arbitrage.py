import pandas as pd
from typing import List, Dict
from datetime import datetime
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class ArbitrageDetector:
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def detect_opportunities(self, price_data: Dict) -> List[Dict]:
        """Detect arbitrage opportunities from price data"""
        opportunities = []

        for symbol, exchanges in price_data.items():
            if len(exchanges) < 2:
                continue

            df = pd.DataFrame(exchanges)
            df = df.dropna(subset=['price'])

            if df.empty or len(df) < 2:
                continue

            min_idx = df['price'].idxmin()
            max_idx = df['price'].idxmax()

            min_row = df.loc[min_idx]
            max_row = df.loc[max_idx]

            min_price = min_row['price']
            max_price = max_row['price']
            min_exchange = min_row['exchange']
            max_exchange = max_row['exchange']

            if min_exchange == max_exchange:
                continue

            spread_pct = ((max_price - min_price) / min_price) * 100

            buy_fee = Config.TRADING_FEES.get(min_exchange, 0.001)
            sell_fee = Config.TRADING_FEES.get(max_exchange, 0.001)
            withdrawal_fee = Config.WITHDRAWAL_FEES.get(min_exchange, 0.0005)

            total_fees_pct = (buy_fee + sell_fee + withdrawal_fee) * 100
            net_profit_pct = spread_pct - total_fees_pct

            if net_profit_pct >= self.threshold:
                profit_per_coin = max_price - min_price - (min_price * total_fees_pct / 100)
                avg_volume = df['volume'].mean()

                opportunity = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'buy_exchange': min_exchange,
                    'buy_price': round(min_price, 6),
                    'sell_exchange': max_exchange,
                    'sell_price': round(max_price, 6),
                    'spread_pct': round(spread_pct, 4),
                    'fees_pct': round(total_fees_pct, 4),
                    'net_profit_pct': round(net_profit_pct, 4),
                    'profit_per_btc': round(profit_per_coin, 4),
                    'volume': round(avg_volume, 2) if avg_volume else 0,
                }
                opportunities.append(opportunity)
                logger.info(f"Opportunity: {symbol} | {min_exchange} → {max_exchange} | Net: {net_profit_pct:.2f}%")

        opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        return opportunities
