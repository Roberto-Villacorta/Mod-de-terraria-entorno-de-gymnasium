# Mod de Terraria - Entorno de Aprendizaje para IA

Este proyecto conecta un mod desarrollado para tModLoader (Terraria) con un agente de Inteligencia Artificial en Python mediante WebSockets. El objetivo es proporcionar un entorno interactivo donde una IA pueda percibir el estado del juego en tiempo real, tomar decisiones y ejecutar acciones en la partida.

## Arquitectura del Proyecto

El sistema está dividido en dos componentes principales:

1. **ComunicacionHTTPDeLaPartida (Mod de tModLoader en C#)**
   - Actúa como servidor WebSocket local en la dirección `http://localhost:8765/`.
   - Extrae el estado del juego (posición del jugador, vida, inventario, estado del mundo y enemigos cercanos) y lo serializa en JSON.
   - Recibe comandos numéricos o JSON desde el cliente de Python y los ejecuta en el juego (movimiento, ataques, curación o cambio de ranura en la barra de accesos directos).

2. **IAAnalisisPY (Cliente y Controlador en Python)**
   - Se conecta al servidor WebSocket emitido por el mod.
   - Procesa los paquetes JSON recibidos mediante un procesador de estado.
   - Gestiona la evaluación por épocas y el sistema de recompensas o puntuación según los objetivos alcanzados.
   - Toma decisiones utilizando un motor dual de comportamiento (modo libre/sandbox y modo combate/progresión).

## Requisitos Previos

- **Terraria** con **tModLoader** instalado.
- **Python 3.10** o superior.
- **SDK de .NET** (necesario si vas a compilar o modificar el mod en C#).

## Instalación y Configuración

### 1. Configuración del Mod en C#

1. Copia o enlaza la carpeta `ComunicacionHTTPDeLaPartida` dentro del directorio de mods de tModLoader:
   `Documentos/My Games/Terraria/tModLoader/ModSources/`
2. Abre tModLoader, ve a la sección de **Fuentes de Mods** (Mod Sources), selecciona `ComunicacionHTTPDeLaPartida` y haz clic en **Compilar y Cargar** (Build & Reload).
3. Asegúrate de que el mod esté habilitado en la lista de mods.

### 2. Configuración del Entorno de Python

1. Accede al directorio del cliente en Python:
   ```bash
   cd IAAnalisisPY
   ```
2. Crea e inicia un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate
   ```
3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

1. Inicia Terraria a través de tModLoader y entra en un mundo con tu personaje. El servidor del mod se iniciará automáticamente escuchando en el puerto `8765`.
2. Ejecuta el script principal de Python:
   ```bash
   python IAAnalisisPY/main.py
   ```
3. Observa la consola de Python para ver las métricas de la época actual, las decisiones tomadas y la puntuación obtenida en tiempo real.

Para realizar pruebas aisladas del sistema de decisiones o simular un servidor sin abrir el juego, puedes ejecutar:
```bash
python IAAnalisisPY/test_ia.py
```

## Flujo de Datos

- **Servidor (Mod C#)** -> Envía paquete JSON con la estructura completa de `EstadoJuego` en cada actualización relevante.
- **Cliente (Python)** -> Recibe el JSON, calcula la mejor respuesta y responde con el identificador numérico de la acción (por ejemplo: `1` para izquierda, `3` para saltar, `4` para atacar).
