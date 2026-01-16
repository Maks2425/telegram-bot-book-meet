"""Configuration module for Telegram bot.

This module handles loading and validation of environment variables
for secure configuration management.
"""

import os
from datetime import time
from typing import Optional

from dotenv import load_dotenv


def load_config() -> None:
    """Load environment variables from .env file (if exists).
    
    This function attempts to load .env file for local development.
    On deployment platforms (Railway, Render, etc.), environment variables
    are set directly through the platform's interface, so .env file is not required.
    
    Note:
        This function does not raise an error if .env file doesn't exist,
        as it's expected on deployment platforms.
    """
    import pathlib
    
    env_file = pathlib.Path(".env")
    if env_file.exists():
        # Load .env file for local development
        load_dotenv()
    else:
        # On deployment platforms, environment variables are set directly
        # Try to load anyway (load_dotenv won't fail if file doesn't exist)
        load_dotenv()


def get_bot_token() -> str:
    """Get Telegram bot token from environment variable.
    
    Returns:
        Bot token string.
        
    Raises:
        ValueError: If BOT_TOKEN is not set in environment variables or invalid.
    """
    token: Optional[str] = os.getenv("BOT_TOKEN")
    
    if not token:
        raise ValueError(
            "BOT_TOKEN environment variable is not set.\n"
            "For local development: Create a .env file with BOT_TOKEN=your_token_here\n"
            "For deployment: Set BOT_TOKEN environment variable in your hosting platform"
        )
    
    token = token.strip()
    
    if not token:
        raise ValueError("BOT_TOKEN cannot be empty")
    
    # Basic validation: Telegram bot tokens typically have format: numbers:letters
    # Example: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
    if ':' not in token:
        raise ValueError(
            "BOT_TOKEN format appears invalid. "
            "Telegram bot tokens should have format: 'number:letters'. "
            "Please check your token from @BotFather."
        )
    
    parts = token.split(':', 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
        raise ValueError(
            "BOT_TOKEN format appears invalid. "
            "Telegram bot tokens should have format: 'number:letters'. "
            "Please check your token from @BotFather."
        )
    
    return token


def get_owner_telegram_id() -> Optional[int]:
    """Get owner Telegram ID from environment variable.
    
    Returns:
        Owner Telegram ID as integer, or None if not set.
        
    Note:
        This is optional - if not set, owner notifications will be skipped.
    """
    owner_id_str: Optional[str] = os.getenv("OWNER_TELEGRAM_ID")
    
    if not owner_id_str:
        return None
    
    try:
        return int(owner_id_str.strip())
    except ValueError:
        return None


# Calendar Configuration
CALENDAR_TIMEZONE: str = "Europe/Stockholm"
CALENDAR_WORK_START: time = time(8, 0)  # 8:00 AM
CALENDAR_WORK_END: time = time(18, 0)    # 6:00 PM (18:00)
CALENDAR_SLOT_INTERVAL_HOURS: int = 2    # Interval between time slots
CALENDAR_CLEANING_DURATION_HOURS: int = 2  # Duration of cleaning appointment

