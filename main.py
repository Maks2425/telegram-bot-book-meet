"""Main entry point for Telegram bot application.

This module initializes and runs the Telegram bot with command handlers
using aiogram 3.x framework with FSM for cleaning booking process.
"""

import asyncio
import logging
import sys
from typing import Final

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from config import get_bot_token, load_config
from keyboards.cleaning import (
    get_book_cleaning_keyboard,
    get_cleaning_type_keyboard,
    get_property_type_keyboard,
)
from keyboards.start import get_start_keyboard
from services.pricing import calculate_cleaning_price
from states import CleaningCalculationStates


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger: Final[logging.Logger] = logging.getLogger(__name__)

# Initialize bot and dispatcher (will be set in main)
bot: Bot | None = None
dp: Dispatcher | None = None


async def show_menu(message: Message) -> None:
    """Show start menu with inline keyboard.
    
    Args:
        message: Telegram message object.
    """
    if not message.from_user:
        logger.warning("Received message without user")
        return
    
    welcome_message: str = "Вітаю! Бот працює ✅\n\nОберіть опцію:"
    keyboard = get_start_keyboard()
    
    try:
        await message.answer(
            text=welcome_message,
            reply_markup=keyboard
        )
        logger.info(f"Sent welcome message to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}", exc_info=True)


async def start_command_handler(message: Message, state: FSMContext) -> None:
    """Handle the /start command.
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    # Clear any existing state
    await state.clear()
    await show_menu(message)


async def text_message_handler(message: Message, state: FSMContext) -> None:
    """Handle any text message - show menu or process FSM state.
    
    This handler catches all text messages (except commands) and either shows
    the menu or processes FSM state (like entering area).
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    # Skip if it's a command (commands are handled separately)
    if message.text and message.text.startswith('/'):
        return
    
    # Check current FSM state
    current_state = await state.get_state()
    
    # If we're in area entering state, process the area input
    if current_state == CleaningCalculationStates.entering_area:
        await process_area_input(message, state)
    else:
        # Otherwise show menu
        await show_menu(message)


