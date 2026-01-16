"""Handlers for cleaning booking process (FSM states)."""

import logging
import os
from datetime import date as date_type, datetime, timedelta, time as time_type
from typing import Final

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from zoneinfo import ZoneInfo

from config import (
    CALENDAR_CLEANING_DURATION_HOURS,
    CALENDAR_TIMEZONE,
    get_owner_telegram_id,
)
from keyboards.cleaning import get_book_cleaning_keyboard
from keyboards.start import get_start_keyboard
from services.calendar_service import create_calendar_event, get_calendar_service
from services.date_utils import format_date_ukrainian
from services.pricing import calculate_cleaning_price
from states import CleaningCalculationStates

logger: Final[logging.Logger] = logging.getLogger(__name__)


async def location_message_handler(message: Message, state: FSMContext) -> None:
    """Handle location messages.
    
    Args:
        message: Telegram message object with location.
        state: FSM context.
    """
    if not message.location:
        return
    
    logger.info(f"Received location from user {message.from_user.id}: {message.location.latitude}, {message.location.longitude}")
    
    current_state = await state.get_state()
    if current_state == CleaningCalculationStates.entering_address:
        await process_location_input(message, state)
    else:
        # Location shared outside of address entry state
        await message.answer("📍 Будь ласка, поділіться локацією після вибору часу бронювання.")


async def text_message_handler(message: Message, state: FSMContext) -> None:
    """Handle any text message - show menu or process FSM state.
    
    This handler catches all text messages (except commands) and either shows
    the menu or processes FSM state (like entering area or address).
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    # Skip if it's a command (commands are handled separately)
    if message.text and message.text.startswith('/'):
        return
    
    # Skip location messages (they are handled separately)
    if message.location:
        return
    
    # Check current FSM state
    current_state = await state.get_state()
    
    # Route to appropriate handler based on state
    if current_state == CleaningCalculationStates.entering_area:
        await process_area_input(message, state)
    elif current_state == CleaningCalculationStates.entering_address:
        await process_address_input(message, state)
    else:
        # Otherwise show menu
        from handlers.start import show_menu
        await show_menu(message)


async def process_area_input(message: Message, state: FSMContext) -> None:
    """Process area input with validation.
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    if not message.text:
        await message.answer("Будь ласка, введіть площу числом.")
        return
    
    try:
        area = float(message.text.strip())
        
        # Validate: must be positive number
        if area <= 0:
            await message.answer(
                "❌ Площа повинна бути більше 0. Будь ласка, введіть коректне значення:"
            )
            return
        
        # Get existing data first
        data = await state.get_data()
        cleaning_type = data.get("cleaning_type")
        property_type = data.get("property_type")
        
        # Save area to state
        await state.update_data(area_m2=area)
        
        if not cleaning_type or not property_type:
            logger.error("Missing data in FSM state")
            await message.answer("❌ Помилка: дані не збережені. Почніть спочатку.")
            await state.clear()
            from handlers.start import show_menu
            await show_menu(message)
            return
        
        # Calculate price
        price_info = calculate_cleaning_price(
            cleaning_type=cleaning_type,
            property_type=property_type,
            area_m2=area
        )
        
        # Format cleaning type name
        cleaning_type_names = {
            "maintenance": "Підтримуюче",
            "deep": "Генеральне",
            "post_renovation": "Після ремонту"
        }
        
        property_type_names = {
            "apartment": "Квартира",
            "house": "Будинок"
        }
        
        # Build result message
        result_message = (
            f"✅ Розрахунок завершено!\n\n"
            f"📋 Тип прибирання: {cleaning_type_names[cleaning_type]}\n"
            f"🏠 Тип житла: {property_type_names[property_type]}\n"
            f"📐 Площа: {area} м²\n\n"
        )
        
        # Add discount information if applicable
        if price_info["discount_percent"] > 0:
            result_message += (
                f"💵 Вартість до знижки: {price_info['price_before_discount']} грн\n"
                f"🎁 Ваша знижка: {price_info['discount_percent']}% "
                f"({price_info['discount_amount']} грн)\n\n"
            )
        
        result_message += (
            f"💰 Приблизна вартість прибирання вашої оселі дорівнює "
            f"{price_info['final_price']} гривень."
        )
        
        keyboard = get_book_cleaning_keyboard()
        
        await message.answer(
            text=result_message,
            reply_markup=keyboard
        )
        
        # Don't clear FSM state here - we need the data for booking
        # Ensure all data is saved in state
        await state.update_data(
            cleaning_type=cleaning_type,
            property_type=property_type,
            area_m2=area
        )
        
        logger.info(
            f"User {message.from_user.id} calculated price: {price_info['final_price']} UAH "
            f"(type: {cleaning_type}, property: {property_type}, area: {area}, "
            f"discount: {price_info['discount_percent']}%)"
        )
        
    except ValueError:
        await message.answer(
            "❌ Будь ласка, введіть коректне число (наприклад: 50 або 75.5):"
        )
    except Exception as e:
        logger.error(f"Error processing area input: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте ще раз.")
        await state.clear()
        from handlers.start import show_menu
        await show_menu(message)


