"""
Utility functions for Nexgensis Forms.

Includes response formatting, validation, and datetime helpers.
"""

from rest_framework.response import Response
from django.utils.timezone import localtime
import uuid
import re
import pytz
from datetime import datetime
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
from django.conf import settings


# ==================== API Response Formatting ====================

def api_response(data=None, message="", status_code=200, errors=None, pagination=None):
    """
    Standardized API response wrapper for consistent response format.

    Args:
        data: Response data (dict, list, or None)
        message: Human-readable message
        status_code: HTTP status code
        errors: Error details (dict or None)
        pagination: Pagination metadata (dict or None)

    Returns:
        DRF Response object

    Usage:
        return api_response(data={'id': 1}, message="Form created successfully")
        return api_response(message="Validation error", errors={'name': 'Required'}, status_code=400)
    """
    response_data = {
        "status": "success" if status_code < 400 else "failed",
        "message": message,
        "data": data,
        "timestamp": localtime().strftime('%Y-%m-%d %H:%M:%S')
    }

    if pagination:
        response_data["pagination"] = pagination

    if errors:
        response_data["errors"] = errors

    return Response(response_data, status=status_code)


# ==================== Validation Functions ====================

def validate_id(id_value):
    """
    Validate that a value is a valid UUID.

    Args:
        id_value: Value to validate

    Returns:
        bool: True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(str(id_value))
        return True
    except (ValueError, TypeError):
        return False


def validate_name(name):
    """
    Validate that a name contains only letters and spaces.

    Args:
        name: Name string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[A-Za-z\s]+$'
    return bool(re.match(pattern, name))


def validate_email(email):
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        bool: True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date(date_string):
    """
    Validate date string in YYYY-MM-DD format.

    Args:
        date_string: Date string to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    pattern = r"\d{4}-\d{2}-\d{2}"
    return bool(re.findall(pattern, date_string))


def validate_bool_value(value):
    """
    Validate boolean string values.

    Args:
        value: String value to validate

    Returns:
        bool: True if valid boolean string, False otherwise
    """
    return value in ('true', 'false', 'False', 'True')


# ==================== Datetime Utilities ====================

def format_user_timezone(date_time):
    """
    Format datetime to user's timezone from settings.

    Args:
        date_time: datetime object

    Returns:
        str: Formatted datetime string 'YYYY-MM-DD HH:MM:SS'
    """
    time_zone = getattr(settings, 'TIME_ZONE', None)
    if not time_zone:
        try:
            system_timezone = get_localzone()
            time_zone = f"{system_timezone}"
        except Exception as e:
            print(f"Error fetching system timezone, defaulting to Asia/Kolkata: {e}")
            time_zone = "Asia/Kolkata"

    dtime = date_time.astimezone(pytz.timezone(time_zone))
    return dtime.strftime('%Y-%m-%d %H:%M:%S')


def format_date(datetime_str=None, tz_kolkata=None):
    """
    Format date string or create current date in specified timezone.

    Args:
        datetime_str: ISO format datetime string or datetime object (optional)
        tz_kolkata: Timezone object (optional, defaults to system timezone)

    Returns:
        datetime: Timezone-aware datetime object
    """
    if not tz_kolkata:
        try:
            system_timezone = get_localzone()
            tz_kolkata = system_timezone
        except Exception as e:
            print(f"Error fetching system timezone, defaulting to Asia/Kolkata: {e}")
            tz_kolkata = ZoneInfo("Asia/Kolkata")

    if not datetime_str:
        datetime_str = datetime.now(tz=tz_kolkata)
    else:
        if isinstance(datetime_str, str):
            datetime_str = datetime.fromisoformat(datetime_str)
        if datetime_str.tzinfo is None:
            datetime_str = datetime_str.replace(tzinfo=tz_kolkata)

    return datetime_str


def format_duration(duration, lang='en'):
    """
    Format timedelta into human-readable string.

    Args:
        duration: timedelta object
        lang: Language code ('en' or 'ar' for Arabic)

    Returns:
        str: Formatted duration string (e.g., "2 years 3 months 5 days")
    """
    if duration:
        total_days = duration.days
        years = total_days // 365
        months = (total_days % 365) // 30
        days = (total_days % 365) % 30

        # Arabic equivalents for years, months, and days
        year_word = "سنة" if years == 1 else "سنوات"
        month_word = "شهر" if months == 1 else "شهور"
        day_word = "يوم" if days == 1 else "أيام"

        parts = []
        if years > 0:
            if lang == 'ar':
                parts.append(f"{years} {year_word}")
            else:
                parts.append(f"{years} year{'s' if years > 1 else ''}")
        if months > 0:
            if lang == 'ar':
                parts.append(f"{months} {month_word}")
            else:
                parts.append(f"{months} month{'s' if months > 1 else ''}")
        if days > 0:
            if lang == 'ar':
                parts.append(f"{days} {day_word}")
            else:
                parts.append(f"{days} day{'s' if days > 1 else ''}")

        return " ".join(parts) if parts else "0 days"
    else:
        return "0 days"
