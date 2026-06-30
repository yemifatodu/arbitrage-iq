import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram credentials from environment
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Trading fees by exchange (maker/taker)
    TRADING_FEES = {
        'binance': 0.001,
        'kucoin': 0.001,
        'kraken': 0.0026,
        'coinbase': 0.005,
        'bitfinex': 0.002,
        'bybit': 0.001,
        'bitbns': 0.0025
    }

    # Withdrawal fees (average)
    WITHDRAWAL_FEES = {
        'binance': 0.0005,
        'kucoin': 0.0005,
        'kraken': 0.001,
        'coinbase': 0.001,
        'bitfinex': 0.0008,
        'bybit': 0.0005,
        'bitbns': 0.001
    }

    # Minimum volume threshold (USD)
    MIN_VOLUME = 100000

    # Database path
    DB_PATH = "data/arbitrage.db"
