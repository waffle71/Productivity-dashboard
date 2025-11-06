from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    
    def ready(self):
        # Import your signals here to ensure they are connected when Django starts
        import dashboard.signals
