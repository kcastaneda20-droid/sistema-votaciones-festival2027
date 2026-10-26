
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from django.views.decorators.http import require_POST
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

    return render(request, "votaciones/inicio.html", {
        "ediciones": ediciones,
        "votaciones": votaciones,
    })


# REGISTRAR UN VOTO
@require_POST
def votar(request, opcion_id):
    opcion = get_object_or_404(
        Opcion.objects.select_related(
            "votacion",
            "votacion__categoria",
            "votacion__categoria__edicion"
        ),
        pk=opcion_id
    )

    votacion = opcion.votacion
    ahora = timezone.now()

    if not votacion.activa:
        messages.error(request, "Esta votación no está activa.")
        return redirect("inicio")

    if not votacion.categoria.edicion.activa:
        messages.error(
            request,
            "Esta edición del festival no está activa."
        )
        return redirect("inicio")

    if ahora < votacion.fecha_inicio or ahora > votacion.fecha_fin:
        messages.error(
            request,
            "Esta votación está fuera de su periodo permitido."
        )
        return redirect("inicio")

    Voto.objects.create(opcion=opcion)

    messages.success(
        request,
        f"Tu voto por {opcion.nombre} fue registrado."
    )

    return redirect("inicio")


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
            return redirect("inicio")
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
            return redirect("inicio")
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
