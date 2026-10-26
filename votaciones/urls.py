from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("votar/<int:opcion_id>/", views.votar, name="votar"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_usuario, name="login"),
    path("logout/", views.logout_usuario, name="logout"),
]
