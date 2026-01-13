"""Configuration module for Telegram bot.

This module handles loading and validation of environment variables
for secure configuration management.
"""

import os
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

