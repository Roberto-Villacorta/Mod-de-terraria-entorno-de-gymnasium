import json
import os
from typing import Dict, Any, Optional, Tuple
from procesador_estado import EstadoJuegoData

FILE_RECETAS = os.path.join(os.path.dirname(__file__), "recetas_terraria.json")


class SistemaDecisionSandbox:
    """
    Sistema 1: Enfoque Sandbox & Construcción.
    Considera el juego como un mundo abierto donde la prioridad es:
    - Recolectar recursos (Madera, Piedra, Minerales).
    - Fabricar componentes y estructuras (Mesa de trabajo, Horno, Paredes, Puertas, Antorchas).
    - Construir casas aptas para NPCs.
    - Mejorar herramientas, armaduras y accesorios.
    """

    def __init__(self, ruta_recetas: str = FILE_RECETAS):
        self.ruta_recetas = ruta_recetas
        self.base_datos_craft = self._cargar_base_datos()

    def _cargar_base_datos(self) -> Dict[str, Any]:
        if os.path.exists(self.ruta_recetas):
            try:
                with open(self.ruta_recetas, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[SistemaSandbox] Error al cargar recetas ({e}).")
        return {}

    def evaluar_prioridad_sandbox(self, estado: EstadoJuegoData) -> Dict[str, Any]:
        """
        Evalúa el estado del jugador y devuelve la mejor acción sandbox propuesta,
        junto con su prioridad (0.0 a 1.0) y la justificación.
        """
        jugador = estado.jugador
        recursos_mundo = estado.mundo.recursos

        cant_madera = jugador.cantidad_item("madera") + jugador.cantidad_item("wood")
        cant_piedra = jugador.cantidad_item("piedra") + jugador.cantidad_item("stone")

        tiene_mesa = jugador.cantidad_item("mesa") > 0 or jugador.cantidad_item("work bench") > 0
        tiene_horno = jugador.cantidad_item("horno") > 0 or jugador.cantidad_item("furnace") > 0

        # 1. SI RECURSOS CRÍTICOS BAJOS -> Alta prioridad recolección de Madera
        if cant_madera < 15:
            if recursos_mundo.hay_arbol_cercano and abs(recursos_mundo.distancia_arbol_x) < 50.0:
                return {
                    "accion": "TALAR_ARBOL",
                    "prioridad": 0.85,
                    "herramienta_requerida": ["hacha", "axe", "hamaxe"],
                    "motivo": f"Recolectando madera básica para construcción (Tenes: {cant_madera}/15)"
                }
            return {
                "accion": "BUSCAR_RECURSOS",
                "prioridad": 0.70,
                "herramienta_requerida": [],
                "motivo": "Explorando en busca de árboles para madera"
            }

        # 2. SI NO TIENE MESA DE TRABAJO -> Alta prioridad crafteo de Mesa
        if not tiene_mesa and cant_madera >= 10:
            return {
                "accion": "CRAFTEAR_ESTACION",
                "prioridad": 0.90,
                "herramienta_requerida": ["mesa", "work bench"],
                "motivo": "Crafteando Mesa de Trabajo básica"
            }

        # 3. CONSTRUCCIÓN DE CASA PARA NPC -> Paredes, Puerta, Antorchas
        cant_paredes = jugador.cantidad_item("pared") + jugador.cantidad_item("wall")
        cant_puertas = jugador.cantidad_item("puerta") + jugador.cantidad_item("door")
        cant_antorchas = jugador.cantidad_item("antorcha") + jugador.cantidad_item("torch")

        if tiene_mesa and (cant_paredes < 30 or cant_puertas < 1 or cant_antorchas < 4):
            return {
                "accion": "PREPARAR_MATERIALES_CASA",
                "prioridad": 0.80,
                "herramienta_requerida": ["mesa", "work bench"],
                "motivo": f"Fabricando componentes de casa para NPC (Paredes: {cant_paredes}/30, Puertas: {cant_puertas}/1)"
            }

        # 4. MINERÍA Y PIEDRA PARA HORNO Y EQUIPAMIENTO
        if cant_piedra < 20:
            if recursos_mundo.hay_piedra_cercana and abs(recursos_mundo.distancia_piedra_x) < 50.0:
                return {
                    "accion": "MINAR_PIEDRA",
                    "prioridad": 0.75,
                    "herramienta_requerida": ["pico", "pickaxe", "drill"],
                    "motivo": f"Minando piedra para Horno y forja (Tenes: {cant_piedra}/20)"
                }

        # 5. EXPLORACIÓN Y MEJORA DE REFUGIO LIBRE
        return {
            "accion": "EXPLORAR_SANDBOX",
            "prioridad": 0.50,
            "herramienta_requerida": [],
            "motivo": "Explorando biomas y expandiendo base sandbox"
        }
