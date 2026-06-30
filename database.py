import sqlite3
import pandas as pd
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="data/arbitrage.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    buy_exchange TEXT,
                    sell_exchange TEXT,
                    buy_price REAL,
                    sell_price REAL,
                    spread_pct REAL,
                    fees_pct REAL,
                    net_profit_pct REAL,
                    profit_per_btc REAL,
                    volume REAL
                )
            ''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON opportunities(timestamp DESC)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON opportunities(symbol)')
            conn.commit()
            conn.close()
            logger.info("Database initialized.")
        except Exception as e:
            logger.error(f"Database init failed: {e}")

    def save_opportunity(self, opportunity: dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO opportunities (
                    timestamp, symbol, buy_exchange, sell_exchange,
                    buy_price, sell_price, spread_pct, fees_pct,
                    net_profit_pct, profit_per_btc, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opportunity.get('timestamp', datetime.now().isoformat()),
                opportunity['symbol'],
                opportunity['buy_exchange'],
                opportunity['sell_exchange'],
                opportunity['buy_price'],
                opportunity['sell_price'],
                opportunity['spread_pct'],
                opportunity['fees_pct'],
                opportunity['net_profit_pct'],
                opportunity['profit_per_btc'],
                opportunity.get('volume', 0)
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save opportunity: {e}")
            return False

    def get_history(self, limit: int = 100) -> pd.DataFrame:
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                f"SELECT * FROM opportunities ORDER BY timestamp DESC LIMIT {limit}",
                conn
            )
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            return pd.DataFrame()

    def get_statistics(self) -> dict:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM opportunities')
            total = c.fetchone()[0] or 0
            c.execute('SELECT AVG(net_profit_pct) FROM opportunities')
            avg = c.fetchone()[0]
            c.execute('SELECT MAX(net_profit_pct) FROM opportunities')
            best = c.fetchone()[0]
            conn.close()
            return {
                'total_opportunities': total,
                'avg_profit': round(avg, 4) if avg else 0.0,
                'best_profit': round(best, 4) if best else 0.0,
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def export_to_csv(self):
        df = self.get_history(limit=10000)
        if not df.empty:
            return df.to_csv(index=False)
        return None

    def clear_data(self) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('DELETE FROM opportunities')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            return False
