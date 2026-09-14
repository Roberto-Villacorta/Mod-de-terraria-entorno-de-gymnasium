import time
from typing import Dict, Any
from procesador_estado import EstadoJuegoData
from gestor_memoria import GestorMemoriaIA


class SistemaProgresion:
    """
    Gestiona el ciclo de Épocas/Generaciones basado en TIEMPO y MUERTE.
    Integra la Memoria Ligera de la IA, el sistema de Rendimientos Decrecientes
    y la Herencia de Inteligencia (transmitir si hay éxito, evitar si hay fracaso).
    """

    def __init__(self, duracion_max_epoca: float = 45.0):
        self.duracion_max_epoca = duracion_max_epoca  # Tiempo por época en segundos
        self.memoria = GestorMemoriaIA()

        self.epoca_actual: int = 1
        self.puntuacion_epoca: float = 0.0
        self.mejor_puntuacion: float = self.memoria.datos.get("mejor_puntuacion_historica", 0.0)

        # Estado del jugador en la época actual
        self.madera_max: int = 0
        self.piedra_max: int = 0
        self.posicion_inicial_x: float = 0.0
        self.max_x_alcanzado: float = 0.0
        self.min_x_alcanzado: float = 0.0

        # Control de tiempo de época
        self.ultimo_timestamp: float = time.time()
        self.tiempo_inicio_epoca: float = time.time()
        self.esta_vivo: bool = True

        # Obtener estrategia e inteligencia inicial heredada de la memoria
        self.estrategia_activa = self.memoria.obtener_estrategia_para_generacion(self.epoca_actual)

        # Configuración de Rendimientos Decrecientes (Diminishing Returns)
        self.config_materiales: Dict[str, Dict[str, float]] = {
            "madera": {"valor_base": 10.0, "factor_decaimiento": 0.95, "multiplicador_minimo": 0.05},
            "wood": {"valor_base": 10.0, "factor_decaimiento": 0.95, "multiplicador_minimo": 0.05},
            "piedra": {"valor_base": 15.0, "factor_decaimiento": 0.95, "multiplicador_minimo": 0.05},
            "stone": {"valor_base": 15.0, "factor_decaimiento": 0.95, "multiplicador_minimo": 0.05},
            "cobre": {"valor_base": 25.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "copper": {"valor_base": 25.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "hierro": {"valor_base": 35.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "iron": {"valor_base": 35.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "plomo": {"valor_base": 35.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "lead": {"valor_base": 35.0, "factor_decaimiento": 0.96, "multiplicador_minimo": 0.05},
            "oro": {"valor_base": 50.0, "factor_decaimiento": 0.97, "multiplicador_minimo": 0.05},
            "gold": {"valor_base": 50.0, "factor_decaimiento": 0.97, "multiplicador_minimo": 0.05},
        }

    def calcular_puntos_material(
        self,
        nombre_material: str,
        cant_anterior: int,
        cant_nueva: int
    ) -> float:
        """
        Calcula la recompensa por recolectar materiales aplicando Rendimientos Decrecientes.
        """
        if cant_nueva <= cant_anterior:
            return 0.0

        config = self.config_materiales.get(
            nombre_material.lower(),
            {"valor_base": 10.0, "factor_decaimiento": 0.95, "multiplicador_minimo": 0.05}
        )

        valor_base = float(config["valor_base"])
        gamma = float(config["factor_decaimiento"])
        min_mult = float(config.get("multiplicador_minimo", 0.05))

        puntos_totales = 0.0
        for k in range(cant_anterior + 1, cant_nueva + 1):
            mult = max(gamma ** (k - 1), min_mult)
            puntos_totales += valor_base * mult

        return puntos_totales

    def actualizar_progresion(self, estado: EstadoJuegoData) -> Dict[str, Any]:
        """
        Evalúa el estado actual del juego, otorga puntos de supervivencia y recursos,
        actualiza la memoria espacial y conmuta de época cuando EXPIRA EL TIEMPO o el jugador MUERE.
        """
        tiempo_ahora = time.time()
        dt = tiempo_ahora - self.ultimo_timestamp
        self.ultimo_timestamp = tiempo_ahora

        jugador = estado.jugador
        mundo = estado.mundo

        tiempo_transcurrido_epoca = tiempo_ahora - self.tiempo_inicio_epoca

        # Actualizar memoria espacial
        self.memoria.actualizar_memoria_espacial(jugador.posicion_x, jugador.posicion_y)
        self.max_x_alcanzado = max(self.max_x_alcanzado, jugador.posicion_x)
        self.min_x_alcanzado = min(self.min_x_alcanzado, jugador.posicion_x)

        # 1. COMPROBAR CONDICIONES DE FIN DE ÉPOCA (Muerte o Límite de Tiempo)
        muerto = (jugador.esta_muerto or jugador.vida <= 0) and self.esta_vivo
        tiempo_agotado = tiempo_transcurrido_epoca >= self.duracion_max_epoca

        if muerto or tiempo_agotado:
            razon_fin = "MUERTE" if muerto else "TIEMPO_AGOTADO"
            if muerto:
                self.puntuacion_epoca -= 100.0  # Penalización por morir

            # Evaluar si la generación fue un ÉXITO o FRACASO
            # Se considera éxito si sobrevivió todo el tiempo y logró puntos mínimos o exploró
            exito = (not muerto) and (self.puntuacion_epoca >= 30.0)

            # Transmitir inteligencia si se logró, o evitar usar la estrategia si fracasó
            recursos_epoca = {
                "madera": self.madera_max,
                "piedra": self.piedra_max
            }
            self.memoria.registrar_fin_generacion(
                epoca=self.epoca_actual,
                puntuacion=self.puntuacion_epoca,
                exito=exito,
                estrategia_usada=self.estrategia_activa,
                recursos=recursos_epoca,
                razon_fin=razon_fin
            )

            resumen_fin = {
                "evento": "FIN_EPOCA",
                "razon": razon_fin,
                "epoca": self.epoca_actual,
                "puntuacion_final": self.puntuacion_epoca,
                "resultado": "ÉXITO (Inteligencia heredada)" if exito else "FRACASO (Estrategia descartada)",
                "objetivo": self.estrategia_activa.get("objetivo", "DESCONOCIDO")
            }

            # Iniciar inmediatamente la siguiente época/generación
            self._iniciar_nueva_epoca(jugador.posicion_x)
            return resumen_fin

        # 2. PUNTUACIÓN POR SUPERVIVENCIA (Día vs Noche)
        puntos_supervivencia = (1.0 if mundo.es_dia else 3.0) * dt
        self.puntuacion_epoca += puntos_supervivencia

        # 3. PUNTUACIÓN POR RECURSOS (Rendimientos Decrecientes)
        cant_madera = jugador.cantidad_item("madera") + jugador.cantidad_item("wood")
        if cant_madera > self.madera_max:
            puntos_madera = self.calcular_puntos_material("madera", self.madera_max, cant_madera)
            self.puntuacion_epoca += puntos_madera
            self.madera_max = cant_madera

        cant_piedra = jugador.cantidad_item("piedra") + jugador.cantidad_item("stone")
        if cant_piedra > self.piedra_max:
            puntos_piedra = self.calcular_puntos_material("piedra", self.piedra_max, cant_piedra)
            self.puntuacion_epoca += puntos_piedra
            self.piedra_max = cant_piedra

        tiempo_restante = max(0.0, self.duracion_max_epoca - tiempo_transcurrido_epoca)

        return {
            "evento": "EN_CURSO",
            "epoca": self.epoca_actual,
            "puntuacion": self.puntuacion_epoca,
            "tiempo_restante": tiempo_restante,
            "objetivo": self.estrategia_activa.get("objetivo", "LIBRE"),
            "es_dia": mundo.es_dia,
            "madera": self.madera_max,
            "piedra": self.piedra_max
        }

    def _iniciar_nueva_epoca(self, pos_x: float):
        """Reinicia las variables de época y carga la inteligencia correspondiente."""
        self.epoca_actual += 1
        self.puntuacion_epoca = 0.0
        self.madera_max = 0
        self.piedra_max = 0
        self.posicion_inicial_x = pos_x
        self.max_x_alcanzado = pos_x
        self.min_x_alcanzado = pos_x
        self.tiempo_inicio_epoca = time.time()
        self.esta_vivo = True

        # Cargar inteligencia heredada / estrategia alternativa para la nueva época
        self.estrategia_activa = self.memoria.obtener_estrategia_para_generacion(self.epoca_actual)
