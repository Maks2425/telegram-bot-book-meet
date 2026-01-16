"""Google Calendar service for checking available time slots."""

import json
import os
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    CALENDAR_CLEANING_DURATION_HOURS,
    CALENDAR_SLOT_INTERVAL_HOURS,
    CALENDAR_TIMEZONE,
    CALENDAR_WORK_END,
    CALENDAR_WORK_START,
)

# Load environment variables
load_dotenv()

# Google Calendar API scope
# Changed to full access to allow creating events
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service() -> Optional[object]:
    """Get Google Calendar service instance.
    
    Supports both OAuth2 and Service Account authentication.
    
    Returns:
        Google Calendar service object or None if authentication fails.
    """
    creds = None
    
    # Try Service Account first (recommended for bots)
    # Option 1: From environment variable as JSON string (for deployment)
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            # Parse JSON string from environment variable
            service_account_info = json.loads(service_account_json)
            creds = ServiceAccountCredentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
        except Exception as e:
            print(f"Error loading service account from JSON: {e}")
    
    # Option 2: From file path (for local development)
    if not creds:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if service_account_file and os.path.exists(service_account_file):
            try:
                creds = ServiceAccountCredentials.from_service_account_file(
                    service_account_file, scopes=SCOPES
                )
            except Exception as e:
                print(f"Error loading service account file: {e}")
    
    # Try OAuth2 credentials
    if not creds:
        token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
        credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If there are no (valid) credentials available, try to get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds and os.path.exists(credentials_file):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error running OAuth flow: {e}")
    
    if not creds:
        print("Warning: No Google Calendar credentials found. Using mock data.")
        return None
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building calendar service: {e}")
        return None


def get_busy_time_slots(
    calendar_service: object,
    calendar_id: str,
    date_obj: date,
    timezone: Optional[str] = None
) -> List[Tuple[time, time]]:
    """Get busy time slots for a specific date.
    
    Args:
        calendar_service: Google Calendar service object.
        calendar_id: Calendar ID (use 'primary' for primary calendar).
        date_obj: Date to check.
        timezone: Timezone string (default: from config).
        
    Returns:
        List of tuples (start_time, end_time) for busy slots.
    """
    if timezone is None:
        timezone = CALENDAR_TIMEZONE
    
    if not calendar_service:
        return []
    
    try:
        # Calculate time range for the day (00:00 to 23:59)
        start_datetime = datetime.combine(date_obj, time.min)
        end_datetime = datetime.combine(date_obj, time.max)
        
        # Format for API
        time_min = start_datetime.isoformat() + 'Z'
        time_max = end_datetime.isoformat() + 'Z'
        
        # Query freebusy
        freebusy_request = {
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": timezone,
            "items": [{"id": calendar_id}]
        }
        
        freebusy = calendar_service.freebusy().query(body=freebusy_request).execute()
        
        busy_slots = []
        if 'calendars' in freebusy and calendar_id in freebusy['calendars']:
            busy_periods = freebusy['calendars'][calendar_id].get('busy', [])
            
            for period in busy_periods:
                start_str = period['start']
                end_str = period['end']
                
                # Parse ISO format
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                # Convert to local time (assuming UTC)
                if start_dt.tzinfo:
                    start_dt = start_dt.astimezone()
                    end_dt = end_dt.astimezone()
                
                # Extract time only
                start_time = start_dt.time()
                end_time = end_dt.time()
                
                busy_slots.append((start_time, end_time))
        
        return busy_slots
    
    except HttpError as e:
        print(f"Error querying calendar: {e}")
        return []
    except Exception as e:
        print(f"Error getting busy slots: {e}")
        return []


def generate_available_time_slots(
    date_obj: date,
    calendar_service: Optional[object] = None,
    calendar_id: str = "primary",
    work_start: Optional[time] = None,
    work_end: Optional[time] = None,
    slot_interval_hours: Optional[int] = None
) -> List[time]:
    """Generate available time slots for a date.
    
    Args:
        date_obj: Date to generate slots for.
        calendar_service: Google Calendar service (optional).
        calendar_id: Calendar ID to check (default: 'primary').
        work_start: Start of working hours (default: from config).
        work_end: End of working hours (default: from config).
        slot_interval_hours: Interval between slots in hours (default: from config).
        
    Returns:
        List of available time slots.
    """
    # Use config defaults if not provided
    if work_start is None:
        work_start = CALENDAR_WORK_START
    if work_end is None:
        work_end = CALENDAR_WORK_END
    if slot_interval_hours is None:
        slot_interval_hours = CALENDAR_SLOT_INTERVAL_HOURS
    
    # Skip weekends
    if date_obj.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return []
    
    # Generate all possible slots within working hours
    all_slots = []
    current_time = work_start
    
    while current_time < work_end:
        all_slots.append(current_time)
        # Add interval hours
        hour = current_time.hour + slot_interval_hours
        if hour >= 24:
            break
        current_time = time(hour, current_time.minute)
    
    # If no calendar service, return all slots
    if not calendar_service:
        return all_slots
    
    # Get busy slots from calendar
    busy_slots = get_busy_time_slots(calendar_service, calendar_id, date_obj)
    
    # Filter out busy slots
    available_slots = []
    for slot in all_slots:
        is_available = True
        
        # Check if slot overlaps with any busy period
        for busy_start, busy_end in busy_slots:
            # Slot is considered busy if it overlaps with busy period
            # We check if slot time is within busy period or if busy period overlaps slot
            if (busy_start <= slot < busy_end) or \
               (slot <= busy_start < time(slot.hour + slot_interval_hours, slot.minute)):
                is_available = False
                break
        
        if is_available:
            available_slots.append(slot)
    
    return available_slots


def create_calendar_event(
    calendar_service: object,
    calendar_id: str,
    title: str,
    description: str,
    start_datetime: datetime,
    end_datetime: datetime,
    location: str = "",
    timezone: Optional[str] = None
) -> Optional[str]:
    """Create an event in Google Calendar.
    
    Args:
        calendar_service: Google Calendar service object.
        calendar_id: Calendar ID (use 'primary' for primary calendar).
        title: Event title.
        description: Event description.
        start_datetime: Event start datetime.
        end_datetime: Event end datetime.
        location: Event location (address).
        timezone: Timezone string (default: from config).
        
    Returns:
        Event ID if successful, None otherwise.
    """
    if timezone is None:
        timezone = CALENDAR_TIMEZONE
    
    if not calendar_service:
        print("Warning: Calendar service not available. Cannot create event.")
        return None
    
    try:
        # Format datetime for API (RFC3339 format)
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()
        
        # Create event body
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
            'location': location,
        }
        
        # Insert event
        created_event = calendar_service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        event_id = created_event.get('id')
        print(f"Event created successfully. Event ID: {event_id}")
        return event_id
    
    except HttpError as e:
        print(f"Error creating calendar event: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error creating event: {e}")
        return None

