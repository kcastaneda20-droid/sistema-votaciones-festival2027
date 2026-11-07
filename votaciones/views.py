from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods

from .models import Edicion, Votacion, Opcion, Voto


# FORMULARIO DE REGISTRO EN ESPAÑOL
class FormularioRegistro(UserCreationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        help_text="Usa letras y números para crear tu usuario.",
        widget=forms.TextInput(attrs={
            "placeholder": "Escribe tu nombre de usuario"
        })
    )

    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Crea una contraseña"
        }),
        help_text=(
            "Evita contraseñas fáciles de adivinar. "
            "Django comprobará que cumpla sus requisitos."
        )
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Escribe nuevamente tu contraseña"
        }),
        help_text="Escribe la misma contraseña para confirmarla."
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "password1", "password2")


# FORMULARIO DE INICIO DE SESIÓN EN ESPAÑOL
class FormularioInicioSesion(AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            "placeholder": "Escribe tu nombre de usuario"
        })
    )

    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Escribe tu contraseña"
        })
    )


def destino_seguro(request):
    """Devuelve la página a la que volver tras iniciar sesión (parámetro next)."""
    siguiente = request.GET.get("next", "")
    if siguiente and url_has_allowed_host_and_scheme(
        siguiente,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return siguiente
    return "inicio"


# PÁGINA PRINCIPAL
def inicio(request):
    ediciones = Edicion.objects.filter(
        activa=True
    ).order_by("-anio")

    votaciones = Votacion.objects.filter(
        activa=True,
        categoria__edicion__activa=True
    ).select_related(
        "categoria",
        "categoria__edicion"
    ).prefetch_related("opciones")

    # Categorías en las que el usuario ya votó
    categorias_votadas = set()
    if request.user.is_authenticated:
        categorias_votadas = set(
            Voto.objects.filter(usuario=request.user)
            .values_list("categoria_id", flat=True)
        )

    return render(request, "votaciones/inicio.html", {
        "ediciones": ediciones,
        "votaciones": votaciones,
        "categorias_votadas": categorias_votadas,
    })


def motivo_bloqueo(opcion):
    """Devuelve por qué NO se puede votar esta opción, o None si se puede."""
    votacion = opcion.votacion
    categoria = votacion.categoria
    ahora = timezone.now()

    if not categoria.edicion.activa:
        return "Esta edición del festival no está activa."
    if not categoria.activa:
        return "Esta categoría está cerrada."
    if not votacion.activa:
        return "Esta votación no está activa."
    if ahora < votacion.fecha_inicio or ahora > votacion.fecha_fin:
        return "Esta votación está fuera de su periodo permitido."
    return None


# CONFIRMAR (GET) Y REGISTRAR (POST) UN VOTO
@login_required
@require_http_methods(["GET", "POST"])
def votar(request, categoria_id, opcion_id):
    opcion = get_object_or_404(
        Opcion.objects.select_related(
            "votacion",
            "votacion__categoria",
            "votacion__categoria__edicion"
        ),
        pk=opcion_id
    )
    votacion = opcion.votacion
    categoria = votacion.categoria
    edicion = categoria.edicion

    # La opción debe pertenecer a la categoría indicada
    if categoria.pk != categoria_id:
        messages.error(
            request,
            "La opción seleccionada no pertenece a esa categoría."
        )
        return redirect("inicio")

    # Categoría, edición y votación habilitadas
    motivo = motivo_bloqueo(opcion)
    if motivo:
        messages.error(request, motivo)
        return redirect("inicio")

    # Un solo voto por usuario, categoría y edición
    ya_voto = Voto.objects.filter(
        usuario=request.user,
        categoria=categoria,
        edicion=edicion
    ).exists()
    if ya_voto:
        messages.error(
            request,
            f"Ya votaste en la categoría {categoria.nombre}. "
            "Solo se permite un voto por categoría."
        )
        return redirect("inicio")

    if request.method == "POST":
        try:
            with transaction.atomic():
                Voto.objects.create(usuario=request.user, opcion=opcion)
        except IntegrityError:
            # Dos solicitudes simultáneas: la restricción de MySQL deja pasar solo una
            messages.error(
                request,
                f"Ya votaste en la categoría {categoria.nombre}. "
                "Solo se permite un voto por categoría."
            )
            return redirect("inicio")

        messages.success(
            request,
            f"Tu voto por {opcion.nombre} fue registrado."
        )
        return redirect("inicio")

    return render(request, "votaciones/confirmar_voto.html", {
        "opcion": opcion,
        "votacion": votacion,
        "categoria": categoria,
    })


# CREAR CUENTA
def registro(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        formulario = FormularioRegistro(request.POST)

        if formulario.is_valid():
            usuario = formulario.save()
            login(request, usuario)
            messages.success(
                request,
                "Tu cuenta fue creada correctamente."
            )
            return redirect(destino_seguro(request))
    else:
        formulario = FormularioRegistro()

    return render(request, "votaciones/registro.html", {
        "formulario": formulario,
    })


# INICIAR SESIÓN
def login_usuario(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        formulario = FormularioInicioSesion(
            request,
            data=request.POST
        )

        if formulario.is_valid():
            usuario = formulario.get_user()
            login(request, usuario)
            messages.success(
                request,
                "Has iniciado sesión correctamente."
            )
            return redirect(destino_seguro(request))
    else:
        formulario = FormularioInicioSesion(request)

    return render(request, "votaciones/login.html", {
        "formulario": formulario,
    })


# CERRAR SESIÓN
@require_POST
def logout_usuario(request):
    logout(request)
    messages.success(request, "Has cerrado sesión.")
    return redirect("inicio")



# HISTORIAL DE PARTICIPACIÓN DEL USUARIO
@login_required
def mis_votos(request):
    votos = (
        Voto.objects.filter(usuario=request.user)
        .select_related("edicion", "categoria", "opcion", "opcion__votacion")
        .order_by("-fecha")
    )
    return render(request, "votaciones/mis_votos.html", {"votos": votos})