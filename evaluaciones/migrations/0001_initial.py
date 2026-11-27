
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dimension",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_dimension", primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=40, unique=True)),
            ],
            options={
                "db_table": "dimension",
            },
        ),
        migrations.CreateModel(
            name="Evaluacion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_evaluacion", primary_key=True, serialize=False
                    ),
                ),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "recomendacion",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("A", "Adoptar"),
                            ("B", "Adoptar con matices"),
                            ("C", "Posponer y analizar la adopción"),
                        ],
                        max_length=1,
                    ),
                ),
                ("explicacion_ia", models.TextField(blank=True)),
                (
                    "fuente_ia",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("IA", "Generado por IA"),
                            ("Plantilla", "Sugerencia automática"),
                        ],
                        max_length=9,
                    ),
                ),
            ],
            options={
                "db_table": "evaluacion",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="Organizacion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_organizacion", primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=150)),
                (
                    "sector",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Público", "Público"),
                            ("Privado", "Privado"),
                            ("Mixto", "Mixto"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "tamano",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Micro", "Micro"),
                            ("Pequeña", "Pequeña"),
                            ("Mediana", "Mediana"),
                            ("Grande", "Grande"),
                        ],
                        max_length=10,
                    ),
                ),
            ],
            options={
                "db_table": "organizacion",
            },
        ),
        migrations.CreateModel(
            name="Software",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_software", primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=120)),
                ("version", models.CharField(blank=True, max_length=30)),
                (
                    "tipo_licencia",
                    models.CharField(
                        choices=[("Libre", "Libre"), ("Privativo", "Privativo")],
                        max_length=10,
                    ),
                ),
            ],
            options={
                "db_table": "software",
            },
        ),
        migrations.CreateModel(
            name="Factor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_factor", primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=80, unique=True)),
                (
                    "alcance_defecto",
                    models.CharField(
                        choices=[("Interno", "Interno"), ("Externo", "Externo")],
                        max_length=7,
                    ),
                ),
                (
                    "dimension",
                    models.ForeignKey(
                        db_column="id_dimension",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="factores",
                        to="evaluaciones.dimension",
                    ),
                ),
            ],
            options={
                "db_table": "factor",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="ImportanciaSugerida",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_is", primary_key=True, serialize=False
                    ),
                ),
                (
                    "sector",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Público", "Público"),
                            ("Privado", "Privado"),
                            ("Mixto", "Mixto"),
                        ],
                        max_length=10,
                    ),
                ),
                ("valor_ie", models.DecimalField(decimal_places=2, max_digits=3)),
                (
                    "valor_il",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Irrelevante"),
                            (2, "Opcional"),
                            (3, "Importante"),
                            (4, "Fundamental"),
                        ]
                    ),
                ),
                (
                    "valor_is",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Irrelevante"),
                            (2, "Opcional"),
                            (3, "Importante"),
                            (4, "Fundamental"),
                        ]
                    ),
                ),
                ("fecha_calculo", models.DateTimeField(auto_now_add=True)),
                ("vigente", models.BooleanField(default=True)),
                (
                    "factor",
                    models.ForeignKey(
                        db_column="id_factor",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="importancias",
                        to="evaluaciones.factor",
                    ),
                ),
            ],
            options={
                "db_table": "importancia_sugerida",
                "ordering": ["factor_id"],
            },
        ),
        migrations.CreateModel(
            name="EvaluacionFactor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_eval_factor", primary_key=True, serialize=False
                    ),
                ),
                (
                    "imp_decisor",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Irrelevante"),
                            (2, "Opcional"),
                            (3, "Importante"),
                            (4, "Fundamental"),
                        ]
                    ),
                ),
                (
                    "imp_relativa",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Irrelevante"),
                            (2, "Opcional"),
                            (3, "Importante"),
                            (4, "Fundamental"),
                        ]
                    ),
                ),
                (
                    "alcance",
                    models.CharField(
                        choices=[("Interno", "Interno"), ("Externo", "Externo")],
                        max_length=7,
                    ),
                ),
                (
                    "ponderacion_media",
                    models.DecimalField(decimal_places=2, max_digits=3, null=True),
                ),
                (
                    "foda",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Fortaleza", "Fortaleza"),
                            ("Oportunidad", "Oportunidad"),
                            ("Debilidad", "Debilidad"),
                            ("Amenaza", "Amenaza"),
                        ],
                        max_length=11,
                    ),
                ),
                ("accion_ia", models.TextField(blank=True)),
                (
                    "evaluacion",
                    models.ForeignKey(
                        db_column="id_evaluacion",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="factores",
                        to="evaluaciones.evaluacion",
                    ),
                ),
                (
                    "factor",
                    models.ForeignKey(
                        db_column="id_factor",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="evaluaciones.factor",
                    ),
                ),
                (
                    "importancia",
                    models.ForeignKey(
                        db_column="id_is",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="evaluaciones.importanciasugerida",
                    ),
                ),
            ],
            options={
                "db_table": "evaluacion_factor",
                "ordering": ["factor_id"],
            },
        ),
        migrations.CreateModel(
            name="RespuestaPerfil",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_respuesta", primary_key=True, serialize=False
                    ),
                ),
                ("pregunta", models.CharField(max_length=255)),
                ("respuesta", models.TextField()),
                (
                    "evaluacion",
                    models.ForeignKey(
                        db_column="id_evaluacion",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfil",
                        to="evaluaciones.evaluacion",
                    ),
                ),
            ],
            options={
                "db_table": "respuesta_perfil",
                "ordering": ["id"],
            },
        ),
        migrations.AddField(
            model_name="evaluacion",
            name="software",
            field=models.ForeignKey(
                db_column="id_software",
                on_delete=django.db.models.deletion.CASCADE,
                to="evaluaciones.software",
            ),
        ),
        migrations.CreateModel(
            name="Subfactor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_subfactor", primary_key=True, serialize=False
                    ),
                ),
                ("descripcion", models.CharField(max_length=255)),
                ("n_citas", models.PositiveIntegerField(default=0)),
                (
                    "factor",
                    models.ForeignKey(
                        db_column="id_factor",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subfactores",
                        to="evaluaciones.factor",
                    ),
                ),
            ],
            options={
                "db_table": "subfactor",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="RespuestaExperto",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_respuesta", primary_key=True, serialize=False
                    ),
                ),
                ("experto", models.CharField(max_length=120)),
                (
                    "sector",
                    models.CharField(
                        choices=[
                            ("Público", "Público"),
                            ("Privado", "Privado"),
                            ("Mixto", "Mixto"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "valor",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Irrelevante"),
                            (2, "Opcional"),
                            (3, "Importante"),
                            (4, "Fundamental"),
                        ]
                    ),
                ),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "subfactor",
                    models.ForeignKey(
                        db_column="id_subfactor",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respuestas",
                        to="evaluaciones.subfactor",
                    ),
                ),
            ],
            options={
                "db_table": "respuesta_experto",
            },
        ),
        migrations.CreateModel(
            name="EvaluacionSubfactor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_eval_sub", primary_key=True, serialize=False
                    ),
                ),
                (
                    "valor",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "No cumple"),
                            (2, "No sé"),
                            (3, "Parcial"),
                            (4, "Cumple"),
                        ]
                    ),
                ),
                (
                    "eval_factor",
                    models.ForeignKey(
                        db_column="id_eval_factor",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subfactores",
                        to="evaluaciones.evaluacionfactor",
                    ),
                ),
                (
                    "subfactor",
                    models.ForeignKey(
                        db_column="id_subfactor",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="evaluaciones.subfactor",
                    ),
                ),
            ],
            options={
                "db_table": "evaluacion_subfactor",
            },
        ),
        migrations.CreateModel(
            name="Usuario",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="id_usuario", primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=120)),
                ("cargo", models.CharField(blank=True, max_length=80)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
                (
                    "organizacion",
                    models.ForeignKey(
                        db_column="id_organizacion",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="evaluaciones.organizacion",
                    ),
                ),
            ],
            options={
                "db_table": "usuario",
            },
        ),
        migrations.AddField(
            model_name="evaluacion",
            name="usuario",
            field=models.ForeignKey(
                db_column="id_usuario",
                on_delete=django.db.models.deletion.CASCADE,
                to="evaluaciones.usuario",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluacionfactor",
            constraint=models.UniqueConstraint(
                fields=("evaluacion", "factor"), name="uq_evaluacion_factor"
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluacionsubfactor",
            constraint=models.UniqueConstraint(
                fields=("eval_factor", "subfactor"), name="uq_evaluacion_subfactor"
            ),
        ),
    ]
