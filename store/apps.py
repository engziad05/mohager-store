from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    # الدالة دي بتشتغل أول ما الـ app يحمل
    def ready(self):
        import store.signals  # هنا بنفعل الإشارات