"""Handlers for start command and menu display."""

import logging
from typing import Final

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.start import get_start_keyboard

logger: Final[logging.Logger] = logging.getLogger(__name__)


async def show_menu(message: Message) -> None:
    """Show start menu with inline keyboard.
    
    Args:
        message: Telegram message object.
    """
    if not message.from_user:
        logger.warning("Received message without user")
        return
    
    welcome_message: str = "Вас вітає клінінгова компанія Чиста Оселя! \n\nОберіть опцію:"
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
    
    This handler processes both:
    - Command /start (typed manually or via deep link)
    - Standard Telegram "Start" button (automatically sends /start command)
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    # Clear any existing state
    await state.clear()
    await show_menu(message)

