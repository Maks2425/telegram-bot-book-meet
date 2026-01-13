"""Date utilities for booking system."""

from datetime import date, timedelta
from typing import List, Tuple


def get_next_working_days(count: int = 5) -> List[Tuple[date, str]]:
    """Get next working days (excluding weekends).
    
    Args:
        count: Number of working days to return (default: 5).
        
    Returns:
        List of tuples (date, formatted_string) where formatted_string
        is in format "Пон, 1 лютого 2026".
    """
    # Ukrainian day names (abbreviated)
    day_names = {
        0: "Пон",  # Monday
        1: "Вів",  # Tuesday
        2: "Сер",  # Wednesday
        3: "Чет",  # Thursday
        4: "П'ят", # Friday
        5: "Суб",  # Saturday (excluded)
        6: "Нед"   # Sunday (excluded)
    }
    
    # Ukrainian month names
    month_names = {
        1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
        5: "травня", 6: "червня", 7: "липня", 8: "серпня",
        9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
    }
    
    working_days: List[Tuple[date, str]] = []
    current_date = date.today()
    
    # Start from tomorrow
    current_date += timedelta(days=1)
    
    while len(working_days) < count:
        # Skip weekends (Saturday = 5, Sunday = 6)
        if current_date.weekday() < 5:  # Monday to Friday (0-4)
            day_name = day_names[current_date.weekday()]
            month_name = month_names[current_date.month]
            
            formatted_date = (
                f"{day_name}, {current_date.day} {month_name} {current_date.year}"
            )
            
            working_days.append((current_date, formatted_date))
        
        current_date += timedelta(days=1)
    
    return working_days


def format_date_ukrainian(date_obj: date) -> str:
    """Format date in Ukrainian format: "Пон, 1 лютого 2026".
    
    Args:
        date_obj: Date object to format.
        
    Returns:
        Formatted date string in Ukrainian.
    """
    # Ukrainian day names (abbreviated)
    day_names = {
        0: "Пон",  # Monday
        1: "Вів",  # Tuesday
        2: "Сер",  # Wednesday
        3: "Чет",  # Thursday
        4: "П'ят", # Friday
        5: "Суб",  # Saturday
        6: "Нед"   # Sunday
    }
    
    # Ukrainian month names
    month_names = {
        1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
        5: "травня", 6: "червня", 7: "липня", 8: "серпня",
        9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
    }
    
    day_name = day_names[date_obj.weekday()]
    month_name = month_names[date_obj.month]
    
    return f"{day_name}, {date_obj.day} {month_name} {date_obj.year}"

