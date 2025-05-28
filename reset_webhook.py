import os
from telegram import Bot
from config import config

async def reset_webhook():
    bot = Bot(token=config.telegram_token)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook reset successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(reset_webhook()) 