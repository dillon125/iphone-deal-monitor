import html
import logging
import os

import requests


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 15) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_listing(self, title: str, price: str, location: str, url: str) -> bool:
        safe_title = html.escape(title)
        safe_price = html.escape(price)
        safe_location = html.escape(location)
        safe_url = html.escape(url)

        message = (
            "🚨 <b>NEW DEAL FOUND</b>\n\n"
            f"📱 <b>Title:</b> {safe_title}\n"
            f"💰 <b>Price:</b> {safe_price}\n"
            f"📍 <b>Area:</b> {safe_location}\n\n"
            "🔗 <b>View Listing:</b>\n"
            f"<a href=\"{safe_url}\">{safe_url}</a>"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok", False):
                logging.error("Telegram API returned non-ok response: %s", data)
                return False
            return True
        except requests.RequestException as exc:
            logging.error("Failed to send Telegram notification: %s", exc)
            return False


def notifier_from_env() -> TelegramNotifier:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment")

    return TelegramNotifier(bot_token=bot_token, chat_id=chat_id)
