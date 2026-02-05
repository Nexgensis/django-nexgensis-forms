"""
Configuration module for Nexgensis Forms.

Handles Django settings with sensible defaults.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Default configuration values
DEFAULTS = {
    'LOCATION_MODEL': None,  # Optional: 'appname.ModelName' for location FK
    'WORKFLOW_INTEGRATION': False,  # Enable if nexgensis_workflow is installed
    'ENABLE_BULK_UPLOAD': True,  # Enable Excel bulk import/export
    'RESPONSE_WRAPPER': 'api_response',  # Function name for API responses
    'USER_MODEL': 'auth.User',  # User model for created_by fields
    'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB max Excel file size
    'ALLOWED_FILE_TYPES': ['xlsx', 'xls'],  # Allowed bulk upload file types
}


def get_setting(name):
    """
    Get a setting from Django settings or use default.

    Args:
        name: Setting name

    Returns:
        Setting value
    """
    user_settings = getattr(settings, 'NEXGENSIS_FORMS', {})
    return user_settings.get(name, DEFAULTS[name])


def get_location_model():
    """
    Get the configured location model (optional).

    Returns:
        Model class or None
    """
    from django.apps import apps

    model_string = get_setting('LOCATION_MODEL')
    if model_string:
        try:
            return apps.get_model(model_string)
        except (LookupError, ValueError):
            raise ImproperlyConfigured(
                f"NEXGENSIS_FORMS['LOCATION_MODEL'] refers to model "
                f"'{model_string}' that has not been installed"
            )
    return None


def get_user_model():
    """
    Get the configured user model.

    Returns:
        Model class
    """
    from django.apps import apps

    model_string = get_setting('USER_MODEL')
    try:
        return apps.get_model(model_string)
    except (LookupError, ValueError):
        raise ImproperlyConfigured(
            f"NEXGENSIS_FORMS['USER_MODEL'] refers to model "
            f"'{model_string}' that has not been installed"
        )


def is_workflow_enabled():
    """
    Check if workflow integration is enabled.

    Returns:
        bool
    """
    return get_setting('WORKFLOW_INTEGRATION')


def is_bulk_upload_enabled():
    """
    Check if bulk upload feature is enabled.

    Returns:
        bool
    """
    return get_setting('ENABLE_BULK_UPLOAD')
