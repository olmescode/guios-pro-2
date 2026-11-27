import json
from operator import attrgetter

from django.contrib import messages
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import guia, ia
from .models import (NIVELES, SECTORES, TAMANOS, Evaluacion, EvaluacionFactor, Factor, ImportanciaSugerida,
                     Organizacion, RespuestaExperto, RespuestaPerfil, Software, Subfactor, Usuario)

CUADRANTES = [("Fortaleza", "Fortalezas", "Internos · PM ≥ 3"), ("Debilidad", "Debilidades", "Internos · PM < 3"),
              ("Oportunidad", "Oportunidades", "Externos · PM ≥ 3"), ("Amenaza", "Amenazas", "Externos · PM < 3")]
CAMPOS_PERFIL = ("sector", "usuarios", "necesidad", "soporte")


def buscar_evaluacion(evaluacion_id):
    evaluaciones = Evaluacion.objects.select_related("usuario__organizacion", "software")
    return get_object_or_404(evaluaciones, pk=evaluacion_id)


def resumen_guia():
    respuestas_nuevas = RespuestaExperto.objects.values("experto")
    expertos_nuevos = respuestas_nuevas.distinct()
    return {"factores": Factor.objects.count(), "subfactores": Subfactor.objects.count(),
            "respuestas": guia.EXPERTOS_TESIS + expertos_nuevos.count()}


def siguiente_paso(evaluacion):
    if evaluacion.recomendacion:
        return "resultado"
    return "factores" if evaluacion.factores.exists() else "perfil"


def inicio(request):
    if request.method == "POST":
        formulario = request.POST
        organizacion, creada = Organizacion.objects.update_or_create(
            nombre=formulario["organizacion"].strip(), defaults={"tamano": formulario["tamano"]})
        usuario = Usuario.objects.create(organizacion=organizacion, nombre=formulario["nombre"].strip(), cargo=formulario["cargo"].strip())
        software = Software.objects.create(nombre=formulario["software"].strip(), version=formulario["version"].strip(),
                                           tipo_licencia=formulario["licencia"])
        evaluacion = Evaluacion.objects.create(usuario=usuario, software=software)
        return redirect("perfil", evaluacion.pk)
    terminadas = Evaluacion.objects.exclude(recomendacion="")
    recientes = terminadas.select_related("usuario", "software")[:4]
    return render(request, "evaluaciones/inicio.html", {"recientes": recientes, "resumen": resumen_guia(), "tamanos": TAMANOS})


