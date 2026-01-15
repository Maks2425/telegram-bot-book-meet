"""Keyboards for cleaning booking process."""

import os
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    CALENDAR_SLOT_INTERVAL_HOURS,
    CALENDAR_WORK_END,
    CALENDAR_WORK_START,
)
from services.calendar_service import generate_available_time_slots, get_calendar_service
from services.date_utils import get_next_working_days


def get_cleaning_type_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting cleaning type.
    
    Returns:
        InlineKeyboardMarkup with cleaning type options:
        - Підтримуюче
        - Генеральне
        - Після ремонту
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Підтримуюче",
                    callback_data="cleaning_type:maintenance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Генеральне",
                    callback_data="cleaning_type:deep"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Після ремонту",
                    callback_data="cleaning_type:post_renovation"
                )
            ]
        ]
    )
    return keyboard


def get_property_type_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting property type.
    
    Returns:
        InlineKeyboardMarkup with property type options:
        - Квартира
        - Будинок
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Квартира",
                    callback_data="property_type:apartment"
                ),
                InlineKeyboardButton(
                    text="Будинок",
                    callback_data="property_type:house"
                )
            ]
        ]
    )
    return keyboard


def get_book_cleaning_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with booking button.
    
    Returns:
        InlineKeyboardMarkup with "Забронювати клінінг" button.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Забронювати клінінг",
                    callback_data="book_cleaning"
                )
            ]
        ]
    )
    return keyboard


def get_date_selection_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting booking date.
    
    Returns:
        InlineKeyboardMarkup with 3-5 next working days.
    """
    working_days = get_next_working_days(count=5)
    
    buttons = []
    for day_date, formatted_date in working_days:
        # Use ISO format date string for callback_data
        date_str = day_date.isoformat()
        buttons.append([
            InlineKeyboardButton(
                text=formatted_date,
                callback_data=f"select_date:{date_str}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_time_selection_keyboard(selected_date: date) -> InlineKeyboardMarkup:
    """Create keyboard for selecting booking time.
    
    Args:
        selected_date: Selected date for booking.
        
    Returns:
        InlineKeyboardMarkup with available time slots.
    """
    # Get calendar service
    calendar_service = get_calendar_service()
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # Generate available time slots (from config)
    available_slots = generate_available_time_slots(
        date_obj=selected_date,
        calendar_service=calendar_service,
        calendar_id=calendar_id,
        work_start=CALENDAR_WORK_START,
        work_end=CALENDAR_WORK_END,
        slot_interval_hours=CALENDAR_SLOT_INTERVAL_HOURS
    )
    
    buttons = []
    for slot in available_slots:
        # Format time as HH:MM
        time_str = slot.strftime("%H:%M")
        buttons.append([
            InlineKeyboardButton(
                text=time_str,
                callback_data=f"select_time:{time_str}"
            )
        ])
    
    # If no slots available, add a message button
    if not buttons:
        buttons.append([
            InlineKeyboardButton(
                text="Немає доступних слотів",
                callback_data="no_slots_available"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

