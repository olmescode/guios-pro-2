# GUIOS PRO 2.0

Sistema web para evaluar si un software, libre o privativo, es adecuado para implementarse en una organización. Automatiza los seis pasos de la guía GUIOS propuesta en la tesis de Rea Sánchez (2022) y moderniza el prototipo GUIOS PRO (GUIOSAD v0.1.2).

Proyecto de la asignatura Procesos y Calidad de Software, UNEMI, Grupo 3.

## Qué incluye

- Registro sencillo del decisor (nombre, cargo y organización) y del software a evaluar.
- Perfil de la organización con un asistente de cuatro preguntas.
- Pasos 1 y 2: importancia del decisor y alcance elegible en los 18 factores, con la explicación de cada Importancia Relativa.
- Pasos 3 y 4: los 61 subfactores en una sola pantalla con guardado automático.
- Pasos 5 y 6: análisis FODA y recomendación A, B o C, que solo se emite cuando todo está evaluado.
- Explicación y plan de acción editables (con IA si se configura una clave; si no, con sugerencias automáticas).
- Historial con filtros, comparación de dos evaluaciones e informe para guardar en PDF.
- Datos de la guía: ingreso de respuestas de expertos y citas nuevas, con recálculo automático de IE, IL e IS y registro de los valores anteriores.

## Tecnologías

Python 3.12 o superior, Django 5.2 y PostgreSQL 16.

## Instalación

1. Crear la base de datos en PostgreSQL:

   ```sql
   CREATE DATABASE guios_pro;
   ```

2. Clonar el repositorio e instalar las dependencias:

   ```bash
   git clone https://github.com/olmescode/guios-pro-2.git
   cd guios-pro-2
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   En Linux o macOS el entorno se activa con `source .venv/bin/activate`.

3. Indicar la contraseña del usuario `postgres` (PowerShell):

   ```powershell
   $env:GUIOS_DB_CLAVE = "tu_contraseña"
   ```

4. Crear las tablas y cargar los datos de la guía:

   ```bash
   python manage.py migrate
   ```

5. Iniciar el servidor y abrir http://127.0.0.1:8000:

   ```bash
   python manage.py runserver
   ```

## Variables de entorno

| Variable | Valor por defecto | Uso |
|---|---|---|
| `GUIOS_DB_NOMBRE` | `guios_pro` | Nombre de la base de datos |
| `GUIOS_DB_USUARIO` | `postgres` | Usuario de PostgreSQL |
| `GUIOS_DB_CLAVE` | vacío | Contraseña de PostgreSQL |
| `GUIOS_DB_HOST` / `GUIOS_DB_PUERTO` | `localhost` / `5432` | Servidor de la base de datos |
| `GUIOS_IA_CLAVE` | vacío | Clave de la API de Anthropic; sin ella el sistema funciona con sugerencias automáticas |
| `GUIOS_IA_MODELO` | `claude-sonnet-5-5` | Modelo de lenguaje que se usaría |

## Pruebas

```bash
python manage.py test evaluaciones
```

Las pruebas comprueban la matriz de la guía, la clasificación FODA, las tres recomendaciones, que la Importancia Sugerida inicial coincida con la Tabla 5.3 de la tesis, el recálculo con datos nuevos y una evaluación completa de principio a fin.

## Estructura

```
guios_pro/            configuración del proyecto Django
evaluaciones/
  models.py           las 12 tablas del diseño físico
  guia.py             cálculos de la guía GUIOS (IR, PM, FODA, recomendación e IS)
  ia.py               asistente de perfil y plan de acción, con respaldo si la IA falla
  views.py, urls.py   pantallas y guardado automático
  data/guia.json      dimensiones, factores, subfactores y citas de la tesis
  templates/, static/ interfaz web
```

## Referencia

Rea Sánchez, V. H. (2022). *Factores para la adopción de soluciones basadas en software libre y fuentes abiertas* [Tesis doctoral, Universidad de Sevilla].