def perfil(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    preguntas = ia.preguntas(evaluacion)
    respuestas = list(evaluacion.perfil.all())
    clave_sesion = f"perfil_{evaluacion_id}"
    if request.method == "POST" and len(respuestas) < len(preguntas):
        respuesta = request.POST["respuesta"]
        RespuestaPerfil.objects.create(evaluacion=evaluacion, pregunta=preguntas[len(respuestas)], respuesta=respuesta.strip())
        respuestas = list(evaluacion.perfil.all())
        if len(respuestas) == len(preguntas):
            request.session[clave_sesion] = ia.extraer_perfil(respuestas)
        return redirect("perfil", evaluacion_id)
    completo = len(respuestas) == len(preguntas)
    perfil_detectado = request.session.get(clave_sesion, {})
    importancias_sector = ImportanciaSugerida.objects.filter(sector=perfil_detectado.get("sector", ""), vigente=True)
    return render(request, "evaluaciones/perfil.html", {
        "ev": evaluacion, "paso": 1, "respuestas": respuestas, "perfil": perfil_detectado,
        "siguiente": "" if completo else preguntas[len(respuestas)],
        "sectores": SECTORES, "tamanos": TAMANOS, "is_sector": importancias_sector.exists()})


@require_POST
def confirmar_perfil(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    organizacion = evaluacion.usuario.organizacion
    organizacion.sector = request.POST["sector"]
    organizacion.tamano = request.POST["tamano"]
    organizacion.save()
    perfil_confirmado = {}
    for campo in CAMPOS_PERFIL:
        perfil_confirmado[campo] = request.POST[campo]
    request.session[f"perfil_{evaluacion_id}"] = perfil_confirmado
    guia.iniciar_factores(evaluacion, organizacion.sector)
    return redirect("factores", evaluacion_id)


def factores(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    if not evaluacion.factores.exists():
        return redirect("perfil", evaluacion_id)
    filas = evaluacion.factores.select_related("factor__dimension", "importancia")
    relevantes = guia.factores_relevantes(evaluacion)
    return render(request, "evaluaciones/factores.html", {
        "ev": evaluacion, "paso": 2, "filas": filas, "niveles": NIVELES, "relevantes": relevantes.count()})


@require_POST
def guardar_factor(request, evaluacion_factor_id):
    evaluacion_factor = get_object_or_404(EvaluacionFactor, pk=evaluacion_factor_id)
    cambios = json.loads(request.body)
    guia.actualizar_factor(evaluacion_factor, int(cambios["imp_decisor"]), cambios["alcance"])
    relevantes = guia.factores_relevantes(evaluacion_factor.evaluacion)
    return JsonResponse({"ir": evaluacion_factor.imp_relativa, "ir_texto": evaluacion_factor.get_imp_relativa_display(),
                         "relevantes": relevantes.count()})


def subfactores(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    relevantes = guia.factores_relevantes(evaluacion)
    bloques = []
    abierto = 0
    for evaluacion_factor in relevantes.select_related("factor"):
        calificaciones = dict(evaluacion_factor.subfactores.values_list("subfactor_id", "valor"))
        filas = []
        for subfactor in evaluacion_factor.factor.subfactores.all():
            filas.append((subfactor, calificaciones.get(subfactor.id, 0)))
        if len(calificaciones) < len(filas) and not abierto:
            abierto = evaluacion_factor.pk
        bloques.append((evaluacion_factor, filas, len(calificaciones)))
    respondidos, total = guia.progreso(evaluacion)
    return render(request, "evaluaciones/subfactores.html", {
        "ev": evaluacion, "paso": 3, "bloques": bloques, "hechos": respondidos, "total": total, "abierto": abierto})


@require_POST
def guardar_subfactor(request, evaluacion_factor_id):
    evaluacion_factor = get_object_or_404(EvaluacionFactor.objects.select_related("factor"), pk=evaluacion_factor_id)
    calificacion = json.loads(request.body)
    subfactor = get_object_or_404(Subfactor, pk=calificacion["subfactor"], factor=evaluacion_factor.factor)
    guia.actualizar_subfactor(evaluacion_factor, subfactor, int(calificacion["valor"]))
    respondidos, total = guia.progreso(evaluacion_factor.evaluacion)
    ponderacion = f"{evaluacion_factor.ponderacion_media:.2f}" if evaluacion_factor.ponderacion_media else ""
    return JsonResponse({"pm": ponderacion.replace(".", ","), "foda": evaluacion_factor.foda,
                         "respondidos": evaluacion_factor.subfactores.count(), "hechos": respondidos, "total": total})


def preparar_resultado(evaluacion):
    guia.cerrar(evaluacion)
    relevantes = guia.factores_relevantes(evaluacion)
    relevantes = list(relevantes.select_related("factor"))
    negativos = []
    sin_accion = not evaluacion.explicacion_ia
    for evaluacion_factor in relevantes:
        if evaluacion_factor.foda in guia.FODA_NEGATIVO:
            negativos.append(evaluacion_factor)
            sin_accion = sin_accion or not evaluacion_factor.accion_ia
    if sin_accion:
        evaluacion.explicacion_ia, acciones, evaluacion.fuente_ia = ia.plan_de_accion(evaluacion, negativos, len(relevantes) - len(negativos))
        evaluacion.save()
        for evaluacion_factor in negativos:
            evaluacion_factor.accion_ia = acciones[evaluacion_factor.factor.nombre]
            evaluacion_factor.save()
    return relevantes, negativos


def contexto_resultado(evaluacion):
    relevantes, negativos = preparar_resultado(evaluacion)
    cuadrantes = []
    for clave, titulo, regla in CUADRANTES:
        factores_cuadrante = []
        for evaluacion_factor in relevantes:
            if evaluacion_factor.foda == clave:
                factores_cuadrante.append(evaluacion_factor)
        cuadrantes.append((clave, titulo, regla, factores_cuadrante))
    negativos.sort(key=attrgetter("imp_relativa"), reverse=True)
    return {"ev": evaluacion, "paso": 4, "foda": cuadrantes, "negativos": negativos}


def resultado(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    respondidos, total = guia.progreso(evaluacion)
    if respondidos < total or total == 0:
        messages.warning(request, "Todavía faltan subfactores por evaluar.")
        return redirect("subfactores", evaluacion_id)
    if request.method == "POST":
        explicacion = request.POST["explicacion"]
        evaluacion.explicacion_ia = explicacion.strip()
        evaluacion.save()
        for evaluacion_factor in evaluacion.factores.filter(foda__in=guia.FODA_NEGATIVO):
            accion = request.POST.get(f"accion_{evaluacion_factor.pk}", evaluacion_factor.accion_ia)
            evaluacion_factor.accion_ia = accion.strip()
            evaluacion_factor.save()
        messages.success(request, "Cambios guardados.")
        return redirect("resultado", evaluacion_id)
    contexto = contexto_resultado(evaluacion)
    contexto["editar"] = "editar" in request.GET
    return render(request, "evaluaciones/resultado.html", contexto)


def informe(request, evaluacion_id):
    evaluacion = buscar_evaluacion(evaluacion_id)
    contexto = contexto_resultado(evaluacion)
    contexto["filas"] = evaluacion.factores.select_related("factor__dimension")
    contexto["perfil"] = evaluacion.perfil.all()
    return render(request, "evaluaciones/informe.html", contexto)


def historial(request):
    filtros = request.GET
    evaluaciones = Evaluacion.objects.select_related("usuario__organizacion", "software")
    if filtros.get("software"):
        evaluaciones = evaluaciones.filter(software__nombre__icontains=filtros["software"])
    if filtros.get("resultado"):
        evaluaciones = evaluaciones.filter(recomendacion=filtros["resultado"])
    if filtros.get("desde"):
        evaluaciones = evaluaciones.filter(fecha__date__gte=filtros["desde"])
    if filtros.get("hasta"):
        evaluaciones = evaluaciones.filter(fecha__date__lte=filtros["hasta"])
    filas = []
    for evaluacion in evaluaciones:
        filas.append((evaluacion, siguiente_paso(evaluacion)))
    return render(request, "evaluaciones/historial.html", {"lista": filas, "f": filtros})


def comparar(request):
    primera = buscar_evaluacion(request.GET.get("a", 0))
    segunda = buscar_evaluacion(request.GET.get("b", 0))
    primeros = {}
    for evaluacion_factor in primera.factores.all():
        primeros[evaluacion_factor.factor_id] = evaluacion_factor
    filas = []
    for evaluacion_factor in segunda.factores.select_related("factor"):
        filas.append((evaluacion_factor.factor, primeros.get(evaluacion_factor.factor_id), evaluacion_factor))
    return render(request, "evaluaciones/comparar.html", {"a": primera, "b": segunda, "filas": filas})


def guardar_dato(formulario):
    subfactor = get_object_or_404(Subfactor, pk=formulario["subfactor"])
    if formulario["accion"] == "experto":
        RespuestaExperto.objects.create(subfactor=subfactor, experto=formulario["experto"].strip(), sector=formulario["sector"],
                                        valor=int(formulario["valor"]))
    if formulario["accion"] == "citas":
        subfactor.n_citas += int(formulario["citas"])
        subfactor.save()
    return guia.recalcular_todo(formulario.get("sector", ""))


def datos(request):
    if request.method == "POST":
        cambios = guardar_dato(request.POST)
        aviso = "Dato guardado. La Importancia Sugerida se recalculó y no cambió."
        if cambios > 0:
            aviso = f"Dato guardado. La Importancia Sugerida se recalculó y se guardaron {cambios} cálculo(s) nuevo(s) en su historial."
        messages.success(request, aviso)
        return redirect("datos")
    importancias_por_factor = ImportanciaSugerida.objects.values("factor")
    calculos_por_factor = importancias_por_factor.annotate(cantidad=Count("id"))
    calculos = dict(calculos_por_factor.values_list("factor", "cantidad"))
    factores_guia = Factor.objects.select_related("dimension")
    factores_guia = factores_guia.annotate(ns=Count("subfactores"), tc=Sum("subfactores__n_citas"))
    filas = []
    for factor in factores_guia.order_by("id"):
        filas.append((factor, guia.importancia_vigente(factor), calculos[factor.id]))
    ultimas = RespuestaExperto.objects.select_related("subfactor__factor")
    return render(request, "evaluaciones/datos.html", {
        "filas": filas, "resumen": resumen_guia(), "sectores": SECTORES, "niveles": NIVELES,
        "factores": Factor.objects.prefetch_related("subfactores"), "ultimas": ultimas.order_by("-fecha")[:5]})
