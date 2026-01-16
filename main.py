"""Main entry point for Telegram bot application.

This module initializes and runs the Telegram bot with command handlers
using aiogram 3.x framework with FSM for cleaning booking process.
"""

import asyncio
import logging
import sys
from typing import Final

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_bot_token, load_config
from handlers import (
    callback_handler,
    location_message_handler,
    start_command_handler,
    text_message_handler,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger: Final[logging.Logger] = logging.getLogger(__name__)


async def main() -> None:
    """Initialize and run the Telegram bot."""
    bot: Bot | None = None
    
    try:
        # Load configuration from .env file
        load_config()
        
        # Get bot token from environment
        bot_token: str = get_bot_token()
        
        # Initialize storage for FSM
        storage = MemoryStorage()
        
        # Initialize bot and dispatcher
        bot = Bot(token=bot_token)
        dp = Dispatcher(storage=storage)
        
        # Register handlers
        dp.message.register(start_command_handler, Command("start"))
        dp.message.register(location_message_handler, F.content_type == ContentType.LOCATION)
        dp.message.register(text_message_handler)
        dp.callback_query.register(callback_handler)
        
        logger.info("Bot is starting...")
        
        # Start polling
        await dp.start_polling(bot)
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error(
            "\n💡 Підказка:\n"
            "1. Перевірте, чи існує файл .env в корені проекту\n"
            "2. Переконайтеся, що в .env файлі є рядок: BOT_TOKEN=ваш_токен\n"
            "3. Отримайте токен від @BotFather в Telegram\n"
            "4. Переконайтеся, що токен скопійовано повністю без пробілів"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        error_msg = str(e)
        if "Not Found" in error_msg or "TelegramNotFound" in error_msg:
            logger.error(f"❌ Помилка підключення до Telegram API: {e}")
            logger.error(
                "\n💡 Можливі причини:\n"
                "1. Невірний BOT_TOKEN - перевірте токен в .env файлі\n"
                "2. Токен був відкликаний або видалений в @BotFather\n"
                "3. Пробіли або зайві символи в токені\n"
                "4. Файл .env не завантажується правильно\n\n"
                "Рішення:\n"
                "1. Відкрийте @BotFather в Telegram\n"
                "2. Використайте команду /token або /mybots\n"
                "3. Отримайте новий токен\n"
                "4. Оновіть BOT_TOKEN в .env файлі"
            )
        else:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if bot:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
