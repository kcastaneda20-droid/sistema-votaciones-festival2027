# Sistema Web de Votaciones – Festival de la Leyenda Vallenata 2027

Proyecto de la asignatura Desarrollo Web (Fundación Universitaria del Área Andina).

## Descripción

Aplicación web para gestionar votaciones del Festival de la Leyenda Vallenata 2027 con la jerarquía configurable **Edición → Categoría → Votación → Opción → Voto**. La Entrega 3 agrega el módulo real de votaciones: voto por usuario autenticado, regla de un voto por usuario, categoría y edición, validaciones en el servidor, historial de participación, consulta administrativa y una API GET en JSON.

## Tecnologías y versiones

- Python 3.10 o superior (probado con Python 3.15 en Windows)
- Django 5.2.18
- MySQL 8.0 (cliente `mysqlclient` 2.3.0)
- python-dotenv 1.2.4
- HTML y CSS en plantillas Django
- Git y GitHub

Las dependencias exactas están en `requirements.txt`.

## Funcionalidades

- Registro, inicio y cierre de sesión (autenticación de Django).
- Administración de ediciones, categorías, votaciones y opciones con Django Admin.
- Votación: elegir una opción, confirmar y guardar el voto en MySQL.
- Un solo voto por usuario, categoría y edición (incluso con varias votaciones en la categoría).
- Validaciones: sesión iniciada, categoría y votación habilitadas, opción que pertenece a la categoría, protección CSRF y control de solicitudes simultáneas.
- "Mis votos": categorías en las que el usuario ya votó.
- Consulta administrativa de votos (solo lectura) en Django Admin.
- API `GET /api/categorias/` con categorías, votaciones y opciones en JSON.

## Instalación y ejecución

Requisitos: Python, Git y un servidor MySQL 8 en ejecución.

1. Clonar el repositorio y entrar a la carpeta:
   ```
   git clone https://github.com/kcastaneda20-droid/sistema-votaciones-festival2027.git
   cd sistema-votaciones-festival2027
   ```
2. Crear y activar el entorno virtual:
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Windows (PowerShell)
   source .venv/bin/activate       # Linux o Mac
   ```
   En PowerShell, si bloquea la activación: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
   En Linux, `mysqlclient` puede requerir las librerías de desarrollo de MySQL (por ejemplo `libmysqlclient-dev`).
4. Crear la base de datos en MySQL:
   ```sql
   CREATE DATABASE festival_vallenato CHARACTER SET utf8mb4;
   ```
5. Configurar las variables de entorno. Copiar `.env.example` como `.env` (`Copy-Item .env.example .env` en PowerShell) y completar los valores: usuario y contraseña de MySQL, y una clave secreta. Para generar la clave:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   El archivo `.env` no se sube al repositorio.
6. Crear las tablas (migraciones):
   ```
   python manage.py migrate
   ```
7. Crear un usuario administrador:
   ```
   python manage.py createsuperuser
   ```
8. Cargar los datos de prueba (ficticios):
   ```
   python manage.py cargar_datos_prueba
   ```
9. Iniciar el servidor:
   ```
   python manage.py runserver
   ```
10. Abrir en el navegador:
    - Sitio público: http://127.0.0.1:8000/
    - Administración: http://127.0.0.1:8000/admin/
    - API: http://127.0.0.1:8000/api/categorias/

Los usuarios votantes se crean desde la página, en "Crear cuenta".

## Datos de prueba

`python manage.py cargar_datos_prueba` crea una edición 2027 y tres categorías ficticias: Música (con dos votaciones), Comparsas y Vestuario (cerrada, para probar el rechazo). Se puede ejecutar varias veces sin duplicar datos. No son categorías definitivas del Festival.

## Pruebas automáticas

```
python manage.py test votaciones -v 2
```

Django crea una base temporal (`test_festival_vallenato`) y la elimina al terminar; el usuario de MySQL debe poder crear bases de datos. Las pruebas cubren los casos CP-01 a CP-10 de la Entrega 3 (incluida la concurrencia), además de la confirmación del voto, la protección CSRF y la restricción de unicidad en la base de datos.

## API

`GET /api/categorias/` devuelve en JSON las categorías de las ediciones activas, con su edición, sus votaciones y las opciones de cada una. Es de solo lectura y no incluye conteo de votos.

## Dónde está cada cosa

| Elemento | Archivo |
|---|---|
| Restricción de unicidad (usuario, categoría, edición) | `votaciones/models.py` (modelo `Voto`) y `votaciones/migrations/0003_voto_unicidad.py` |
| Registro del voto, validaciones y manejo de duplicados | `votaciones/views.py` (vista `votar`) |
| API GET | `votaciones/api.py` (ruta en `votaciones/urls.py`) |
| Consulta administrativa de votos | `votaciones/admin.py` |
| Pruebas automáticas | `votaciones/tests.py` |
| Datos de prueba | `votaciones/management/commands/cargar_datos_prueba.py` |

## Equipo de trabajo

- Paula Andrea Muñoz Hormiga
- Nicolás Mora Molina
- Iker Andrés Arias
- Karen Gineth Castañeda