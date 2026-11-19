from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .models import Edicion, Opcion, Voto


@login_required
@require_GET
def consultar(request):
    """Resultados por edición, categoría y opción, leídos de MySQL.

    Permisos diferenciados: sin sesión se redirige al login; un votante
    (usuario sin is_staff) es devuelto al inicio con un mensaje; solo el
    personal administrador ve los resultados.
    """
    if not request.user.is_staff:
        messages.error(
            request,
            "Solo los administradores pueden consultar los resultados."
        )
        return redirect("inicio")

    ediciones = list(Edicion.objects.order_by("-anio", "-id"))

    # Edición seleccionada: la pedida en la URL, si no la activa más reciente
    seleccionada = None
    pedida = request.GET.get("edicion", "")
    if pedida.isdigit():
        seleccionada = next((e for e in ediciones if e.pk == int(pedida)), None)
    if seleccionada is None:
        seleccionada = next((e for e in ediciones if e.activa), None)
    if seleccionada is None and ediciones:
        seleccionada = ediciones[0]

    categorias = []
    total_votos = 0
    total_votantes = 0

    if seleccionada:
        opciones = Opcion.objects.annotate(total=Count("votos")).order_by("-total", "nombre")
        consulta = seleccionada.categorias.prefetch_related(
            Prefetch("votaciones__opciones", queryset=opciones)
        ).order_by("id")

        for categoria in consulta:
            bloques = []
            total = 0
            for votacion in categoria.votaciones.all():
                lista = list(votacion.opciones.all())
                total += sum(opcion.total for opcion in lista)
                bloques.append({"votacion": votacion, "opciones": lista})

            # Porcentaje sobre los votos de la categoría (un voto por categoría)
            for bloque in bloques:
                for opcion in bloque["opciones"]:
                    opcion.porcentaje = round(opcion.total * 100 / total) if total else 0

            categorias.append({
                "categoria": categoria,
                "total": total,
                "votaciones": bloques,
            })

        votos = Voto.objects.filter(edicion=seleccionada)
        total_votos = votos.count()
        total_votantes = votos.values("usuario").distinct().count()

    return render(request, "votaciones/resultados.html", {
        "ediciones": ediciones,
        "seleccionada": seleccionada,
        "categorias": categorias,
        "total_votos": total_votos,
        "total_votantes": total_votantes,
    })
