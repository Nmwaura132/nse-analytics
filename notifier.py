import asyncio
from telegram import Bot
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat_id not provided. Notifications will be disabled (printed to console).")
            self.bot = None
        else:
            self.bot = Bot(token=self.token)

    async def send_message(self, message):
        """
        Sends a message to the configured Telegram chat.
        """
        if self.bot:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
                logger.info("Telegram message sent successfully.")
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
        else:
            try:
                print(f"\n[MOCK TELEGRAM] Message to {self.chat_id}:\n{message}\n")
            except UnicodeEncodeError:
                print(f"\n[MOCK TELEGRAM] Message to {self.chat_id}:\n{message.encode('ascii', 'ignore').decode()}\n")

if __name__ == "__main__":
    # Test
    async def test():
        notifier = TelegramNotifier() # Will try to load from env
        await notifier.send_message("Test message from NSE Bot!")

    asyncio.run(test())
