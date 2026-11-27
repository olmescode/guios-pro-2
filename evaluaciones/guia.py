from decimal import Decimal
from statistics import quantiles

from django.db import transaction
from django.db.models import Count, Sum

from .models import EvaluacionFactor, Factor, ImportanciaSugerida, RespuestaExperto

EXPERTOS_TESIS = 57
IE_TESIS = 3
PM_FAVORABLE = 3
NIVELES_CRITICOS = (3, 4)
FODA_NEGATIVO = ("Debilidad", "Amenaza")
CLASIFICACION_FODA = {
    ("Interno", True): "Fortaleza",
    ("Interno", False): "Debilidad",
    ("Externo", True): "Oportunidad",
    ("Externo", False): "Amenaza",
}


def cruzar(primera_importancia, segunda_importancia):
    return (primera_importancia + segunda_importancia) // 2


def redondear(numero):
    return int(numero + Decimal("0.5"))


def importancia_literatura(citas_por_factor):
    cuartiles = quantiles(citas_por_factor.values(), n=4, method="inclusive")
    niveles = {}
    for factor_id, citas in citas_por_factor.items():
        niveles[factor_id] = 1
        for cuartil in cuartiles:
            niveles[factor_id] += citas > cuartil
    return niveles


def ponderacion_media(calificaciones):
    return Decimal(sum(calificaciones)) / len(calificaciones)


def clasificar(alcance, ponderacion):
    return CLASIFICACION_FODA[(alcance, ponderacion >= PM_FAVORABLE)]


def recomendar(resultados_por_factor):
    recomendacion = "A"
    for importancia_relativa, foda in resultados_por_factor:
        if foda in FODA_NEGATIVO and importancia_relativa in NIVELES_CRITICOS:
            return "C"
        if foda in FODA_NEGATIVO:
            recomendacion = "B"
    return recomendacion


def importancia_vigente(factor, sector=""):
    vigentes = factor.importancias.filter(vigente=True)
    del_sector = vigentes.filter(sector=sector)
    return del_sector.first() or vigentes.get(sector="")


def importancia_experto(factor, sector):
    respuestas = RespuestaExperto.objects.filter(subfactor__factor=factor)
    if sector:
        respuestas = respuestas.filter(sector=sector)
    nuevas = respuestas.aggregate(suma=Sum("valor"), cantidad=Count("id"))
    respuestas_tesis = EXPERTOS_TESIS * factor.subfactores.count()
    suma_total = IE_TESIS * respuestas_tesis + (nuevas["suma"] or 0)
    promedio = Decimal(suma_total) / (respuestas_tesis + nuevas["cantidad"])
    return promedio.quantize(Decimal("0.01"))


@transaction.atomic
def recalcular(sector=""):
    factores_con_citas = Factor.objects.annotate(citas=Sum("subfactores__n_citas"), cantidad=Count("subfactores"))
    factores = list(factores_con_citas.order_by("id"))
    citas_por_factor = {}
    for factor in factores:
        citas_por_factor[factor.id] = factor.citas / factor.cantidad
    niveles_literatura = importancia_literatura(citas_por_factor)
    cambios = 0
    for factor in factores:
        valor_ie = importancia_experto(factor, sector)
        valor_il = niveles_literatura[factor.id]
        valor_is = cruzar(redondear(valor_ie), valor_il)
        vigentes = factor.importancias.filter(vigente=True, sector=sector)
        actual = vigentes.first()
        if actual and (actual.valor_ie, actual.valor_il, actual.valor_is) == (valor_ie, valor_il, valor_is):
            continue
        vigentes.update(vigente=False)
        ImportanciaSugerida.objects.create(factor=factor, sector=sector, valor_ie=valor_ie, valor_il=valor_il, valor_is=valor_is)
        cambios += 1
    return cambios


def recalcular_todo(sector=""):
    con_sector = ImportanciaSugerida.objects.exclude(sector="")
    sectores = set(con_sector.values_list("sector", flat=True)) | {"", sector}
    cambios = 0
    for sector_registrado in sectores:
        cambios += recalcular(sector_registrado)
    return cambios


def iniciar_factores(evaluacion, sector):
    for factor in Factor.objects.all():
        importancia = importancia_vigente(factor, sector)
        EvaluacionFactor.objects.get_or_create(evaluacion=evaluacion, factor=factor, defaults={
            "importancia": importancia, "imp_decisor": importancia.valor_is,
            "imp_relativa": importancia.valor_is, "alcance": factor.alcance_defecto})


def actualizar_factor(evaluacion_factor, imp_decisor, alcance):
    evaluacion_factor.imp_decisor = imp_decisor
    evaluacion_factor.alcance = alcance
    evaluacion_factor.imp_relativa = cruzar(evaluacion_factor.importancia.valor_is, imp_decisor)
    if evaluacion_factor.ponderacion_media:
        evaluacion_factor.foda = clasificar(alcance, evaluacion_factor.ponderacion_media)
    evaluacion_factor.save()


def actualizar_subfactor(evaluacion_factor, subfactor, calificacion):
    evaluacion_factor.subfactores.update_or_create(subfactor=subfactor, defaults={"valor": calificacion})
    calificaciones = list(evaluacion_factor.subfactores.values_list("valor", flat=True))
    if len(calificaciones) == evaluacion_factor.factor.subfactores.count():
        evaluacion_factor.ponderacion_media = ponderacion_media(calificaciones)
        evaluacion_factor.foda = clasificar(evaluacion_factor.alcance, evaluacion_factor.ponderacion_media)
        evaluacion_factor.save()


def factores_relevantes(evaluacion):
    return evaluacion.factores.filter(imp_relativa__gt=1)


def progreso(evaluacion):
    relevantes = factores_relevantes(evaluacion)
    respondidos = 0
    total = 0
    for evaluacion_factor in relevantes.select_related("factor"):
        respondidos += evaluacion_factor.subfactores.count()
        total += evaluacion_factor.factor.subfactores.count()
    return respondidos, total


def cerrar(evaluacion):
    relevantes = factores_relevantes(evaluacion)
    evaluacion.recomendacion = recomendar(relevantes.values_list("imp_relativa", "foda"))
    evaluacion.save()
