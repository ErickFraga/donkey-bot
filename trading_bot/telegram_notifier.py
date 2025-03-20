import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Bot(token=self.bot_token)

    def send_message(self, message):
        """Send a message to the configured chat"""
        try:
            asyncio.run(self._send_message_async(message))
        except TelegramError as e:
            print(f"Error sending Telegram message: {str(e)}")

    async def _send_message_async(self, message):
        """Async method to send message"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='HTML'
        ) 