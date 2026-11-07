import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def borrar_votos_anonimos(apps, schema_editor):
    # Los votos de la Entrega 2 no tenían usuario: eran solo datos de prueba.
    apps.get_model("votaciones", "Voto").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("votaciones", "0002_voto"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria",
            name="activa",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(borrar_votos_anonimos, migrations.RunPython.noop),
        migrations.AddField(
            model_name="voto",
            name="usuario",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votos",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="voto",
            name="edicion",
            field=models.ForeignKey(
                default=1,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votos",
                to="votaciones.edicion",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="voto",
            name="categoria",
            field=models.ForeignKey(
                default=1,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votos",
                to="votaciones.categoria",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="voto",
            constraint=models.UniqueConstraint(
                fields=("usuario", "categoria", "edicion"),
                name="voto_unico_usuario_categoria_edicion",
            ),
        ),
    ]