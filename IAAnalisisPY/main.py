import asyncio
import sys
import websockets
from procesador_estado import ProcesadorEstado
from generador_respuesta import GeneradorRespuesta
from sistema_progresion import SistemaProgresion

URLS_SERVIDOR = ["ws://localhost:8765/", "ws://127.0.0.1:8765/"]


async def cliente_ia():
    procesador = ProcesadorEstado()
    generador = GeneradorRespuesta()
    progresion = SistemaProgresion(duracion_max_epoca=45.0)

    url_idx = 0
    while True:
        url_actual = URLS_SERVIDOR[url_idx % len(URLS_SERVIDOR)]
        try:
            print(f"[IA] Conectando al Servidor Puente de Terraria en {url_actual}...")
            async with websockets.connect(url_actual) as websocket:
                print("[IA] ¡Conexión establecida exitosamente con Terraria!")
                print("[IA] Sistema Dual (Sandbox + Progresión de Jefes / Hardmode) activo.\n")

                async for mensaje in websocket:
                    # 1. Procesar la información del estado del juego
                    estado = procesador.procesar_json(mensaje)

                    # 2. Actualizar el sistema de progresión y épocas por tiempo
                    info_prog = progresion.actualizar_progresion(estado)

                    if info_prog.get("evento") == "FIN_EPOCA":
                        razon = info_prog.get("razon", "DESCONOCIDO")
                        resultado = info_prog.get("resultado", "")
                        print(
                            f"\n🔄 [ÉPOCA {info_prog['epoca']} FINALIZADA - {razon}] 🔄\n"
                            f"   Puntuación conseguida: {info_prog['puntuacion_final']:.1f} pts\n"
                            f"   Objetivo de la generación: {info_prog['objetivo']}\n"
                            f"   Evaluación: {resultado}\n"
                            f"---------------------------------------------------\n"
                        )
                        continue

                    # 3. Generar la decisión con el Coordinador Dual de Decisiones
                    accion = generador.decidir_accion(estado, progresion)

                    # 4. Mostrar panel en consola
                    ciclo_dia = "☀️ Día" if estado.mundo.es_dia else "🌙 Noche"
                    hp_jugador = estado.jugador.vida
                    hp_max = estado.jugador.vida_maxima
                    puntos = info_prog.get("puntuacion", 0.0)
                    tiempo_rest = info_prog.get("tiempo_restante", 0.0)
                    epoca = info_prog.get("epoca", 1)

                    modo = generador.modo_activo
                    motivo = generador.motivo_activo

                    enemigo_info = (
                        f"{estado.enemigo_cercano.nombre} (HP: {estado.enemigo_cercano.vida})"
                        if estado.enemigo_cercano.activo
                        else "Ninguno"
                    )

                    print(
                        f"[ÉPOCA {epoca}] Pts: {puntos:.1f} | {tiempo_rest:.1f}s | {ciclo_dia} | "
                        f"Sistema: {modo} | Motivo: {motivo} | "
                        f"HP: {hp_jugador}/{hp_max} | Acción: {accion.name} ({int(accion)})"
                    )

                    # 5. Transmitir la respuesta al Servidor Puente en C#
                    await websocket.send(str(int(accion)))

        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidHandshake, OSError) as error:
            print(f"[IA] Conexión rechazada o no disponible en {url_actual} ({error}). Reintentando alternativo en 3s...")
            url_idx += 1
            await asyncio.sleep(3)
        except Exception as error:
            print(f"[IA] Error inesperado: {error}")
            url_idx += 1
            await asyncio.sleep(2)


def main():
    try:
        asyncio.run(cliente_ia())
    except KeyboardInterrupt:
        print("\n[IA] Cliente de IA detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
