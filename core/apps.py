from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'  # Optional: Adds a human-readable name

    def ready(self):
        import core.signals  # Ensure signals are loaded
