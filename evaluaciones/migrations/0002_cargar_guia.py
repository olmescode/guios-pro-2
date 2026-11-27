import json
from pathlib import Path

from django.db import migrations

from evaluaciones.guia import recalcular

ARCHIVO_GUIA = Path(__file__).parent.parent / "data" / "guia.json"


def cargar_guia(apps, schema_editor):
    Dimension = apps.get_model("evaluaciones", "Dimension")
    Factor = apps.get_model("evaluaciones", "Factor")
    Subfactor = apps.get_model("evaluaciones", "Subfactor")
    contenido = ARCHIVO_GUIA.read_text(encoding="utf-8")
    for factor_guia in json.loads(contenido):
        dimension, creada = Dimension.objects.get_or_create(nombre=factor_guia["dimension"])
        factor = Factor.objects.create(dimension=dimension, nombre=factor_guia["nombre"], alcance_defecto=factor_guia["alcance"])
        for subfactor_guia in factor_guia["subfactores"]:
            Subfactor.objects.create(factor=factor, **subfactor_guia)
    recalcular()


class Migration(migrations.Migration):
    dependencies = [("evaluaciones", "0001_initial")]
    operations = [migrations.RunPython(cargar_guia, migrations.RunPython.noop)]
