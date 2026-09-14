import unittest
import time
from procesador_estado import ProcesadorEstado, EstadoJuegoData
from generador_respuesta import GeneradorRespuesta, AccionJuego
from sistema_progresion import SistemaProgresion
from gestor_memoria import GestorMemoriaIA
from sistema_decision_sandbox import SistemaDecisionSandbox
from sistema_decision_progresion import SistemaDecisionProgresion


class TestIAProgresionYMemoria(unittest.TestCase):

    def setUp(self):
        self.procesador = ProcesadorEstado()
        self.generador = GeneradorRespuesta(umbral_curacion=0.35, rango_ataque=200.0)
        self.progresion = SistemaProgresion(duracion_max_epoca=1.0)

    def test_procesar_json_con_mundo(self):
        raw_json = '''{
            "jugador": {
                "vida": 80,
                "vidaMaxima": 100,
                "estaMuerto": false,
                "inventario": {"Madera": 12}
            },
            "enemigoCercano": {"activo": false},
            "mundo": {"esDia": false, "tiempo": 1200.0}
        }'''

        estado = self.procesador.procesar_json(raw_json)
        self.assertEqual(estado.jugador.vida, 80)
        self.assertFalse(estado.mundo.es_dia)
        self.assertEqual(estado.jugador.cantidad_item("Madera"), 12)

    def test_sistema_puntuacion_noche(self):
        estado = EstadoJuegoData()
        estado.jugador.vida = 100
        estado.jugador.vida_maxima = 100
        estado.mundo.es_dia = False
        time.sleep(0.05)
        info = self.progresion.actualizar_progresion(estado)
        self.assertGreater(info["puntuacion"], 0)
        self.assertFalse(info["es_dia"])

    def test_sistema_sandbox_prioridades(self):
        sandbox = SistemaDecisionSandbox()
        estado = EstadoJuegoData()

        # Con 0 madera debe priorizar recolección de recursos
        propuesta = sandbox.evaluar_prioridad_sandbox(estado)
        self.assertIn("madera", propuesta["motivo"].lower())

        # Con madera suficiente y sin mesa de trabajo debe priorizar crafteo de Mesa
        estado.jugador.inventario = {"Madera": 20}
        propuesta = sandbox.evaluar_prioridad_sandbox(estado)
        self.assertEqual(propuesta["accion"], "CRAFTEAR_ESTACION")

    def test_sistema_progresion_bosses_e_hitos(self):
        prog_bosses = SistemaDecisionProgresion()
        estado = EstadoJuegoData()
        estado.jugador.vida_maxima = 100

        # Con HP baja debe estar en HITO_1 de preparación para Ojo de Cthulhu
        propuesta = prog_bosses.evaluar_prioridad_progresion(estado)
        self.assertEqual(propuesta["hito_actual"], "HITO_1_OJO_CTHULHU_PREPARACION")

        # Marcar Ojo de Cthulhu como derrotado -> Avanzar a Corrupción
        prog_bosses.jefes_derrotados.append("Ojo de Cthulhu")
        propuesta = prog_bosses.evaluar_prioridad_progresion(estado)
        self.assertEqual(propuesta["hito_actual"], "HITO_2_CORRUPCION")

        # Activar Hardmode
        prog_bosses.hardmode_activo = True
        propuesta = prog_bosses.evaluar_prioridad_progresion(estado)
        self.assertIn("HARDMODE", propuesta["hito_actual"])

    def test_coordinador_dual_generador_respuesta(self):
        estado = EstadoJuegoData()
        estado.jugador.vida = 100
        estado.jugador.vida_maxima = 100

        # Probar que el generador decide una acción y establece el modo activo
        accion = self.generador.decidir_accion(estado, self.progresion)
        self.assertIsInstance(accion, AccionJuego)
        self.assertTrue(len(self.generador.modo_activo) > 0)

    def test_transmision_inteligencia_y_descarte(self):
        gestor = GestorMemoriaIA()
        estrategia_inicial = {"objetivo": "EXPLORAR_DERECHA", "pesos_acciones": {"MOVER_DERECHA": 0.8}}

        gestor.registrar_fin_generacion(
            epoca=1,
            puntuacion=100.0,
            exito=True,
            estrategia_usada=estrategia_inicial,
            recursos={"madera": 20},
            razon_fin="TIEMPO_AGOTADO"
        )
        self.assertEqual(gestor.datos["mejor_inteligencia"]["objetivo"], "EXPLORAR_DERECHA")

        estrategia_fallida = {"objetivo": "RECOLECTAR_RECURSOS", "pesos_acciones": {}}
        gestor.registrar_fin_generacion(
            epoca=2,
            puntuacion=5.0,
            exito=False,
            estrategia_usada=estrategia_fallida,
            recursos={},
            razon_fin="MUERTE"
        )
        self.assertIn("RECOLECTAR_RECURSOS", gestor.datos["estrategias_fallidas"])

    def test_rendimientos_decrecientes_materiales(self):
        puntos_1 = self.progresion.calcular_puntos_material("madera", 0, 1)
        puntos_2 = self.progresion.calcular_puntos_material("madera", 1, 2)
        self.assertEqual(puntos_1, 10.0)
        self.assertEqual(puntos_2, 9.5)


if __name__ == "__main__":
    unittest.main()
