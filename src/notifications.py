import requests
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID

    def send_telegram_alert(self, message: str) -> bool:
        """Send alert via Telegram Bot API"""
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured — skipping alert.")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=payload, timeout=5)
            response.raise_for_status()
            logger.info("Telegram alert sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")
            return False

    def format_arbitrage_alert(self, opportunity: dict) -> str:
        """Format an opportunity dict into a Telegram-ready HTML message"""
        return (
            f"🚀 <b>ARBITRAGE OPPORTUNITY!</b>\n\n"
            f"💰 <b>Symbol:</b> {opportunity['symbol']}\n"
            f"📈 <b>Net Profit:</b> {opportunity['net_profit_pct']}%\n"
            f"🔄 <b>Spread:</b> {opportunity['spread_pct']}%\n\n"
            f"🟢 <b>Buy:</b> {opportunity['buy_exchange']} @ ${opportunity['buy_price']:.4f}\n"
            f"🔴 <b>Sell:</b> {opportunity['sell_exchange']} @ ${opportunity['sell_price']:.4f}\n"
            f"💵 <b>Profit per coin:</b> ${opportunity['profit_per_btc']:.4f}\n\n"
            f"⏰ {opportunity['timestamp']}"
        )