async def process_area_input(message: Message, state: FSMContext) -> None:
    """Process area input with validation.
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    if not message.text:
        await message.answer("Будь ласка, введіть площу числом.")
        return
    
    try:
        area = float(message.text.strip())
        
        # Validate: must be positive number
        if area <= 0:
            await message.answer(
                "❌ Площа повинна бути більше 0. Будь ласка, введіть коректне значення:"
            )
            return
        
        # Save area to state
        await state.update_data(area_m2=area)
        
        # Get all saved data
        data = await state.get_data()
        cleaning_type = data.get("cleaning_type")
        property_type = data.get("property_type")
        
        if not cleaning_type or not property_type:
            logger.error("Missing data in FSM state")
            await message.answer("❌ Помилка: дані не збережені. Почніть спочатку.")
            await state.clear()
            await show_menu(message)
            return
        
        # Calculate price
        price_info = calculate_cleaning_price(
            cleaning_type=cleaning_type,
            property_type=property_type,
            area_m2=area
        )
        
        # Format cleaning type name
        cleaning_type_names = {
            "maintenance": "Підтримуюче",
            "deep": "Генеральне",
            "post_renovation": "Після ремонту"
        }
        
        property_type_names = {
            "apartment": "Квартира",
            "house": "Будинок"
        }
        
        # Build result message
        result_message = (
            f"✅ Розрахунок завершено!\n\n"
            f"📋 Тип прибирання: {cleaning_type_names[cleaning_type]}\n"
            f"🏠 Тип житла: {property_type_names[property_type]}\n"
            f"📐 Площа: {area} м²\n\n"
        )
        
        # Add discount information if applicable
        if price_info["discount_percent"] > 0:
            result_message += (
                f"💵 Вартість до знижки: {price_info['price_before_discount']} грн\n"
                f"🎁 Ваша знижка: {price_info['discount_percent']}% "
                f"({price_info['discount_amount']} грн)\n\n"
            )
        
        result_message += (
            f"💰 Приблизна вартість прибирання вашої оселі дорівнює "
            f"{price_info['final_price']} гривень."
        )
        
        keyboard = get_book_cleaning_keyboard()
        
        await message.answer(
            text=result_message,
            reply_markup=keyboard
        )
        
        # Clear FSM state
        await state.clear()
        
        logger.info(
            f"User {message.from_user.id} calculated price: {price_info['final_price']} UAH "
            f"(type: {cleaning_type}, property: {property_type}, area: {area}, "
            f"discount: {price_info['discount_percent']}%)"
        )
        
    except ValueError:
        await message.answer(
            "❌ Будь ласка, введіть коректне число (наприклад: 50 або 75.5):"
        )
    except Exception as e:
        logger.error(f"Error processing area input: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте ще раз.")
        await state.clear()
        await show_menu(message)


async def callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle inline keyboard callbacks.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    if not callback.from_user:
        logger.warning("Received callback without user")
        return
    
    if not callback.data:
        logger.warning("Received callback without data")
        return
    
    if not callback.message:
        logger.warning("Received callback without message")
        return
    
    callback_data: str = callback.data
    
    try:
        await callback.answer()
        
        # Handle "calculate_price" - start FSM flow
        if callback_data == "calculate_price":
            await state.set_state(CleaningCalculationStates.selecting_cleaning_type)
            await callback.message.answer(
                text="Оберіть тип прибирання:",
                reply_markup=get_cleaning_type_keyboard()
            )
            return
        
        # Handle cleaning type selection
        if callback_data.startswith("cleaning_type:"):
            cleaning_type = callback_data.split(":")[1]
            await state.update_data(cleaning_type=cleaning_type)
            await state.set_state(CleaningCalculationStates.selecting_property_type)
            
            cleaning_type_names = {
                "maintenance": "Підтримуюче",
                "deep": "Генеральне",
                "post_renovation": "Після ремонту"
            }
            
            await callback.message.answer(
                text=f"✅ Ви обрали: {cleaning_type_names.get(cleaning_type, cleaning_type)}\n\n"
                     f"Оберіть тип житла:",
                reply_markup=get_property_type_keyboard()
            )
            return
        
        # Handle property type selection
        if callback_data.startswith("property_type:"):
            property_type = callback_data.split(":")[1]
            await state.update_data(property_type=property_type)
            await state.set_state(CleaningCalculationStates.entering_area)
            
            property_type_names = {
                "apartment": "Квартира",
                "house": "Будинок"
            }
            
            await callback.message.answer(
                text=f"✅ Ви обрали: {property_type_names.get(property_type, property_type)}\n\n"
                     f"Введіть площу вашого житла у м² (наприклад: 50 або 75.5):"
            )
            return
        
        # Handle "book_cleaning" - final booking step
        if callback_data == "book_cleaning":
            await callback.message.answer(
                text="✅ Дякуємо за вибір! Ваша заявка на бронювання клінінгу прийнята.\n\n"
                     "Наш менеджер зв'яжеться з вами найближчим часом."
            )
            await state.clear()
            return
        
        # Unknown callback
        logger.warning(f"Unknown callback data: {callback_data}")
        await callback.message.answer("❌ Невідома дія.")
        
    except Exception as e:
        logger.error(f"Error handling callback: {e}", exc_info=True)
        await callback.message.answer("❌ Виникла помилка. Спробуйте ще раз.")
        await state.clear()


async def main() -> None:
    """Initialize and run the Telegram bot."""
    global bot, dp
    
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
        # Command /start shows menu
        dp.message.register(start_command_handler, Command("start"))
        # Any text message also shows menu or processes FSM state
        dp.message.register(text_message_handler)
        # Callback queries from inline buttons
        dp.callback_query.register(callback_handler)
        
        logger.info("Bot is starting...")
        
        # Start polling
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if bot:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
