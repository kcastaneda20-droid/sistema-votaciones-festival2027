from django.contrib import admin
from .models import Edicion, Categoria, Votacion, Opcion, Voto


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "activa")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activa")
    list_filter = ("edicion", "activa")


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "fecha_inicio", "fecha_fin", "activa")
    list_filter = ("categoria__edicion", "categoria", "activa")


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion")
    list_filter = ("votacion__categoria",)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    """Consulta administrativa de votos: solo lectura (no se crean ni editan a mano)."""

    campos = ("usuario", "edicion", "categoria", "opcion", "fecha")
    list_display = campos
    fields = campos
    readonly_fields = campos
    list_filter = ("edicion", "categoria")
    search_fields = ("usuario__username", "opcion__nombre")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False