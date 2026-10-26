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
    opcion = models.ForeignKey(
        Opcion,
        on_delete=models.CASCADE,
        related_name="votos"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voto por {self.opcion.nombre}"
