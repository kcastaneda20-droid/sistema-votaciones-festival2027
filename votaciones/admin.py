from datetime import timedelta

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count

from .models import Edicion, Categoria, Votacion, Opcion, Voto

admin.site.site_header = "Festival de la Leyenda Vallenata 2027 · Administración"
admin.site.site_title = "Administración de votaciones"
admin.site.index_title = "Gestión de ediciones, categorías, votaciones y participantes"


# ---------------------------------------------------------------------------
# Formularios en línea: toda la jerarquía se configura desde una sola pantalla
# (Edición → Categorías, Categoría → Votaciones, Votación → Opciones)
# ---------------------------------------------------------------------------

class CategoriaInline(admin.TabularInline):
    model = Categoria
    extra = 1
    fields = ("nombre", "descripcion", "activa")
    show_change_link = True


class VotacionInline(admin.TabularInline):
    model = Votacion
    extra = 1
    fields = ("nombre", "fecha_inicio", "fecha_fin", "activa")
    show_change_link = True


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2
    fields = ("nombre", "descripcion", "imagen")


# ---------------------------------------------------------------------------
# Acciones masivas
# ---------------------------------------------------------------------------

@admin.action(description="Marcar como activos")
def activar(modeladmin, request, queryset):
    cantidad = queryset.update(activa=True)
    modeladmin.message_user(request, f"{cantidad} registro(s) activado(s).", messages.SUCCESS)


@admin.action(description="Marcar como inactivos (cerrar)")
def desactivar(modeladmin, request, queryset):
    cantidad = queryset.update(activa=False)
    modeladmin.message_user(request, f"{cantidad} registro(s) cerrado(s).", messages.SUCCESS)


def _mover(fecha, dias=365):
    """Desplaza una fecha un año hacia adelante (admite None)."""
    return fecha + timedelta(days=dias) if fecha else None


@admin.action(description="Duplicar edición (sin votos) para el año siguiente")
def duplicar_edicion(modeladmin, request, queryset):
    """Copia la edición con sus categorías, votaciones y opciones, sin los votos.

    La copia queda inactiva: el administrador revisa fechas y participantes
    y luego la activa. Así se configura una edición nueva sin tocar el código.
    """
    with transaction.atomic():
        for edicion in queryset:
            nueva = Edicion.objects.create(
                nombre=edicion.nombre,
                anio=edicion.anio + 1,
                descripcion=edicion.descripcion,
                fecha_inicio=_mover(edicion.fecha_inicio),
                fecha_fin=_mover(edicion.fecha_fin),
                activa=False,
            )
            for categoria in edicion.categorias.all():
                nueva_categoria = Categoria.objects.create(
                    edicion=nueva,
                    nombre=categoria.nombre,
                    descripcion=categoria.descripcion,
                    activa=categoria.activa,
                )
                for votacion in categoria.votaciones.all():
                    nueva_votacion = Votacion.objects.create(
                        categoria=nueva_categoria,
                        nombre=votacion.nombre,
                        descripcion=votacion.descripcion,
                        fecha_inicio=_mover(votacion.fecha_inicio),
                        fecha_fin=_mover(votacion.fecha_fin),
                        activa=False,
                    )
                    Opcion.objects.bulk_create([
                        Opcion(
                            votacion=nueva_votacion,
                            nombre=opcion.nombre,
                            descripcion=opcion.descripcion,
                            imagen=opcion.imagen,
                        )
                        for opcion in votacion.opciones.all()
                    ])

    modeladmin.message_user(
        request,
        f"Se duplicaron {queryset.count()} edición(es). Las copias quedaron inactivas: "
        "revisa fechas y participantes y actívalas cuando estén listas.",
        messages.SUCCESS,
    )


# ---------------------------------------------------------------------------
# Administración de cada modelo
# ---------------------------------------------------------------------------

@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "activa", "total_categorias", "total_votos")
    list_editable = ("activa",)
    list_filter = ("activa",)
    search_fields = ("nombre",)
    inlines = [CategoriaInline]
    actions = [activar, desactivar, duplicar_edicion]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _categorias=Count("categorias", distinct=True),
            _votos=Count("votos", distinct=True),
        )

    @admin.display(description="Categorías", ordering="_categorias")
    def total_categorias(self, obj):
        return obj._categorias

    @admin.display(description="Votos", ordering="_votos")
    def total_votos(self, obj):
        return obj._votos


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activa", "total_votaciones", "total_votos")
    list_editable = ("activa",)
    list_filter = ("edicion", "activa")
    search_fields = ("nombre",)
    list_select_related = ("edicion",)
    inlines = [VotacionInline]
    actions = [activar, desactivar]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _votaciones=Count("votaciones", distinct=True),
            _votos=Count("votos", distinct=True),
        )

    @admin.display(description="Votaciones", ordering="_votaciones")
    def total_votaciones(self, obj):
        return obj._votaciones

    @admin.display(description="Votos", ordering="_votos")
    def total_votos(self, obj):
        return obj._votos


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "categoria", "fecha_inicio", "fecha_fin",
        "activa", "total_opciones", "total_votos",
    )
    list_editable = ("activa",)
    list_filter = ("categoria__edicion", "categoria", "activa")
    search_fields = ("nombre",)
    list_select_related = ("categoria",)
    inlines = [OpcionInline]
    actions = [activar, desactivar]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _opciones=Count("opciones", distinct=True),
            _votos=Count("opciones__votos", distinct=True),
        )

    @admin.display(description="Opciones", ordering="_opciones")
    def total_opciones(self, obj):
        return obj._opciones

    @admin.display(description="Votos", ordering="_votos")
    def total_votos(self, obj):
        return obj._votos


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "categoria", "total_votos")
    list_filter = ("votacion__categoria__edicion", "votacion__categoria")
    search_fields = ("nombre",)
    list_select_related = ("votacion__categoria",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_votos=Count("votos"))

    @admin.display(description="Categoría")
    def categoria(self, obj):
        return obj.votacion.categoria

    @admin.display(description="Votos", ordering="_votos")
    def total_votos(self, obj):
        return obj._votos


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    """Consulta administrativa de votos: solo lectura (no se crean ni editan a mano)."""

    campos = ("usuario", "edicion", "categoria", "opcion", "fecha")
    list_display = campos
    fields = campos
    readonly_fields = campos
    list_filter = ("edicion", "categoria")
    search_fields = ("usuario__username", "opcion__nombre")
    list_select_related = ("usuario", "edicion", "categoria", "opcion")
    

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
