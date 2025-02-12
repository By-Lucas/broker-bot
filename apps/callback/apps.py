from django.apps import AppConfig


class CallbackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "callback"

    def ready(self):
        import callback.signals