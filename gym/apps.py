from django.apps import AppConfig


class GymConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gym'
    
    def ready(self):
        import gym.models  # Importa para activar signals