async def process_location_input(message: Message, state: FSMContext) -> None:
    """Process location input and convert to address.
    
    Args:
        message: Telegram message object with location.
        state: FSM context.
    """
    if not message.location:
        await message.answer("❌ Помилка: локація не отримана. Спробуйте ще раз.")
        return
    
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    
    # Format address for display (with emoji for user)
    address_display = f"📍 Координати: {latitude:.6f}, {longitude:.6f}"
    
    # Format address for calendar (just coordinates)
    address_calendar = f"{latitude:.6f}, {longitude:.6f}"
    
    # Save both addresses and coordinates to state
    await state.update_data(
        address=address_display,  # For user display
        address_calendar=address_calendar,  # For Google Calendar
        location_latitude=latitude,
        location_longitude=longitude
    )
    
    # Remove location keyboard
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        text=f"✅ Локацію отримано!\n\n{address_display}\n\nОбробляю замовлення...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Continue with booking process
    await _complete_booking(message, state)


async def process_address_input(message: Message, state: FSMContext) -> None:
    """Process address input and create calendar event.
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    if not message.text:
        await message.answer("Будь ласка, введіть адресу текстом.")
        return
    
    address = message.text.strip()
    
    if len(address) < 5:
        await message.answer("❌ Адреса занадто коротка. Будь ласка, введіть повну адресу:")
        return
    
    # Save address to state (for both display and calendar)
    await state.update_data(
        address=address,
        address_calendar=address  # For text addresses, use the same value
    )
    
    # Remove location keyboard if it was shown
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        text="✅ Адресу збережено!\n\nОбробляю замовлення...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Continue with booking process
    await _complete_booking(message, state)


async def _complete_booking(message: Message, state: FSMContext) -> None:
    """Complete booking process - create summary, calendar event, and notify owner.
    
    Args:
        message: Telegram message object.
        state: FSM context.
    """
    # Get all booking data
    data = await state.get_data()
    
    # Log all data for debugging
    logger.info(f"FSM data for user {message.from_user.id}: {data}")
    
    selected_date_str = data.get("selected_date")
    selected_time = data.get("selected_time")
    cleaning_type = data.get("cleaning_type")
    property_type = data.get("property_type")
    area_m2 = data.get("area_m2")
    address = data.get("address")  # Display address for user
    address_calendar = data.get("address_calendar")  # Calendar address (coordinates only)
    
    if not address:
        logger.error("Address not found in FSM state")
        await message.answer("❌ Помилка: адреса не збережена. Почніть спочатку.")
        await state.clear()
        from handlers.start import show_menu
        await show_menu(message)
        return
    
    # Use calendar address if available (for coordinates), otherwise use display address
    calendar_address = address_calendar if address_calendar else address
    
    # Format cleaning type name
    cleaning_type_names = {
        "maintenance": "Підтримуюче",
        "deep": "Генеральне",
        "post_renovation": "Після ремонту"
    }
    
    property_type_names = {
        "apartment": "Квартира",
        "house": "Будинок"
    }
    
    if selected_date_str:
        selected_date = date_type.fromisoformat(selected_date_str)
        formatted_date = format_date_ukrainian(selected_date)
    else:
        formatted_date = "Не вказано"
    
    # Build summary message - only include available data
    summary_parts = ["✅ Бронювання підтверджено!\n\n📋 Деталі замовлення:"]
    
    if cleaning_type:
        summary_parts.append(f"• Тип прибирання: {cleaning_type_names.get(cleaning_type, cleaning_type)}")
    
    if property_type:
        summary_parts.append(f"• Тип житла: {property_type_names.get(property_type, property_type)}")
    
    if area_m2:
        summary_parts.append(f"• Площа: {area_m2} м²")
    
    if formatted_date != "Не вказано":
        summary_parts.append(f"• Дата: {formatted_date}")
    
    if selected_time:
        summary_parts.append(f"• Час: {selected_time}")
    
    summary_parts.append(f"• Адреса: {address}")
    summary_parts.append("\n✅ Дякуємо за замовлення! Наш менеджер зв'яжеться з вами найближчим часом для підтвердження.")
    
    summary_message = "\n".join(summary_parts)
    
    await message.answer(text=summary_message)
    
    # Create calendar event
    await _create_calendar_event(
        message=message,
        selected_date_str=selected_date_str,
        selected_time=selected_time,
        cleaning_type=cleaning_type,
        property_type=property_type,
        area_m2=area_m2,
        address=calendar_address,  # Use calendar address (coordinates only for location)
        cleaning_type_names=cleaning_type_names,
        property_type_names=property_type_names
    )
    
    # Send notification to owner
    await _notify_owner(
        bot=message.bot,
        client_username=message.from_user.username,
        client_id=message.from_user.id,
        cleaning_type=cleaning_type,
        property_type=property_type,
        area_m2=area_m2,
        selected_date_str=selected_date_str,
        selected_time=selected_time,
        address=address,
        cleaning_type_names=cleaning_type_names,
        property_type_names=property_type_names
    )
    
    # Log booking
    logger.info(
        f"User {message.from_user.id} completed booking. "
        f"Date: {selected_date_str}, Time: {selected_time}, Address: {address}"
    )
    
    # Clear FSM state
    await state.clear()


async def _create_calendar_event(
    message: Message,
    selected_date_str: str | None,
    selected_time: str | None,
    cleaning_type: str | None,
    property_type: str | None,
    area_m2: float | None,
    address: str,
    cleaning_type_names: dict[str, str],
    property_type_names: dict[str, str]
) -> None:
    """Create calendar event for booking.
    
    Args:
        message: Telegram message object.
        selected_date_str: Selected date in ISO format.
        selected_time: Selected time string.
        cleaning_type: Cleaning type.
        property_type: Property type.
        area_m2: Area in square meters.
        address: Booking address.
        cleaning_type_names: Mapping of cleaning type codes to names.
        property_type_names: Mapping of property type codes to names.
    """
    if not selected_date_str or not selected_time:
        return
    
    try:
        # Parse date and time
        selected_date = date_type.fromisoformat(selected_date_str)
        
        # Parse time - handle both "10:00" and "10" formats
        time_parts = selected_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Create datetime objects with timezone
        tz = ZoneInfo(CALENDAR_TIMEZONE)
        start_datetime = datetime.combine(selected_date, time_type(hour, minute), tzinfo=tz)
        end_datetime = start_datetime + timedelta(hours=CALENDAR_CLEANING_DURATION_HOURS)
        
        # Format event details - only include available data
        event_title_parts = ["Прибирання"]
        event_description_parts = []
        
        # Add cleaning type if available
        if cleaning_type:
            cleaning_type_display = cleaning_type_names.get(cleaning_type, cleaning_type)
            event_title_parts.append(cleaning_type_display)
            event_description_parts.append(f"Тип прибирання: {cleaning_type_display}")
        
        # Add property type if available
        if property_type:
            property_type_display = property_type_names.get(property_type, property_type)
            if cleaning_type:
                event_title_parts.append(f"({property_type_display})")
            else:
                event_title_parts.append(property_type_display)
            event_description_parts.append(f"Тип житла: {property_type_display}")
        
        # Add area if available
        if area_m2:
            event_description_parts.append(f"Площа: {area_m2} м²")
        
        # Always add client info
        client_username = message.from_user.username if message.from_user.username else 'без username'
        event_description_parts.append(f"Клієнт: @{client_username}")
        event_description_parts.append(f"Telegram ID: {message.from_user.id}")
        
        # Build title and description
        event_title = " ".join(event_title_parts)
        event_description = "\n".join(event_description_parts)
        
        # Get calendar service
        calendar_service = get_calendar_service()
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        
        # Create event
        event_id = create_calendar_event(
            calendar_service=calendar_service,
            calendar_id=calendar_id,
            title=event_title,
            description=event_description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=address
        )
        
        if event_id:
            logger.info(
                f"Calendar event created successfully. Event ID: {event_id} "
                f"for user {message.from_user.id}"
            )
        else:
            logger.warning(
                f"Failed to create calendar event for user {message.from_user.id}. "
                f"Booking data saved but event not created."
            )
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}", exc_info=True)
        # Don't fail the booking if calendar creation fails


async def _notify_owner(
    bot,
    client_username: str | None,
    client_id: int,
    cleaning_type: str | None,
    property_type: str | None,
    area_m2: float | None,
    selected_date_str: str | None,
    selected_time: str | None,
    address: str,
    cleaning_type_names: dict[str, str],
    property_type_names: dict[str, str]
) -> None:
    """Send booking notification to owner.
    
    Args:
        bot: Bot instance for sending messages.
        client_username: Client's Telegram username.
        client_id: Client's Telegram ID.
        cleaning_type: Cleaning type code.
        property_type: Property type code.
        area_m2: Area in square meters.
        selected_date_str: Selected date in ISO format.
        selected_time: Selected time string.
        address: Booking address.
        cleaning_type_names: Mapping of cleaning type codes to names.
        property_type_names: Mapping of property type codes to names.
    """
    owner_id = get_owner_telegram_id()
    
    if not owner_id:
        logger.debug("OWNER_TELEGRAM_ID not set, skipping owner notification")
        return
    
    try:
        # Build notification message
        notification_parts = ["🔔 НОВЕ БРОНЮВАННЯ\n"]
        
        # Client info
        client_display = f"@{client_username}" if client_username else f"ID: {client_id}"
        notification_parts.append(f"👤 Клієнт: {client_display}")
        notification_parts.append(f"🆔 Telegram ID: {client_id}\n")
        
        # Booking details
        notification_parts.append("📋 Деталі замовлення:")
        
        if cleaning_type:
            cleaning_type_display = cleaning_type_names.get(cleaning_type, cleaning_type)
            notification_parts.append(f"• Тип прибирання: {cleaning_type_display}")
        
        if property_type:
            property_type_display = property_type_names.get(property_type, property_type)
            notification_parts.append(f"• Тип житла: {property_type_display}")
        
        if area_m2:
            notification_parts.append(f"• Площа: {area_m2} м²")
        
        if selected_date_str:
            selected_date = date_type.fromisoformat(selected_date_str)
            formatted_date = format_date_ukrainian(selected_date)
            notification_parts.append(f"• Дата: {formatted_date}")
        
        if selected_time:
            notification_parts.append(f"• Час: {selected_time}")
        
        notification_parts.append(f"• Адреса: {address}")
        
        notification_message = "\n".join(notification_parts)
        
        # Send message to owner
        await bot.send_message(
            chat_id=owner_id,
            text=notification_message
        )
        
        logger.info(f"Owner notification sent successfully to {owner_id}")
        
    except Exception as e:
        logger.error(
            f"Error sending owner notification: {e}. "
            f"Owner ID: {owner_id}",
            exc_info=True
        )
        # Don't fail the booking if notification fails

