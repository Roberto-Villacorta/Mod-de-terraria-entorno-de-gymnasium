using System;
using System.IO;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Terraria.ModLoader;

namespace ComunicacionHTTPDeLaPartida
{
    public class ServidorPuenteIA : ModSystem
    {
        private HttpListener _escuchadorHttp;
        private CancellationTokenSource _fuenteCancelacion;
        private static WebSocket _socketActivo;

        private const string DireccionServidor = "http://localhost:8765/";

        /// <summary>
        /// Mantiene la última acción recibida desde el entorno de Python.
        /// (0: Quieto, 1: Izquierda, 2: Derecha, 3: Saltar, 4: Atacar, 5: Curar, 6-15: Seleccionar ranura Hotbar 0-9)
        /// </summary>
        public static int UltimaAccion { get; private set; } = 0;

        /// <summary>
        /// Mantiene el índice de la ranura de hotbar a seleccionar (0-9, o -1 si no aplica).
        /// </summary>
        public static int SlotSeleccionado { get; private set; } = -1;

        /// <summary>
        /// Comprueba si hay un cliente Python conectado actualmente.
        /// </summary>
        public static bool EstaClienteConectado => _socketActivo != null && _socketActivo.State == WebSocketState.Open;

        public override void OnModLoad()
        {
            IniciarServidor();
        }

        public override void OnModUnload()
        {
            DetenerServidor();
        }

        private void IniciarServidor()
        {
            _fuenteCancelacion = new CancellationTokenSource();
            _escuchadorHttp = new HttpListener();
            _escuchadorHttp.Prefixes.Add("http://localhost:8765/");
            _escuchadorHttp.Prefixes.Add("http://127.0.0.1:8765/");

            try
            {
                _escuchadorHttp.Start();
                Mod.Logger.Info($"[PuenteIA] Servidor WebSocket iniciado en http://localhost:8765/ y http://127.0.0.1:8765/");
                Task.Run(() => EscucharConexionesAsync(_fuenteCancelacion.Token));
            }
            catch (Exception excepcion)
            {
                Mod.Logger.Error($"[PuenteIA] Error al iniciar el servidor: {excepcion.Message}");
            }
        }

        private async Task EscucharConexionesAsync(CancellationToken tokenCancelacion)
        {
            while (!tokenCancelacion.IsCancellationRequested && _escuchadorHttp.IsListening)
            {
                try
                {
                    HttpListenerContext contexto = await _escuchadorHttp.GetContextAsync();

                    if (contexto.Request.IsWebSocketRequest)
                    {
                        HttpListenerWebSocketContext contextoWebSocket = await contexto.AcceptWebSocketAsync(subProtocol: null);
                        Mod.Logger.Info("[PuenteIA] Cliente Python conectado exitosamente.");

                        _socketActivo = contextoWebSocket.WebSocket;
                        await ManejarClienteAsync(_socketActivo, tokenCancelacion);
                    }
                    else
                    {
                        contexto.Response.StatusCode = 400;
                        contexto.Response.Close();
                    }
                }
                catch (HttpListenerException) when (tokenCancelacion.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception excepcion)
                {
                    Mod.Logger.Error($"[PuenteIA] Error procesando conexiones: {excepcion.Message}");
                }
            }
        }

        private async Task ManejarClienteAsync(WebSocket socket, CancellationToken tokenCancelacion)
        {
            byte[] buffer = new byte[4096];

            try
            {
                while (socket.State == WebSocketState.Open && !tokenCancelacion.IsCancellationRequested)
                {
                    using (MemoryStream ms = new MemoryStream())
                    {
                        WebSocketReceiveResult resultado;
                        do
                        {
                            resultado = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), tokenCancelacion);

                            if (resultado.MessageType == WebSocketMessageType.Close)
                            {
                                await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Conexión cerrada", tokenCancelacion);
                                Mod.Logger.Info("[PuenteIA] Cliente Python desconectado.");
                                return;
                            }

                            ms.Write(buffer, 0, resultado.Count);
                        }
                        while (!resultado.EndOfMessage);

                        if (resultado.MessageType == WebSocketMessageType.Text)
                        {
                            string mensaje = Encoding.UTF8.GetString(ms.ToArray()).Trim();
                            ProcesarMensajeCliente(mensaje);
                        }
                    }
                }
            }
            catch (Exception excepcion) when (!tokenCancelacion.IsCancellationRequested)
            {
                Mod.Logger.Error($"[PuenteIA] Excepción en lectura de red: {excepcion.Message}");
            }
            finally
            {
                _socketActivo = null;
            }
        }

        private static void ProcesarMensajeCliente(string mensaje)
        {
            if (string.IsNullOrWhiteSpace(mensaje))
                return;

            if (int.TryParse(mensaje, out int accionIdentificada))
            {
                UltimaAccion = accionIdentificada;
                if (accionIdentificada >= 6 && accionIdentificada <= 15)
                {
                    SlotSeleccionado = accionIdentificada - 6;
                }
            }
            else
            {
                try
                {
                    using var doc = JsonDocument.Parse(mensaje);
                    if (doc.RootElement.TryGetProperty("accion", out JsonElement elemAccion) && elemAccion.TryGetInt32(out int acc))
                    {
                        UltimaAccion = acc;
                    }
                    if (doc.RootElement.TryGetProperty("slot", out JsonElement elemSlot) && elemSlot.TryGetInt32(out int slot))
                    {
                        SlotSeleccionado = slot;
                    }
                }
                catch
                {
                    // No es un JSON ni entero válido
                }
            }
        }

        /// <summary>
        /// Envía el objeto EstadoJuego serializado a formato JSON hacia el script de Python.
        /// </summary>
        public static async Task EnviarEstadoAsync(EstadoJuego estado)
        {
            if (estado == null)
                return;

            string jsonEstado = JsonSerializer.Serialize(estado);
            await EnviarEstadoAsync(jsonEstado);
        }

        /// <summary>
        /// Envía el estado serializado (string JSON) del juego hacia el script de Python.
        /// </summary>
        public static async Task EnviarEstadoAsync(string jsonEstado)
        {
            if (_socketActivo == null || _socketActivo.State != WebSocketState.Open)
                return;

            try
            {
                byte[] datosBytes = Encoding.UTF8.GetBytes(jsonEstado);
                await _socketActivo.SendAsync(
                    new ArraySegment<byte>(datosBytes),
                    WebSocketMessageType.Text,
                    endOfMessage: true,
                    CancellationToken.None
                );
            }
            catch (Exception excepcion)
            {
                ModContent.GetInstance<ServidorPuenteIA>()?.Mod?.Logger.Error($"[PuenteIA] Error enviando estado: {excepcion.Message}");
            }
        }

        private void DetenerServidor()
        {
            _fuenteCancelacion?.Cancel();

            if (_socketActivo != null)
            {
                try { _socketActivo.Dispose(); } catch { }
                _socketActivo = null;
            }

            if (_escuchadorHttp != null && _escuchadorHttp.IsListening)
            {
                try { _escuchadorHttp.Stop(); } catch { }
                try { _escuchadorHttp.Close(); } catch { }
            }

            Mod.Logger.Info("[PuenteIA] Servidor detenido.");
        }
    }
}