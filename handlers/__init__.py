"""Handlers package for Telegram bot."""

from handlers.callbacks import callback_handler
from handlers.cleaning import text_message_handler
from handlers.start import start_command_handler

__all__ = [
    "callback_handler",
    "start_command_handler",
    "text_message_handler",
]

