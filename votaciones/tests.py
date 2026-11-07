import threading
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import Edicion, Categoria, Votacion, Opcion, Voto

User = get_user_model()


class DatosPrueba:
    """Datos ficticios mínimos compartidos por todas las pruebas."""

    def setUp(self):
        super().setUp()
        ahora = timezone.now()

        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba", anio=2027, activa=True
        )
        self.musica = Categoria.objects.create(
            edicion=self.edicion, nombre="Música", activa=True
        )
        self.comparsas = Categoria.objects.create(
            edicion=self.edicion, nombre="Comparsas", activa=True
        )
        self.cerrada = Categoria.objects.create(
            edicion=self.edicion, nombre="Cerrada", activa=False
        )

        def crear_votacion(categoria, nombre):
            return Votacion.objects.create(
                categoria=categoria,
                nombre=nombre,
                fecha_inicio=ahora - timedelta(days=1),
                fecha_fin=ahora + timedelta(days=1),
                activa=True,
            )

        # Música tiene dos votaciones (subeventos) para probar el duplicado
        v_cancion = crear_votacion(self.musica, "Canción favorita")
        v_interprete = crear_votacion(self.musica, "Intérprete favorito")
        v_comparsa = crear_votacion(self.comparsas, "Comparsa favorita")
        v_cerrada = crear_votacion(self.cerrada, "Votación cerrada")

        self.cancion_a = Opcion.objects.create(votacion=v_cancion, nombre="Canción A")
        self.interprete_1 = Opcion.objects.create(votacion=v_interprete, nombre="Intérprete 1")
        self.comparsa_1 = Opcion.objects.create(votacion=v_comparsa, nombre="Comparsa 1")
        self.opcion_cerrada = Opcion.objects.create(votacion=v_cerrada, nombre="Opción cerrada")

        # Usuario ficticio sin contraseña: se autentica con force_login
        self.usuario = User.objects.create_user("usuario_prueba")
        self.cliente = Client()
        self.cliente.force_login(self.usuario)

    def votar(self, cliente, categoria, opcion):
        return cliente.post(reverse("votar", args=[categoria.id, opcion.id]))

    def ultimo_mensaje(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)][-1]


