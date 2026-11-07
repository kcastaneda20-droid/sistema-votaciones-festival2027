from django.conf import settings
from django.db import models


class Edicion(models.Model):
    nombre = models.CharField(max_length=150)
    anio = models.PositiveIntegerField()
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.anio}"


class Categoria(models.Model):
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.CASCADE,
        related_name="categorias"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    # Una categoría cerrada no recibe votos
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Votacion(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="votaciones"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name="opciones"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    imagen = models.URLField(blank=True)

    def __str__(self):
        return self.nombre


class Voto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votos"
    )
    # La edición y la categoría se calculan a partir de la opción (ver save)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.CASCADE,
        related_name="votos",
        editable=False
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="votos",
        editable=False
    )
    opcion = models.ForeignKey(
        Opcion,
        on_delete=models.CASCADE,
        related_name="votos"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Un voto por usuario, categoría y edición (regla central)
            models.UniqueConstraint(
                fields=["usuario", "categoria", "edicion"],
                name="voto_unico_usuario_categoria_edicion",
            )
        ]

    def save(self, *args, **kwargs):
        self.categoria = self.opcion.votacion.categoria
        self.edicion = self.categoria.edicion
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario} votó por {self.opcion.nombre}"