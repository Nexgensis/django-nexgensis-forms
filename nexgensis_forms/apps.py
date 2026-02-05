"""Django app configuration for Nexgensis Forms."""

from django.apps import AppConfig


class NexgensisFormsConfig(AppConfig):
    """Configuration for the Nexgensis Forms application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nexgensis_forms'
    verbose_name = 'Nexgensis Dynamic Forms'

    def ready(self):
        """
        Import signals and perform app initialization.
        Called when Django starts.
        """
        # Import signals if needed
        # from . import signals
        pass
