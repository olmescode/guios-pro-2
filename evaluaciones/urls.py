from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("evaluacion/<int:evaluacion_id>/perfil/", views.perfil, name="perfil"),
    path("evaluacion/<int:evaluacion_id>/perfil/confirmar/", views.confirmar_perfil, name="confirmar_perfil"),
    path("evaluacion/<int:evaluacion_id>/factores/", views.factores, name="factores"),
    path("evaluacion/<int:evaluacion_id>/subfactores/", views.subfactores, name="subfactores"),
    path("evaluacion/<int:evaluacion_id>/resultado/", views.resultado, name="resultado"),
    path("evaluacion/<int:evaluacion_id>/informe/", views.informe, name="informe"),
    path("api/factor/<int:evaluacion_factor_id>/", views.guardar_factor, name="guardar_factor"),
    path("api/subfactor/<int:evaluacion_factor_id>/", views.guardar_subfactor, name="guardar_subfactor"),
    path("historial/", views.historial, name="historial"),
    path("historial/comparar/", views.comparar, name="comparar"),
    path("datos/", views.datos, name="datos"),
]
