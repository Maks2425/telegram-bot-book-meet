"""Handlers for inline keyboard callbacks."""

import logging
from datetime import date as date_type
from typing import Final

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.cleaning import (
    get_cleaning_type_keyboard,
    get_date_selection_keyboard,
    get_location_keyboard,
    get_property_type_keyboard,
    get_time_selection_keyboard,
)
from services.date_utils import format_date_ukrainian
from states import CleaningCalculationStates

logger: Final[logging.Logger] = logging.getLogger(__name__)


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
        
        # Route to appropriate handler based on callback data
        if callback_data == "calculate_price":
            await _handle_calculate_price(callback, state)
        elif callback_data.startswith("cleaning_type:"):
            await _handle_cleaning_type_selection(callback, state)
        elif callback_data.startswith("property_type:"):
            await _handle_property_type_selection(callback, state)
        elif callback_data == "book_cleaning":
            await _handle_book_cleaning(callback, state)
        elif callback_data.startswith("select_date:"):
            await _handle_date_selection(callback, state)
        elif callback_data.startswith("select_time:"):
            await _handle_time_selection(callback, state)
        elif callback_data == "no_slots_available":
            await _handle_no_slots_available(callback)
        elif callback_data == "no_available_days":
            await _handle_no_available_days(callback)
        else:
            logger.warning(f"Unknown callback data: {callback_data}")
            await callback.message.answer("❌ Невідома дія.")
        
    except Exception as e:
        logger.error(f"Error handling callback: {e}", exc_info=True)
        await callback.message.answer("❌ Виникла помилка. Спробуйте ще раз.")
        await state.clear()


async def _handle_calculate_price(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle calculate price callback - start FSM flow.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    await state.set_state(CleaningCalculationStates.selecting_cleaning_type)
    await callback.message.answer(
        text="Оберіть тип прибирання:",
        reply_markup=get_cleaning_type_keyboard()
    )


async def _handle_cleaning_type_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle cleaning type selection.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    cleaning_type = callback.data.split(":")[1]
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


async def _handle_property_type_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle property type selection.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    property_type = callback.data.split(":")[1]
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


async def _handle_book_cleaning(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle book cleaning callback - show date selection.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    await state.set_state(CleaningCalculationStates.selecting_date)
    await callback.message.answer(
        text="📅 Оберіть дату для бронювання:",
        reply_markup=get_date_selection_keyboard()
    )


async def _handle_date_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle date selection.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    date_str = callback.data.split(":")[1]
    try:
        selected_date = date_type.fromisoformat(date_str)
        await state.update_data(selected_date=date_str)
        
        # Format date for display
        formatted_date = format_date_ukrainian(selected_date)
        
        # Move to time selection state
        await state.set_state(CleaningCalculationStates.selecting_time)
        
        # Show time selection with selected date reminder
        await callback.message.answer(
            text=f"📅 Обрана дата: {formatted_date}\n\n"
                 f"🕐 Оберіть час для бронювання:",
            reply_markup=get_time_selection_keyboard(selected_date)
        )
    except ValueError as e:
        logger.error(f"Invalid date format: {date_str}, error: {e}")
        await callback.message.answer("❌ Помилка формату дати. Спробуйте ще раз.")


async def _handle_time_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle time selection.
    
    Args:
        callback: Telegram callback query object.
        state: FSM context.
    """
    time_str = callback.data.split(":")[1]
    await state.update_data(selected_time=time_str)
    
    # Get selected date from state
    data = await state.get_data()
    selected_date_str = data.get("selected_date")
    
    if not selected_date_str:
        await callback.message.answer("❌ Помилка: дата не збережена. Почніть спочатку.")
        await state.clear()
        return
    
    selected_date = date_type.fromisoformat(selected_date_str)
    formatted_date = format_date_ukrainian(selected_date)
    
    # Move to address entry state
    await state.set_state(CleaningCalculationStates.entering_address)
    
    location_keyboard = get_location_keyboard()
    
    await callback.message.answer(
        text=f"✅ Ви обрали:\n"
             f"📅 Дата: {formatted_date}\n"
             f"🕐 Час: {time_str}\n\n"
             f"📍 Введіть адресу для прибирання або поділіться локацією:",
        reply_markup=location_keyboard
    )


async def _handle_no_slots_available(callback: CallbackQuery) -> None:
    """Handle no slots available callback.
    
    Args:
        callback: Telegram callback query object.
    """
    await callback.message.answer(
        text="❌ На жаль, на обрану дату немає доступних часових слотів.\n\n"
             "Будь ласка, оберіть іншу дату."
    )


async def _handle_no_available_days(callback: CallbackQuery) -> None:
    """Handle no available days callback.
    
    Args:
        callback: Telegram callback query object.
    """
    await callback.message.answer(
        text="❌ На жаль, на найближчі дні немає доступних слотів для бронювання.\n\n"
             "Будь ласка, спробуйте пізніше або зв'яжіться з нами безпосередньо."
    )

