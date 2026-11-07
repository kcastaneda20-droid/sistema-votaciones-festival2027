from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from votaciones.models import Edicion, Categoria, Votacion, Opcion

# Datos ficticios para pruebas (no son categorías definitivas del Festival)
DATOS = [
    {
        "categoria": "Música (prueba)",
        "activa": True,
        "votaciones": [
            {
                "nombre": "Canción favorita (prueba)",
                "opciones": ["Canción A", "Canción B", "Canción C"],
            },
            {
                "nombre": "Intérprete favorito (prueba)",
                "opciones": ["Intérprete 1", "Intérprete 2"],
            },
        ],
    },
    {
        "categoria": "Comparsas (prueba)",
        "activa": True,
        "votaciones": [
            {
                "nombre": "Comparsa favorita (prueba)",
                "opciones": ["Comparsa 1", "Comparsa 2", "Comparsa 3"],
            },
        ],
    },
    {
        "categoria": "Vestuario (prueba)",
        "activa": False,  # categoría cerrada, para probar el rechazo
        "votaciones": [
            {
                "nombre": "Mejor vestuario (prueba)",
                "opciones": ["Vestuario 1", "Vestuario 2"],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Carga datos ficticios de prueba: edición, categorías, votaciones y opciones."

    def handle(self, *args, **options):
        ahora = timezone.now()

        edicion, _ = Edicion.objects.get_or_create(
            nombre="Festival de la Leyenda Vallenata",
            anio=2027,
            defaults={"descripcion": "Edición de prueba.", "activa": True},
        )

        for item in DATOS:
            categoria, _ = Categoria.objects.update_or_create(
                edicion=edicion,
                nombre=item["categoria"],
                defaults={
                    "descripcion": "Categoría ficticia para pruebas.",
                    "activa": item["activa"],
                },
            )
            for datos_votacion in item["votaciones"]:
                votacion, _ = Votacion.objects.update_or_create(
                    categoria=categoria,
                    nombre=datos_votacion["nombre"],
                    defaults={
                        "descripcion": "Votación ficticia para pruebas.",
                        "fecha_inicio": ahora - timedelta(days=1),
                        "fecha_fin": ahora + timedelta(days=30),
                        "activa": True,
                    },
                )
                for nombre in datos_votacion["opciones"]:
                    Opcion.objects.get_or_create(
                        votacion=votacion,
                        nombre=nombre,
                        defaults={"descripcion": "Opción ficticia para pruebas."},
                    )

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados."))