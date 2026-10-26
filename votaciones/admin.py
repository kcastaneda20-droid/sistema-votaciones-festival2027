from django.contrib import admin
from .models import Edicion, Categoria, Votacion, Opcion, Voto

admin.site.register(Edicion)
admin.site.register(Categoria)
admin.site.register(Votacion)
admin.site.register(Opcion)
admin.site.register(Voto)