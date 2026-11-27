import json
import re
import urllib.request

from django.conf import settings

URL_API = "https://api.anthropic.com/v1/messages"

PREGUNTAS = [
    "Hola, {nombre}. Para ajustar la evaluación de {software} necesito conocer un poco a la organización. ¿A qué sector pertenece?",
    "¿Cuántas personas usarían el software, más o menos?",
    "¿Qué problema buscan resolver con este cambio?",
    "¿Cuentan con personal técnico propio para dar soporte?",
]

PALABRAS_SECTOR = {"públic": "Público", "public": "Público", "privad": "Privado", "mixt": "Mixto"}

ACCIONES = {
    "Compatibilidad": "Probar el intercambio de archivos con los sistemas actuales y definir los formatos estándar que se usarán.",
    "Fiabilidad": "Hacer un piloto controlado y registrar las fallas antes de pasar a todo el personal.",
    "Mantenibilidad": "Revisar la actividad del proyecto y elegir una versión con soporte de largo plazo.",
    "Personalización": "Revisar qué plantillas, macros o ajustes se usan hoy y probar su migración antes de adoptar.",
    "Prueba": "Preparar un entorno de pruebas donde el personal clave pueda usar el software unas semanas.",
    "Documentación": "Preparar guías cortas en español para las tareas más comunes del personal.",
    "Portabilidad": "Confirmar en qué sistemas y dispositivos se usaría y probarlo en cada uno.",
    "Reusabilidad": "Revisar la licencia y las bibliotecas disponibles para reutilizar lo que ya existe.",
    "Usabilidad": "Hacer sesiones cortas con usuarios reales para detectar dónde se traban.",
    "Apoyo de la alta dirección": "Presentar a la alta dirección los costos, beneficios y riesgos para conseguir su respaldo formal.",
    "Formación": "Armar un plan de capacitación para el personal antes del cambio.",
    "Soporte": "Designar técnicos responsables y abrir una mesa de ayuda interna durante la migración.",
    "Actitud hacia el cambio": "Comunicar el porqué del cambio y sumar a usuarios clave como promotores.",
    "Bloqueo de proveedores": "Identificar los contratos y formatos que atan al proveedor actual y planificar la salida.",
    "Casos de estudio de adopción": "Buscar organizaciones parecidas que ya lo adoptaron y conversar con ellas.",
    "Centralidad de la TI": "Centralizar la instalación y las actualizaciones desde el departamento de TIC.",
    "Tiempo de adopción": "Dividir la adopción en etapas con fechas realistas por área.",
    "Coste total de propiedad": "Calcular los costos de migración, formación y soporte, no solo el de la licencia.",
}

RAZONES = {
    "A": "todos los factores relevantes salieron como fortaleza u oportunidad",
    "B": "las debilidades o amenazas están solo en factores opcionales",
    "C": "hay debilidades o amenazas en factores que marcaste como importantes o fundamentales",
}


def consultar(instruccion):
    if not settings.IA_CLAVE:
        return {}
    # Sonnet 5.5 piensa antes de responder: se usa esfuerzo bajo (tareas cortas) y margen de tokens
    # para que el razonamiento no deje la respuesta cortada.
    cuerpo = json.dumps({"model": settings.IA_MODELO, "max_tokens": 4000, "output_config": {"effort": "low"},
                         "messages": [{"role": "user", "content": instruccion}]})
    cabeceras = {"x-api-key": settings.IA_CLAVE, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    pedido = urllib.request.Request(URL_API, cuerpo.encode(), cabeceras)
    try:
        with urllib.request.urlopen(pedido, timeout=60) as conexion:
            mensaje = json.load(conexion)
        # La respuesta puede traer primero un bloque de razonamiento; se toma el de texto.
        contenido = "".join(bloque.get("text", "") for bloque in mensaje["content"] if bloque.get("type") == "text")
        return json.loads(contenido[contenido.find("{"):contenido.rfind("}") + 1])
    except Exception:
        return {}


def preguntas(evaluacion):
    nombres = evaluacion.usuario.nombre.split()
    lista = []
    for pregunta in PREGUNTAS:
        lista.append(pregunta.format(nombre=nombres[0], software=evaluacion.software.nombre))
    return lista


def perfil_basico(respuestas):
    respuesta_sector = respuestas[0].lower()
    sector = ""
    for palabra, nombre_sector in PALABRAS_SECTOR.items():
        if palabra in respuesta_sector and not sector:
            sector = nombre_sector
    cantidad = re.search(r"\d+", respuestas[1].replace(".", ""))
    usuarios = int(cantidad[0]) if cantidad else ""
    respuesta_soporte = respuestas[3].lower()
    soporte = "Externo" if re.match(r"\s*no\b", respuesta_soporte) else "Interno"
    necesidad = respuestas[2].strip()
    return {"sector": sector, "usuarios": usuarios, "necesidad": necesidad.rstrip(".")[:120], "soporte": soporte}


def extraer_perfil(respuestas_perfil):
    conversacion = ""
    respuestas = []
    for respuesta_perfil in respuestas_perfil:
        conversacion += f"P: {respuesta_perfil.pregunta}\nR: {respuesta_perfil.respuesta}\n"
        respuestas.append(respuesta_perfil.respuesta)
    perfil = consultar(
        "Lee estas respuestas de un decisor y devuelve solo un JSON con las claves sector (Público, Privado o Mixto), "
        f"usuarios (número entero), necesidad (frase corta) y soporte (Interno o Externo).\n{conversacion}")
    return perfil or perfil_basico(respuestas)


def plan_de_accion(evaluacion, negativos, positivos):
    detalle = ""
    nombres = []
    for evaluacion_factor in negativos:
        nombre = evaluacion_factor.factor.nombre
        detalle += f"- {nombre}: {evaluacion_factor.foda}, importancia {evaluacion_factor.get_imp_relativa_display()}, PM {evaluacion_factor.ponderacion_media}\n"
        nombres.append(nombre)
    plan = consultar(
        f"Eres un asesor de adopción de software. La organización {evaluacion.usuario.organizacion.nombre} evaluó "
        f"{evaluacion.software} con la guía GUIOS y obtuvo la recomendación {evaluacion.recomendacion}. "
        f"Factores con problemas:\n{detalle}Devuelve solo un JSON con las claves explicacion (un párrafo corto, en español, "
        "tuteando al decisor) y acciones (objeto con el nombre exacto de cada factor y una acción concreta de una línea).")
    acciones_ia = plan.get("acciones", {})
    if plan and set(acciones_ia) >= set(nombres):
        return plan["explicacion"], acciones_ia, "IA"
    lista_nombres = ", ".join(nombres) or "ninguno"
    explicacion = (f"La recomendación es {evaluacion.recomendacion} porque {RAZONES[evaluacion.recomendacion]}. "
                   f"{positivos} de {positivos + len(nombres)} factores relevantes salieron bien; "
                   f"los que necesitan atención son: {lista_nombres}.")
    acciones = {}
    for nombre in nombres:
        acciones[nombre] = ACCIONES[nombre]
    return explicacion, acciones, "Plantilla"
