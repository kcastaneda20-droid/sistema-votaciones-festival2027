from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from .models import Voto
from .tests import DatosPrueba

User = get_user_model()


class PruebasDeResultadosYPermisos(DatosPrueba, TestCase):
    """Resultados reales desde la base de datos y permisos diferenciados."""

    def setUp(self):
        super().setUp()
        self.administrador = User.objects.create_user("staff_prueba", is_staff=True)
        self.cliente_admin = Client()
        self.cliente_admin.force_login(self.administrador)

    def test_sin_sesion_se_redirige_al_login(self):
        respuesta = Client().get(reverse("resultados"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith(reverse("login")))

    def test_votante_no_puede_ver_resultados(self):
        Voto.objects.create(usuario=self.usuario, opcion=self.cancion_a)
        respuesta = self.cliente.get(reverse("resultados"))  # usuario sin is_staff
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any("administradores" in m for m in mensajes))

    def test_administrador_ve_el_conteo_por_opcion(self):
        Voto.objects.create(usuario=self.usuario, opcion=self.cancion_a)
        respuesta = self.cliente_admin.get(reverse("resultados"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Canción A")
        self.assertContains(respuesta, "100%")
        self.assertEqual(respuesta.context["total_votos"], 1)
        self.assertEqual(respuesta.context["total_votantes"], 1)

    def test_resultados_sin_votos_muestran_cero(self):
        respuesta = self.cliente_admin.get(reverse("resultados"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_votos"], 0)
        self.assertContains(respuesta, "0%")
