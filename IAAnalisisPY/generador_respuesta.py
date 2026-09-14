from enum import IntEnum
from typing import List, Optional, Dict, Any
from procesador_estado import EstadoJuegoData
from sistema_progresion import SistemaProgresion
from sistema_decision_sandbox import SistemaDecisionSandbox
from sistema_decision_progresion import SistemaDecisionProgresion


class AccionJuego(IntEnum):
    QUIETO = 0
    MOVER_IZQUIERDA = 1
    MOVER_DERECHA = 2
    SALTAR = 3
    ATACAR = 4
    CURAR_RAPIDO = 5
    HOTBAR_0 = 6
    HOTBAR_1 = 7
    HOTBAR_2 = 8
    HOTBAR_3 = 9
    HOTBAR_4 = 10
    HOTBAR_5 = 11
    HOTBAR_6 = 12
    HOTBAR_7 = 13
    HOTBAR_8 = 14
    HOTBAR_9 = 15


class GeneradorRespuesta:
    """
    Coordinador de IA que integra los 2 Sistemas de Toma de Decisiones:
    1. SistemaDecisionSandbox: Recursos, estaciones, construcción de casas para NPCs y mejoras.
    2. SistemaDecisionProgresion: Hitos de Terraria, jefes Pre-Hardmode, Muro de Carne, Hardmode y Moon Lord.

    Compara prioridades en tiempo real y selecciona dinámicamente qué sistema toma el control.
    """

    def __init__(self, umbral_curacion: float = 0.35, rango_ataque: float = 200.0):
        self.umbral_curacion = umbral_curacion
        self.rango_ataque = rango_ataque
        self.contador_ticks = 0

        # Los 2 Sistemas de Decisiones
        self.sistema_sandbox = SistemaDecisionSandbox()
        self.sistema_progresion_bosses = SistemaDecisionProgresion()

        # Diagnóstico del sistema activo
        self.modo_activo: str = "SANDBOX"
        self.motivo_activo: str = "Inicio"

    def decidir_accion(self, estado: EstadoJuegoData, progresion: SistemaProgresion) -> AccionJuego:
        """
        Evalúa el estado con ambos sistemas de toma de decisiones, selecciona el de mayor prioridad
        y ejecuta la acción equipando las herramientas necesarias.
        """
        self.contador_ticks += 1
        jugador = estado.jugador
        enemigo = estado.enemigo_cercano

        # Si el jugador está muerto, detener cualquier acción
        if jugador.esta_muerto or jugador.vida <= 0:
            self.modo_activo = "MUERTO"
            self.motivo_activo = "Jugador sin vida"
            return AccionJuego.QUIETO

        # 1. SALUD CRÍTICA -> Prioridad Absoluta Curación
        if jugador.porcentaje_vida < self.umbral_curacion:
            tiene_pocion = any("pocion" in item.lower() or "potion" in item.lower() for item in jugador.inventario.keys())
            if tiene_pocion:
                self.modo_activo = "SUPERVIVENCIA"
                self.motivo_activo = "Curación rápida de emergencia"
                return AccionJuego.CURAR_RAPIDO

        # 2. EVALUACIÓN PARALELA DE LOS 2 SISTEMAS
        propuesta_sandbox = self.sistema_sandbox.evaluar_prioridad_sandbox(estado)
        propuesta_progresion = self.sistema_progresion_bosses.evaluar_prioridad_progresion(estado)

        prio_sandbox = propuesta_sandbox.get("prioridad", 0.5)
        prio_progresion = propuesta_progresion.get("prioridad", 0.5)

        # Seleccionar el sistema dominante según la prioridad más alta
        if prio_progresion > prio_sandbox:
            propuesta_elegida = propuesta_progresion
            self.modo_activo = "PROGRESIÓN (JEFES/HARDMODE)"
        else:
            propuesta_elegida = propuesta_sandbox
            self.modo_activo = "SANDBOX (CASAS/RECURSOS)"

        self.motivo_activo = propuesta_elegida.get("motivo", "")
        palabras_herramienta = propuesta_elegida.get("herramienta_requerida", [])

        # 3. VERIFICAR Y EQUIPAR HERRAMIENTA REQUERIDA
        if palabras_herramienta:
            accion_equipar = self._equipar_herramienta(jugador, palabras_herramienta)
            if accion_equipar is not None:
                return accion_equipar

        # 4. EJECUCIÓN DE COMBATE O NAVEGACIÓN SEGÚN PROPUESTA
        if enemigo.activo:
            distancia_x = enemigo.distancia_relativa_x
            distancia_y = enemigo.distancia_relativa_y
            distancia_total = enemigo.distancia_euclidiana

            # Equipar arma si no la tiene
            accion_equipar = self._equipar_herramienta(jugador, ["espada", "sword", "corta", "blade", "bow", "gun"])
            if accion_equipar is not None:
                return accion_equipar

            if distancia_y < -40.0:
                return AccionJuego.SALTAR
            if distancia_total <= self.rango_ataque:
                return AccionJuego.ATACAR
            return AccionJuego.MOVER_IZQUIERDA if distancia_x < 0 else AccionJuego.MOVER_DERECHA

        # Ejecución de movimientos según objetivo activo de la generación
        estrategia = progresion.estrategia_activa
        objetivo = estrategia.get("objetivo", "EXPLORAR_DERECHA")

        accion_str = propuesta_elegida.get("accion", "")

        if accion_str in ["TALAR_ARBOL", "MINAR_PIEDRA", "CRAFTEAR_ESTACION", "PREPARAR_MATERIALES_CASA"]:
            return AccionJuego.ATACAR

        if objetivo == "EXPLORAR_IZQUIERDA":
            if self.contador_ticks % 12 == 0:
                return AccionJuego.SALTAR
            return AccionJuego.MOVER_IZQUIERDA
        else:
            if self.contador_ticks % 12 == 0:
                return AccionJuego.SALTAR
            return AccionJuego.MOVER_DERECHA

    def _equipar_herramienta(self, jugador, palabras_clave: List[str]) -> Optional[AccionJuego]:
        """
        Comprueba si la mano actual tiene alguna de las herramientas requeridas.
        Si no la tiene, devuelve el comando de la hotbar (HOTBAR_0..HOTBAR_9) para equiparla.
        """
        item_mano_lower = jugador.item_mano.lower()
        if any(kw in item_mano_lower for kw in palabras_clave):
            return None

        slot = jugador.buscar_slot_herramienta(palabras_clave)
        if slot is not None:
            return AccionJuego(AccionJuego.HOTBAR_0 + slot)

        return None