class PruebasDeVotacion(DatosPrueba, TestCase):

    def test_cp01_voto_valido(self):
        """CP-01: usuario autenticado selecciona una opción válida."""
        respuesta = self.votar(self.cliente, self.musica, self.cancion_a)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        voto = Voto.objects.get()
        self.assertEqual(voto.usuario, self.usuario)
        self.assertEqual(voto.opcion, self.cancion_a)
        self.assertEqual(voto.categoria, self.musica)
        self.assertEqual(voto.edicion, self.edicion)

    def test_cp02_segundo_voto_en_la_misma_categoria_rechazado(self):
        """CP-02: segundo voto en la misma categoría (otra opción y otro subevento)."""
        self.votar(self.cliente, self.musica, self.cancion_a)
        respuesta = self.votar(self.cliente, self.musica, self.interprete_1)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertIn("Ya votaste", self.ultimo_mensaje(respuesta))
        self.assertEqual(
            Voto.objects.filter(usuario=self.usuario, categoria=self.musica).count(), 1
        )

    def test_cp03_voto_en_otra_categoria_permitido(self):
        """CP-03: vota en una categoría diferente."""
        self.votar(self.cliente, self.musica, self.cancion_a)
        self.votar(self.cliente, self.comparsas, self.comparsa_1)
        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)

    def test_cp04_usuario_sin_sesion_debe_autenticarse(self):
        """CP-04: usuario no autenticado intenta votar."""
        respuesta = self.votar(Client(), self.musica, self.cancion_a)
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith(reverse("login")))
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp05_categoria_cerrada_rechazada(self):
        """CP-05: intenta votar en una categoría no habilitada."""
        respuesta = self.votar(self.cliente, self.cerrada, self.opcion_cerrada)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertIn("cerrada", self.ultimo_mensaje(respuesta))
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp06_opcion_de_otra_categoria_rechazada(self):
        """CP-06: envía una opción que pertenece a otra categoría."""
        respuesta = self.votar(self.cliente, self.comparsas, self.cancion_a)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertIn("no pertenece", self.ultimo_mensaje(respuesta))
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp07_usuario_consulta_sus_votos(self):
        """CP-07: consulta sus categorías votadas (sin ver votos de otros)."""
        self.votar(self.cliente, self.musica, self.cancion_a)
        otro = User.objects.create_user("otro_usuario")
        cliente_otro = Client()
        cliente_otro.force_login(otro)
        self.votar(cliente_otro, self.comparsas, self.comparsa_1)

        respuesta = self.cliente.get(reverse("mis_votos"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Canción A")
        self.assertNotContains(respuesta, "Comparsa 1")

    def test_confirmacion_no_registra_voto(self):
        """Confirmación: abrir la página de confirmación no guarda el voto."""
        respuesta = self.cliente.get(
            reverse("votar", args=[self.musica.id, self.cancion_a.id])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Confirmar voto")
        self.assertEqual(Voto.objects.count(), 0)

    def test_csrf_exige_token_en_el_post(self):
        """CSRF: un POST sin token CSRF es rechazado."""
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        respuesta = self.votar(cliente, self.musica, self.cancion_a)
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_restriccion_unica_en_la_base_de_datos(self):
        """Integridad: la base de datos rechaza un segundo voto del mismo usuario y categoría."""
        Voto.objects.create(usuario=self.usuario, opcion=self.cancion_a)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Voto.objects.create(usuario=self.usuario, opcion=self.interprete_1)


class PruebasDeAdministracion(DatosPrueba, TestCase):

    def test_cp08_administrador_consulta_los_votos(self):
        """CP-08: el administrador consulta los votos y coinciden con la base de datos."""
        Voto.objects.create(usuario=self.usuario, opcion=self.cancion_a)
        administrador = User.objects.create_superuser("admin_prueba")
        self.client.force_login(administrador)

        respuesta = self.client.get(reverse("admin:votaciones_voto_changelist"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "usuario_prueba")
        self.assertContains(respuesta, "Música")
        self.assertContains(respuesta, "Canción A")
        self.assertEqual(Voto.objects.count(), 1)

        # Los votos no se crean a mano desde el admin
        respuesta_alta = self.client.get(reverse("admin:votaciones_voto_add"))
        self.assertEqual(respuesta_alta.status_code, 403)


class PruebasDeApi(DatosPrueba, TestCase):

    def test_cp10_api_categorias_devuelve_json_valido(self):
        """CP-10: GET /api/categorias/ devuelve JSON con categorías y opciones reales."""
        respuesta = self.client.get(reverse("api_categorias"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("application/json", respuesta["Content-Type"])

        datos = respuesta.json()
        self.assertEqual(datos["total"], 3)
        categorias = datos["categorias"]
        self.assertEqual(
            [c["nombre"] for c in categorias], ["Música", "Comparsas", "Cerrada"]
        )
        opciones_musica = [
            opcion["nombre"]
            for votacion in categorias[0]["votaciones"]
            for opcion in votacion["opciones"]
        ]
        self.assertCountEqual(opciones_musica, ["Canción A", "Intérprete 1"])

    def test_api_solo_permite_get(self):
        """La API es de solo lectura: un POST no está permitido."""
        respuesta = self.client.post(reverse("api_categorias"))
        self.assertEqual(respuesta.status_code, 405)


class PruebaDeConcurrencia(DatosPrueba, TransactionTestCase):

    def test_cp09_solicitudes_simultaneas_dejan_un_solo_voto(self):
        """CP-09: varias solicitudes simultáneas a la misma categoría dejan un solo voto."""
        opciones = [self.cancion_a, self.interprete_1] * 3  # 6 solicitudes a la vez
        salida = threading.Barrier(len(opciones))
        codigos = []

        def intentar_votar(opcion):
            cliente = Client()
            cliente.force_login(self.usuario)
            try:
                salida.wait(timeout=15)  # todas arrancan al mismo tiempo
                respuesta = cliente.post(
                    reverse("votar", args=[self.musica.id, opcion.id])
                )
                codigos.append(respuesta.status_code)
            finally:
                connection.close()

        hilos = [threading.Thread(target=intentar_votar, args=(o,)) for o in opciones]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        # Todas las solicitudes terminaron sin error del servidor...
        self.assertEqual(len(codigos), len(opciones))
        self.assertTrue(all(codigo == 302 for codigo in codigos))
        # ...y solo quedó un voto válido
        self.assertEqual(
            Voto.objects.filter(usuario=self.usuario, categoria=self.musica).count(), 1
        )