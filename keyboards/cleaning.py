"""Keyboards for cleaning booking process."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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

