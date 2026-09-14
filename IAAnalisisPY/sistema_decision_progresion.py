import json
import os
from typing import Dict, Any, List
from procesador_estado import EstadoJuegoData

FILE_RECETAS = os.path.join(os.path.dirname(__file__), "recetas_terraria.json")


class SistemaDecisionProgresion:
    """
    Sistema 2: Enfoque Progresión Global de Terraria (Jefes, Hitos y Hardmode).
    Rastrea el avance del juego a largo plazo:
    - Pre-Hardmode: Ojo de Cthulhu -> Devorador/Cerebro -> Esqueletrón -> Muro de Carne.
    - Transición a HARDMODE.
    - Hardmode: Jefes Mecánicos -> Plantera -> Golem -> Cultista Lunático -> Moon Lord.
    """

    def __init__(self, ruta_recetas: str = FILE_RECETAS):
        self.ruta_recetas = ruta_recetas
        self.base_datos = self._cargar_base_datos()
        self.hardmode_activo: bool = False
        self.jefes_derrotados: List[str] = []

    def _cargar_base_datos(self) -> Dict[str, Any]:
        if os.path.exists(self.ruta_recetas):
            try:
                with open(self.ruta_recetas, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[SistemaProgresionBosses] Error al cargar base de datos ({e}).")
        return {}

    def evaluar_prioridad_progresion(self, estado: EstadoJuegoData) -> Dict[str, Any]:
        """
        Evalúa el estado de combate, armamento e hitos de jefes para proponer
        la siguiente acción de progresión en Terraria.
        """
        jugador = estado.jugador
        enemigo = estado.enemigo_cercano

        # 1. COMBATE INMEDIATO SI HAY UN JEFE ACTIVO O ENEMIGO POTENTE
        if enemigo.activo:
            es_jefe = enemigo.es_jefe or "ojo" in enemigo.nombre.lower() or "zombi" not in enemigo.nombre.lower()
            if es_jefe:
                return {
                    "accion": "LUCHAR_CONTRA_JEFE",
                    "prioridad": 0.98,
                    "herramienta_requerida": ["espada", "sword", "corta", "blade", "bow", "gun"],
                    "hito_actual": "COMBATE_JEFE",
                    "motivo": f"¡COMBATE CONTRA JEFE! Enfrentando a {enemigo.nombre} (HP: {enemigo.vida})"
                }

        # 2. EVALUACIÓN DE HITOS PRE-HARDMODE VS HARDMODE
        hp_jugador = jugador.vida_maxima
        defensa_total = jugador.defensa

        if not self.hardmode_activo:
            # HITO 1: Preparación Pre-Boss Ojo de Cthulhu
            if "Ojo de Cthulhu" not in self.jefes_derrotados:
                if hp_jugador < 200 or defensa_total < 10:
                    return {
                        "accion": "PREPARAR_PRE_BOSS",
                        "prioridad": 0.65,
                        "herramienta_requerida": ["pico", "pickaxe"],
                        "hito_actual": "HITO_1_OJO_CTHULHU_PREPARACION",
                        "motivo": f"Preparando stats para Ojo de Cthulhu (HP: {hp_jugador}/200, Def: {defensa_total}/10)"
                    }
                else:
                    return {
                        "accion": "INVOCAR_OJO_CTHULHU",
                        "prioridad": 0.88,
                        "herramienta_requerida": ["espada", "sword", "bow"],
                        "hito_actual": "HITO_1_OJO_CTHULHU_LISTO",
                        "motivo": "¡Listo para invocar y derrotar al Ojo de Cthulhu de noche!"
                    }

            # HITO 2: Devorador de Mundos / Cerebro de Cthulhu
            if "Devorador de Mundos" not in self.jefes_derrotados:
                return {
                    "accion": "EXPLORAR_CORRUPCION_CARMESI",
                    "prioridad": 0.75,
                    "herramienta_requerida": ["pico", "pickaxe"],
                    "hito_actual": "HITO_2_CORRUPCION",
                    "motivo": "Explorando bioma corrupto/carmesí para orbes y Devorador/Cerebro"
                }

            # HITO 3: Esqueletrón y Mazmorra
            if "Esqueletrón" not in self.jefes_derrotados:
                return {
                    "accion": "IR_A_LA_MAZMORRA",
                    "prioridad": 0.80,
                    "herramienta_requerida": ["espada", "sword"],
                    "hito_actual": "HITO_3_ESQUELETRON",
                    "motivo": "Viajando a la Mazmorra para hablar con el Anciano y derrotar a Esqueletrón"
                }

            # HITO 4: Muro de Carne (Paso a HARDMODE)
            if "Muro de Carne" not in self.jefes_derrotados:
                return {
                    "accion": "DESCENDER_AL_INFRAMUNDO",
                    "prioridad": 0.95,
                    "herramienta_requerida": ["pico", "pickaxe", "espada"],
                    "hito_actual": "HITO_4_MURO_DE_CARNE_HARDMODE",
                    "motivo": "¡Descendiendo al Inframundo para construir pasarela y derrotar Muro de Carne (Entrada a HARDMODE)!"
                }

        else:
            # PROGRESIÓN EN HARDMODE
            if "Plantera" not in self.jefes_derrotados:
                return {
                    "accion": "HARDMODE_JEFES_MECANICOS",
                    "prioridad": 0.90,
                    "herramienta_requerida": ["pico", "espada"],
                    "hito_actual": "HARDMODE_MECANICOS_PLANTERA",
                    "motivo": "Enfrentando Jefes Mecánicos y buscando Capullo de Plantera en la Jungla"
                }
            else:
                return {
                    "accion": "HARDMODE_CAMINO_MOON_LORD",
                    "prioridad": 0.95,
                    "herramienta_requerida": ["espada", "bow"],
                    "hito_actual": "HARDMODE_GOLEM_MOON_LORD",
                    "motivo": "Avanzando en el Templo Lihzahrd hacia Cultista Lunático y el Señor de la Luna (Moon Lord)"
                }

        return {
            "accion": "EXPLORAR_PROGRESIÓN",
            "prioridad": 0.60,
            "herramienta_requerida": [],
            "hito_actual": "PROGRESIÓN_GENERAL",
            "motivo": "Buscando nuevos hitos de progresión"
        }
