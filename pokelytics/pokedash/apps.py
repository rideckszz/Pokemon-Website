from django.apps import AppConfig

class PokedashConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pokedash'

    def ready(self):
        # Import signals only when the app is ready
        import pokedash.signals
