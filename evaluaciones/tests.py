from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from . import guia
from .models import Evaluacion, Factor, ImportanciaSugerida, RespuestaExperto, Subfactor

TABLA_5_3 = {"Compatibilidad": 3, "Fiabilidad": 3, "Mantenibilidad": 3, "Personalización": 3, "Prueba": 3, "Documentación": 2,
             "Portabilidad": 2, "Reusabilidad": 2, "Usabilidad": 2, "Apoyo de la alta dirección": 3, "Formación": 3, "Soporte": 3,
             "Actitud hacia el cambio": 2, "Bloqueo de proveedores": 2, "Casos de estudio de adopción": 2,
             "Centralidad de la TI": 2, "Tiempo de adopción": 2, "Coste total de propiedad": 3}
MATRIZ_GUIA = [[1, 1, 2, 2], [1, 2, 2, 3], [2, 2, 3, 3], [2, 3, 3, 4]]
PERFIL_UNEMI = ["Universidad pública", "Unas 300", "Reemplazar la suite de pago", "Sí, tenemos técnicos"]


class CalculosTest(TestCase):
    def test_matriz_de_la_guia(self):
        for importancia_decisor in range(1, 5):
            for importancia_sugerida in range(1, 5):
                esperado = MATRIZ_GUIA[importancia_decisor - 1][importancia_sugerida - 1]
                self.assertEqual(guia.cruzar(importancia_decisor, importancia_sugerida), esperado)

    def test_clasificacion_foda(self):
        self.assertEqual(guia.clasificar("Interno", 3), "Fortaleza")
        self.assertEqual(guia.clasificar("Interno", Decimal("2.99")), "Debilidad")
        self.assertEqual(guia.clasificar("Externo", 4), "Oportunidad")
        self.assertEqual(guia.clasificar("Externo", 1), "Amenaza")

    def test_recomendacion(self):
        self.assertEqual(guia.recomendar([(3, "Fortaleza"), (2, "Oportunidad")]), "A")
        self.assertEqual(guia.recomendar([(3, "Fortaleza"), (2, "Amenaza")]), "B")
        self.assertEqual(guia.recomendar([(2, "Amenaza"), (4, "Debilidad")]), "C")

    def test_is_inicial_coincide_con_la_tesis(self):
        vigentes = ImportanciaSugerida.objects.filter(vigente=True, sector="")
        calculadas = {}
        for importancia in vigentes.select_related("factor"):
            calculadas[importancia.factor.nombre] = importancia.valor_is
        self.assertEqual(calculadas, TABLA_5_3)

    def test_recalculo_guarda_el_valor_anterior(self):
        subfactor = Subfactor.objects.get(descripcion__startswith="La alta dirección")
        for numero in range(200):
            RespuestaExperto.objects.create(subfactor=subfactor, experto=f"Experto {numero}", sector="Público", valor=1)
        self.assertGreater(guia.recalcular_todo("Público"), 0)
        self.assertEqual(guia.importancia_vigente(subfactor.factor, "Público").valor_is, 2)
        self.assertEqual(guia.importancia_vigente(subfactor.factor).valor_is, 2)
        anteriores = subfactor.factor.importancias.filter(vigente=False)
        self.assertTrue(anteriores.exists())


class FlujoTest(TestCase):
    def test_evaluacion_completa(self):
        self.client.post(reverse("inicio"), {"nombre": "Ana Pérez", "cargo": "Directora de TIC", "organizacion": "UNEMI",
                                             "tamano": "Grande", "software": "LibreOffice", "version": "24.2", "licencia": "Libre"})
        evaluacion = Evaluacion.objects.get()
        for respuesta in PERFIL_UNEMI:
            self.client.post(reverse("perfil", args=[evaluacion.pk]), {"respuesta": respuesta})
        self.assertEqual(self.client.session[f"perfil_{evaluacion.pk}"]["sector"], "Público")
        self.client.post(reverse("confirmar_perfil", args=[evaluacion.pk]),
                         {"sector": "Público", "tamano": "Grande", "usuarios": "300", "necesidad": "Suite de oficina", "soporte": "Interno"})
        self.assertEqual(evaluacion.factores.count(), Factor.objects.count())
        documentacion = evaluacion.factores.get(factor__nombre="Documentación")
        self.client.post(reverse("guardar_factor", args=[documentacion.pk]), {"imp_decisor": 1, "alcance": "Externo"},
                         content_type="application/json")
        pendiente = self.client.get(reverse("resultado", args=[evaluacion.pk]))
        self.assertEqual(pendiente.status_code, 302)
        for evaluacion_factor in guia.factores_relevantes(evaluacion):
            calificacion = 2 if evaluacion_factor.factor.nombre == "Formación" else 4
            for subfactor in evaluacion_factor.factor.subfactores.all():
                self.client.post(reverse("guardar_subfactor", args=[evaluacion_factor.pk]),
                                 {"subfactor": subfactor.pk, "valor": calificacion}, content_type="application/json")
        pagina_resultado = self.client.get(reverse("resultado", args=[evaluacion.pk]))
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.recomendacion, "C")
        self.assertContains(pagina_resultado, "Formación")
        formacion = evaluacion.factores.get(factor__nombre="Formación")
        self.assertEqual(formacion.foda, "Debilidad")
