"""Configuration module for Telegram bot.

This module handles loading and validation of environment variables
for secure configuration management.
"""

import os
from datetime import time
from typing import Optional

from dotenv import load_dotenv


def load_config() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


def get_bot_token() -> str:
    """Get Telegram bot token from environment variable.
    
    Returns:
        Bot token string.
        
    Raises:
        ValueError: If BOT_TOKEN is not set in environment variables.
    """
    token: Optional[str] = os.getenv("BOT_TOKEN")
    
    if not token:
        raise ValueError(
            "BOT_TOKEN environment variable is not set. "
            "Please create a .env file with BOT_TOKEN=your_token_here"
        )
    
    if not token.strip():
        raise ValueError("BOT_TOKEN cannot be empty")
    
    return token


# Calendar Configuration
CALENDAR_TIMEZONE: str = "Europe/Stockholm"
CALENDAR_WORK_START: time = time(8, 0)  # 8:00 AM
CALENDAR_WORK_END: time = time(18, 0)    # 6:00 PM (18:00)
CALENDAR_SLOT_INTERVAL_HOURS: int = 2    # Interval between time slots
CALENDAR_CLEANING_DURATION_HOURS: int = 2  # Duration of cleaning appointment

