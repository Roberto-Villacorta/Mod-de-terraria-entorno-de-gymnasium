import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DatosJugador:
    vida: int = 0
    vida_maxima: int = 100
    posicion_x: float = 0.0
    posicion_y: float = 0.0
    velocidad_x: float = 0.0
    velocidad_y: float = 0.0
    defensa: float = 0.0
    esta_muerto: bool = False
    hotbar: List[str] = field(default_factory=list)
    item_mano: str = ""
    inventario: Dict[str, int] = field(default_factory=dict)

    @property
    def porcentaje_vida(self) -> float:
        if self.vida_maxima <= 0:
            return 0.0
        return self.vida / self.vida_maxima

    def cantidad_item(self, nombre_parcial: str) -> int:
        """Devuelve la cantidad total acumulada de un ítem en el inventario o hotbar."""
        total = 0
        nombre_lower = nombre_parcial.lower()
        for item, count in self.inventario.items():
            if nombre_lower in item.lower():
                total += count
        return total

    def buscar_slot_herramienta(self, palabras_clave: List[str]) -> Optional[int]:
        """Devuelve el índice exacto de la hotbar (0 a 9) que contiene una herramienta requerida."""
        for idx, item_nombre in enumerate(self.hotbar):
            if not item_nombre:
                continue
            item_lower = item_nombre.lower()
            if any(kw in item_lower for kw in palabras_clave):
                return idx
        return None


@dataclass
class DatosEnemigo:
    activo: bool = False
    vida: int = 0
    vida_maxima: int = 100
    distancia_relativa_x: float = 0.0
    distancia_relativa_y: float = 0.0
    es_jefe: bool = False
    nombre: str = ""

    @property
    def porcentaje_vida(self) -> float:
        if self.vida_maxima <= 0:
            return 0.0
        return self.vida / self.vida_maxima

    @property
    def distancia_euclidiana(self) -> float:
        if not self.activo:
            return float("inf")
        return math.hypot(self.distancia_relativa_x, self.distancia_relativa_y)


@dataclass
class DatosRecursosMundo:
    hay_arbol_cercano: bool = False
    distancia_arbol_x: float = 0.0
    distancia_arbol_y: float = 0.0
    hay_piedra_cercana: bool = False
    distancia_piedra_x: float = 0.0
    distancia_piedra_y: float = 0.0
    bloque_bajo_pies: str = ""


@dataclass
class DatosMundo:
    es_dia: bool = True
    tiempo: float = 0.0
    recursos: DatosRecursosMundo = field(default_factory=DatosRecursosMundo)


@dataclass
class EstadoJuegoData:
    jugador: DatosJugador = field(default_factory=DatosJugador)
    enemigo_cercano: DatosEnemigo = field(default_factory=DatosEnemigo)
    mundo: DatosMundo = field(default_factory=DatosMundo)
    hay_jefe_activo: bool = False


class ProcesadorEstado:
    """
    Clase encargada de deserializar y procesar la información del estado del juego
    recibida desde el ServidorPuenteIA en Terraria.
    """

    def __init__(self):
        self.ultimo_estado: Optional[EstadoJuegoData] = None

    def procesar_json(self, raw_json: str) -> EstadoJuegoData:
        """
        Convierte la cadena JSON del estado del juego recibida por WebSocket
        en una instancia estructurada de EstadoJuegoData.
        """
        try:
            datos = json.loads(raw_json)
        except json.JSONDecodeError as e:
            print(f"[ProcesadorEstado] Error al decodificar JSON: {e}")
            return self.ultimo_estado or EstadoJuegoData()

        jugador_raw = datos.get("jugador", {})
        enemigo_raw = datos.get("enemigoCercano", {})
        mundo_raw = datos.get("mundo", {})

        hotbar_raw = jugador_raw.get("hotbar", [])
        if isinstance(hotbar_raw, dict):
            hotbar_list = list(hotbar_raw.keys())
        else:
            hotbar_list = list(hotbar_raw)

        datos_jugador = DatosJugador(
            vida=jugador_raw.get("vida", 0),
            vida_maxima=jugador_raw.get("vidaMaxima", 100),
            posicion_x=jugador_raw.get("posicionX", 0.0),
            posicion_y=jugador_raw.get("posicionY", 0.0),
            velocidad_x=jugador_raw.get("velocidadX", 0.0),
            velocidad_y=jugador_raw.get("velocidadY", 0.0),
            defensa=jugador_raw.get("defensa", 0.0),
            esta_muerto=jugador_raw.get("estaMuerto", False),
            hotbar=hotbar_list,
            item_mano=jugador_raw.get("itemMano", ""),
            inventario=jugador_raw.get("inventario", {}),
        )

        datos_enemigo = DatosEnemigo(
            activo=enemigo_raw.get("activo", False),
            vida=enemigo_raw.get("vida", 0),
            vida_maxima=enemigo_raw.get("vidaMaxima", 100),
            distancia_relativa_x=enemigo_raw.get("distanciaRelativaX", 0.0),
            distancia_relativa_y=enemigo_raw.get("distanciaRelativaY", 0.0),
            es_jefe=enemigo_raw.get("esJefe", False),
            nombre=enemigo_raw.get("nombre", ""),
        )

        recursos_raw = mundo_raw.get("recursos", {})
        datos_recursos = DatosRecursosMundo(
            hay_arbol_cercano=recursos_raw.get("hayArbolCercano", False),
            distancia_arbol_x=recursos_raw.get("distanciaArbolX", 0.0),
            distancia_arbol_y=recursos_raw.get("distanciaArbolY", 0.0),
            hay_piedra_cercana=recursos_raw.get("hayPiedraCercana", False),
            distancia_piedra_x=recursos_raw.get("distanciaPiedraX", 0.0),
            distancia_piedra_y=recursos_raw.get("distanciaPiedraY", 0.0),
            bloque_bajo_pies=recursos_raw.get("bloqueBajoPies", ""),
        )

        datos_mundo = DatosMundo(
            es_dia=mundo_raw.get("esDia", True),
            tiempo=mundo_raw.get("tiempo", 0.0),
            recursos=datos_recursos,
        )

        estado = EstadoJuegoData(
            jugador=datos_jugador,
            enemigo_cercano=datos_enemigo,
            mundo=datos_mundo,
            hay_jefe_activo=datos.get("hayJefeActivo", False),
        )

        self.ultimo_estado = estado
        return estado
