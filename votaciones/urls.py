from django.urls import path
from . import api, views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("votar/<int:categoria_id>/<int:opcion_id>/", views.votar, name="votar"),
    path("mis-votos/", views.mis_votos, name="mis_votos"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_usuario, name="login"),
    path("logout/", views.logout_usuario, name="logout"),
    path("api/categorias/", api.categorias, name="api_categorias"),
]