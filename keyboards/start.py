"""Start menu keyboard with inline buttons."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Create start menu inline keyboard.
    
    Returns:
        InlineKeyboardMarkup with two buttons:
        - "Розрахувати вартість"
        - "Забронювати клінінг"
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Розрахувати вартість",
                    callback_data="calculate_price"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Забронювати клінінг",
                    callback_data="book_cleaning"
                )
            ]
        ]
    )
    return keyboard

