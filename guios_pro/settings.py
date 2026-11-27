import os
from pathlib import Path

ARCHIVO_CONFIGURACION = Path(__file__).resolve()
BASE_DIR = ARCHIVO_CONFIGURACION.parent.parent
SECRET_KEY = os.environ.get("GUIOS_SECRET_KEY", "clave-solo-para-desarrollo")
DEBUG = os.environ.get("GUIOS_DEBUG", "1") == "1"
HOSTS = os.environ.get("GUIOS_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = HOSTS.split(",")

HOST_RENDER = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if HOST_RENDER:
    ALLOWED_HOSTS.append(HOST_RENDER)
    CSRF_TRUSTED_ORIGINS = [f"https://{HOST_RENDER}"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "evaluaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "guios_pro.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "guios_pro.wsgi.application"

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("GUIOS_DB_NOMBRE", "guios_pro"),
    "USER": os.environ.get("GUIOS_DB_USUARIO", "postgres"),
    "PASSWORD": os.environ.get("GUIOS_DB_CLAVE", ""),
    "HOST": os.environ.get("GUIOS_DB_HOST", "localhost"),
    "PORT": os.environ.get("GUIOS_DB_PUERTO", "5432"),
}}

LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

IA_CLAVE = os.environ.get("GUIOS_IA_CLAVE", "")
IA_MODELO = os.environ.get("GUIOS_IA_MODELO", "claude-sonnet-5-5")
