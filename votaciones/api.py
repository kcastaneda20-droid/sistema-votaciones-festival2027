from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Categoria


@require_GET
def categorias(request):
    """GET /api/categorias/: categorías con sus votaciones y opciones, en JSON."""
    consulta = (
        Categoria.objects.filter(edicion__activa=True)
        .select_related("edicion")
        .prefetch_related("votaciones__opciones")
        .order_by("edicion__anio", "id")
    )

    datos = []
    for categoria in consulta:
        datos.append({
            "id": categoria.id,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "activa": categoria.activa,
            "edicion": {
                "id": categoria.edicion.id,
                "nombre": categoria.edicion.nombre,
                "anio": categoria.edicion.anio,
            },
            "votaciones": [
                {
                    "id": votacion.id,
                    "nombre": votacion.nombre,
                    "descripcion": votacion.descripcion,
                    "activa": votacion.activa,
                    "fecha_inicio": votacion.fecha_inicio.isoformat(),
                    "fecha_fin": votacion.fecha_fin.isoformat(),
                    "opciones": [
                        {
                            "id": opcion.id,
                            "nombre": opcion.nombre,
                            "descripcion": opcion.descripcion,
                            "imagen": opcion.imagen,
                        }
                        for opcion in votacion.opciones.all()
                    ],
                }
                for votacion in categoria.votaciones.all()
            ],
        })

    return JsonResponse(
        {"total": len(datos), "categorias": datos},
        content_type="application/json; charset=utf-8",
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )
