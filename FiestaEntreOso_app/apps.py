from django.apps import AppConfig


class FiestaEntreOsoAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "FiestaEntreOso_app"
    verbose_name = "Sitio público Fiesta Entre Oso"

    def ready(self):
        # Registra señales (auto-creación de productos desde imágenes de referencia)
        from . import signals  # noqa: F401

