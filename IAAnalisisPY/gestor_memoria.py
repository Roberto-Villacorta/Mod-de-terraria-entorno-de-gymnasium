import json
import os
from typing import Dict, List, Any, Tuple

FILE_MEMORIA = os.path.join(os.path.dirname(__file__), "memoria_ia.json")

OBJETIVOS_DISPONIBLES = [
    "EXPLORAR_DERECHA",
    "EXPLORAR_IZQUIERDA",
    "RECOLECTAR_RECURSOS",
    "SOBREVIVIR_Y_COMBATIR"
]


class GestorMemoriaIA:
    """
    Gestiona la memoria persistente ligera de la IA entre generaciones/épocas:
    - Ubicación en el mundo y zonas exploradas.
    - Historial de logros y recursos conseguidos.
    - Transmisión de 'inteligencia' (mejores estrategias) si una generación logra su objetivo.
    - Descarte de estrategias fallidas para evitar su reutilización.
    """

    def __init__(self, ruta_archivo: str = FILE_MEMORIA):
        self.ruta_archivo = ruta_archivo
        self.datos: Dict[str, Any] = self._cargar_memoria()

    def _cargar_memoria(self) -> Dict[str, Any]:
        default_memoria = {
            "total_epocas_jugadas": 0,
            "mejor_puntuacion_historica": 0.0,
            "memoria_espacial": {
                "x_min_explorado": 0.0,
                "x_max_explorado": 0.0,
                "ultima_posicion": [0.0, 0.0]
            },
            "recursos_max_historicos": {},
            "mejor_inteligencia": {
                "objetivo": "EXPLORAR_DERECHA",
                "pesos_acciones": {
                    "MOVER_DERECHA": 0.6,
                    "MOVER_IZQUIERDA": 0.1,
                    "SALTAR": 0.15,
                    "ATACAR": 0.15
                },
                "puntuacion_obtenida": 0.0
            },
            "estrategias_fallidas": [],
            "historial_epocas": []
        }

        if os.path.exists(self.ruta_archivo):
            try:
                with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                    cargado = json.load(f)
                    for k, v in default_memoria.items():
                        if k not in cargado:
                            cargado[k] = v
                    return cargado
            except Exception as e:
                print(f"[MemoriaIA] Error al cargar memoria JSON ({e}). Creando memoria nueva.")

        return default_memoria

    def guardar(self):
        """Guarda la memoria en disco (memoria_ia.json)."""
        try:
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoriaIA] Error al guardar memoria en disco: {e}")

    def actualizar_memoria_espacial(self, x: float, y: float):
        """Actualiza la memoria ligera sobre las zonas exploradas en el mundo."""
        espacial = self.datos["memoria_espacial"]
        espacial["ultima_posicion"] = [round(x, 2), round(y, 2)]

        if x < espacial["x_min_explorado"]:
            espacial["x_min_explorado"] = round(x, 2)
        if x > espacial["x_max_explorado"]:
            espacial["x_max_explorado"] = round(x, 2)

    def obtener_estrategia_para_generacion(self, epoca: int) -> Dict[str, Any]:
        """
        Selecciona la inteligencia/estrategia para la generación actual.
        Si la generación previa fue exitosa, hereda la mejor inteligencia.
        Si fracasó, evita usar la estrategia fallida y selecciona una alternativa.
        """
        mejor = self.datos.get("mejor_inteligencia", {})
        fallidas = set(self.datos.get("estrategias_fallidas", []))

        objetivo_base = mejor.get("objetivo", "EXPLORAR_DERECHA")

        # Si el objetivo base está marcado como fallido repetidamente, buscar una opción no fallida
        if objetivo_base in fallidas:
            opciones_validas = [obj for obj in OBJETIVOS_DISPONIBLES if obj not in fallidas]
            if opciones_validas:
                objetivo_base = opciones_validas[epoca % len(opciones_validas)]
            else:
                # Si todas fallaron, limpiar fallidas para reintentar
                self.datos["estrategias_fallidas"] = []
                objetivo_base = OBJETIVOS_DISPONIBLES[epoca % len(OBJETIVOS_DISPONIBLES)]

        return {
            "objetivo": objetivo_base,
            "pesos_acciones": mejor.get("pesos_acciones", {
                "MOVER_DERECHA": 0.6,
                "MOVER_IZQUIERDA": 0.1,
                "SALTAR": 0.15,
                "ATACAR": 0.15
            })
        }

    def registrar_fin_generacion(
        self,
        epoca: int,
        puntuacion: float,
        exito: bool,
        estrategia_usada: Dict[str, Any],
        recursos: Dict[str, int],
        razon_fin: str
    ):
        """
        Evalúa el resultado de la generación actual:
        - Si se logró (éxito), se pasa su inteligencia a la siguiente generación.
        - Si NO se logró (fracaso), se evita utilizar esa estrategia.
        """
        objetivo = estrategia_usada.get("objetivo", "EXPLORAR_DERECHA")

        if exito:
            # Transmitir inteligencia al siguiente
            self.datos["mejor_inteligencia"] = {
                "objetivo": objetivo,
                "pesos_acciones": estrategia_usada.get("pesos_acciones", {}),
                "puntuacion_obtenida": round(puntuacion, 2)
            }
            if puntuacion > self.datos["mejor_puntuacion_historica"]:
                self.datos["mejor_puntuacion_historica"] = round(puntuacion, 2)
        else:
            # Evitar usar esta estrategia en el futuro cercano
            if objetivo not in self.datos["estrategias_fallidas"]:
                self.datos["estrategias_fallidas"].append(objetivo)

        # Actualizar historial de recursos
        for rec, cant in recursos.items():
            max_ant = self.datos["recursos_max_historicos"].get(rec, 0)
            if cant > max_ant:
                self.datos["recursos_max_historicos"][rec] = cant

        # Registrar época en el historial ligero (mantener últimas 10 épocas)
        self.datos["total_epocas_jugadas"] += 1
        resumen_epoca = {
            "epoca": epoca,
            "puntuacion": round(puntuacion, 2),
            "resultado": "ÉXITO" if exito else "FRACASO",
            "objetivo": objetivo,
            "razon": razon_fin
        }

        self.datos["historial_epocas"].append(resumen_epoca)
        if len(self.datos["historial_epocas"]) > 10:
            self.datos["historial_epocas"].pop(0)

        self.guardar()
