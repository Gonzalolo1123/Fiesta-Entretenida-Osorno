from django.urls import path
from . import views

app_name = "FiestaEntreOso_app"

urlpatterns = [
    path("", views.index, name="index"),
    path("contacto/enviar/", views.enviar_contacto, name="enviar_contacto"),
]

