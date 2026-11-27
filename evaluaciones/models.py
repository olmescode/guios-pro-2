from django.db import models

NIVELES = [(1, "Irrelevante"), (2, "Opcional"), (3, "Importante"), (4, "Fundamental")]
RESPUESTAS = [(1, "No cumple"), (2, "No sé"), (3, "Parcial"), (4, "Cumple")]
SECTORES = [("Público", "Público"), ("Privado", "Privado"), ("Mixto", "Mixto")]
TAMANOS = [("Micro", "Micro"), ("Pequeña", "Pequeña"), ("Mediana", "Mediana"), ("Grande", "Grande")]
ALCANCES = [("Interno", "Interno"), ("Externo", "Externo")]
LICENCIAS = [("Libre", "Libre"), ("Privativo", "Privativo")]
FODA = [("Fortaleza", "Fortaleza"), ("Oportunidad", "Oportunidad"), ("Debilidad", "Debilidad"), ("Amenaza", "Amenaza")]
RECOMENDACIONES = [("A", "Adoptar"), ("B", "Adoptar con matices"), ("C", "Posponer y analizar la adopción")]
FUENTES_IA = [("IA", "Generado por IA"), ("Plantilla", "Sugerencia automática")]


def clave_primaria(columna):
    return models.AutoField(primary_key=True, db_column=columna)


def clave_foranea(modelo, columna, **opciones):
    return models.ForeignKey(modelo, models.CASCADE, db_column=columna, **opciones)


class Organizacion(models.Model):
    id = clave_primaria("id_organizacion")
    nombre = models.CharField(max_length=150)
    sector = models.CharField(max_length=10, choices=SECTORES, blank=True)
    tamano = models.CharField(max_length=10, choices=TAMANOS, blank=True)

    class Meta:
        db_table = "organizacion"


class Usuario(models.Model):
    id = clave_primaria("id_usuario")
    organizacion = clave_foranea(Organizacion, "id_organizacion")
    nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=80, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuario"


class Dimension(models.Model):
    id = clave_primaria("id_dimension")
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "dimension"


class Factor(models.Model):
    id = clave_primaria("id_factor")
    dimension = clave_foranea(Dimension, "id_dimension", related_name="factores")
    nombre = models.CharField(max_length=80, unique=True)
    alcance_defecto = models.CharField(max_length=7, choices=ALCANCES)

    class Meta:
        db_table = "factor"
        ordering = ["id"]


class Subfactor(models.Model):
    id = clave_primaria("id_subfactor")
    factor = clave_foranea(Factor, "id_factor", related_name="subfactores")
    descripcion = models.CharField(max_length=255)
    n_citas = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "subfactor"
        ordering = ["id"]


class RespuestaExperto(models.Model):
    id = clave_primaria("id_respuesta")
    subfactor = clave_foranea(Subfactor, "id_subfactor", related_name="respuestas")
    experto = models.CharField(max_length=120)
    sector = models.CharField(max_length=10, choices=SECTORES)
    valor = models.PositiveSmallIntegerField(choices=NIVELES)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "respuesta_experto"


class ImportanciaSugerida(models.Model):
    id = clave_primaria("id_is")
    factor = clave_foranea(Factor, "id_factor", related_name="importancias")
    sector = models.CharField(max_length=10, choices=SECTORES, blank=True)
    valor_ie = models.DecimalField(max_digits=3, decimal_places=2)
    valor_il = models.PositiveSmallIntegerField(choices=NIVELES)
    valor_is = models.PositiveSmallIntegerField(choices=NIVELES)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        db_table = "importancia_sugerida"
        ordering = ["factor_id"]


class Software(models.Model):
    id = clave_primaria("id_software")
    nombre = models.CharField(max_length=120)
    version = models.CharField(max_length=30, blank=True)
    tipo_licencia = models.CharField(max_length=10, choices=LICENCIAS)

    class Meta:
        db_table = "software"

    def __str__(self):
        nombre_completo = f"{self.nombre} {self.version}"
        return nombre_completo.strip()


class Evaluacion(models.Model):
    id = clave_primaria("id_evaluacion")
    usuario = clave_foranea(Usuario, "id_usuario")
    software = clave_foranea(Software, "id_software")
    fecha = models.DateTimeField(auto_now_add=True)
    recomendacion = models.CharField(max_length=1, choices=RECOMENDACIONES, blank=True)
    explicacion_ia = models.TextField(blank=True)
    fuente_ia = models.CharField(max_length=9, choices=FUENTES_IA, blank=True)

    class Meta:
        db_table = "evaluacion"
        ordering = ["-fecha"]


class RespuestaPerfil(models.Model):
    id = clave_primaria("id_respuesta")
    evaluacion = clave_foranea(Evaluacion, "id_evaluacion", related_name="perfil")
    pregunta = models.CharField(max_length=255)
    respuesta = models.TextField()

    class Meta:
        db_table = "respuesta_perfil"
        ordering = ["id"]


class EvaluacionFactor(models.Model):
    id = clave_primaria("id_eval_factor")
    evaluacion = clave_foranea(Evaluacion, "id_evaluacion", related_name="factores")
    factor = models.ForeignKey(Factor, models.PROTECT, db_column="id_factor")
    importancia = models.ForeignKey(ImportanciaSugerida, models.PROTECT, db_column="id_is")
    imp_decisor = models.PositiveSmallIntegerField(choices=NIVELES)
    imp_relativa = models.PositiveSmallIntegerField(choices=NIVELES)
    alcance = models.CharField(max_length=7, choices=ALCANCES)
    ponderacion_media = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    foda = models.CharField(max_length=11, choices=FODA, blank=True)
    accion_ia = models.TextField(blank=True)

    class Meta:
        db_table = "evaluacion_factor"
        ordering = ["factor_id"]
        constraints = [models.UniqueConstraint(fields=["evaluacion", "factor"], name="uq_evaluacion_factor")]

    @property
    def relevante(self):
        return self.imp_relativa > 1


class EvaluacionSubfactor(models.Model):
    id = clave_primaria("id_eval_sub")
    eval_factor = clave_foranea(EvaluacionFactor, "id_eval_factor", related_name="subfactores")
    subfactor = models.ForeignKey(Subfactor, models.PROTECT, db_column="id_subfactor")
    valor = models.PositiveSmallIntegerField(choices=RESPUESTAS)

    class Meta:
        db_table = "evaluacion_subfactor"
        constraints = [models.UniqueConstraint(fields=["eval_factor", "subfactor"], name="uq_evaluacion_subfactor")]
