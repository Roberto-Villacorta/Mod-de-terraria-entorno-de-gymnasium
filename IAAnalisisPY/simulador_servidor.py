import asyncio
import json
import websockets

NOMBRES_ACCIONES = {
    0: "QUIETO",
    1: "MOVER_IZQUIERDA",
    2: "MOVER_DERECHA",
    3: "SALTAR",
    4: "ATACAR",
    5: "CURAR_RAPIDO",
    6: "HOTBAR_0",
    7: "HOTBAR_1",
    8: "HOTBAR_2",
    9: "HOTBAR_3",
    10: "HOTBAR_4",
    11: "HOTBAR_5",
    12: "HOTBAR_6",
    13: "HOTBAR_7",
    14: "HOTBAR_8",
    15: "HOTBAR_9"
}


async def simular_teraria(websocket):
    print("[Simulador] Cliente de IA conectado. Simulando épocas y memoria de Terraria...\n")

    escenarios = [
        {
            "descripcion": "Generación 1: Recolección y exploración diurna",
            "estado": {
                "jugador": {
                    "vida": 100,
                    "vidaMaxima": 100,
                    "posicionX": 500.0,
                    "posicionY": 200.0,
                    "defensa": 5.0,
                    "estaMuerto": False,
                    "hotbar": ["Hacha de cobre"],
                    "itemMano": "Hacha de cobre",
                    "inventario": {"Hacha de cobre": 1, "Madera": 12}
                },
                "enemigoCercano": {"activo": False},
                "mundo": {"esDia": True, "tiempo": 1000.0},
                "hayJefeActivo": False
            }
        },
        {
            "descripcion": "Generación 1: Noche con zombi en combate",
            "estado": {
                "jugador": {
                    "vida": 90,
                    "vidaMaxima": 100,
                    "defensa": 5.0,
                    "estaMuerto": False,
                    "hotbar": ["Espada corta de cobre"],
                    "itemMano": "Espada corta de cobre",
                    "inventario": {"Madera": 25}
                },
                "enemigoCercano": {
                    "activo": True,
                    "vida": 45,
                    "vidaMaxima": 45,
                    "distanciaRelativaX": 80.0,
                    "distanciaRelativaY": 0.0,
                    "nombre": "Zombi"
                },
                "mundo": {"esDia": False, "tiempo": 15000.0},
                "hayJefeActivo": False
            }
        },
        {
            "descripcion": "Generación 1: Muerte del jugador (Transmisión o descarte de inteligencia)",
            "estado": {
                "jugador": {
                    "vida": 0,
                    "vidaMaxima": 100,
                    "estaMuerto": True,
                    "inventario": {}
                },
                "enemigoCercano": {"activo": False},
                "mundo": {"esDia": False, "tiempo": 16000.0},
                "hayJefeActivo": False
            }
        }
    ]

    try:
        for i, escenario in enumerate(escenarios, 1):
            print(f"--- [Paso {i}/3] {escenario['descripcion']} ---")
            json_str = json.dumps(escenario['estado'])

            await websocket.send(json_str)

            respuesta = await websocket.recv()
            accion_num = int(respuesta) if respuesta.isdigit() else -1
            nombre_accion = NOMBRES_ACCIONES.get(accion_num, "DESCONOCIDA")
            print(f"<- [Simulador] Respuesta de IA: Código {respuesta} ({nombre_accion})\n")

            await asyncio.sleep(2)

        print("[Simulador] Prueba de simulación finalizada con éxito.")
    except websockets.exceptions.ConnectionClosed:
        print("[Simulador] El cliente de IA se ha desconectado.")


async def main():
    print("[Simulador] Iniciando servidor en ws://127.0.0.1:8765 ...")
    async with websockets.serve(simular_teraria, "127.0.0.1", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Simulador] Servidor simulador detenido.")
