"""Register (or inspect) the Telegram webhook.  Usage: python -m scripts.set_webhook [--info|--delete]"""
import asyncio
import sys

from aiogram import Bot

from app.config import get_settings


async def main():
    s = get_settings()
    bot = Bot(s.telegram_bot_token)
    try:
        if "--delete" in sys.argv:
            await bot.delete_webhook()
            print("webhook deleted")
        elif "--info" in sys.argv:
            i = await bot.get_webhook_info()
            print({"url": i.url, "pending": i.pending_update_count, "last_error": i.last_error_message})
        else:
            await bot.set_webhook(f"{s.public_base_url.rstrip('/')}/webhook/telegram",
                                  secret_token=s.telegram_webhook_secret, allowed_updates=["message", "callback_query"])
            print("webhook set to", f"{s.public_base_url.rstrip('/')}/webhook/telegram")
    finally:
        await bot.session.close()


asyncio.run(main())
