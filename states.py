"""FSM states for cleaning booking process."""

from aiogram.fsm.state import State, StatesGroup


class CleaningCalculationStates(StatesGroup):
    """States for cleaning cost calculation flow."""
    
    # Step 1: Select cleaning type
    selecting_cleaning_type = State()
    
    # Step 2: Select property type
    selecting_property_type = State()
    
    # Step 3: Enter area
    entering_area = State()

