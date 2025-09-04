from django.apps import AppConfig


class PriorityAnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'priority_analyzer'
    
    def ready(self):
        """Import signals when the app is ready"""
        import priority_analyzer.signals
