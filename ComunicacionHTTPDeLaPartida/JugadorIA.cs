using Microsoft.Xna.Framework;
using System;
using System.Collections.Generic;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace ComunicacionHTTPDeLaPartida
{
    public class JugadorIA : ModPlayer
    {
        public override void SetControls()
        {
            AplicarControlesEInput();
        }

        public override void PreUpdate()
        {
            AplicarControlesEInput();
        }

        private void AplicarControlesEInput()
        {
            if (!ServidorPuenteIA.EstaClienteConectado)
                return;

            int accionActual = ServidorPuenteIA.UltimaAccion;

            // Inyección básica de controles desde la IA
            Player.controlLeft = (accionActual == 1);
            Player.controlRight = (accionActual == 2);
            Player.controlJump = (accionActual == 3);
            Player.controlUseItem = (accionActual == 4);

            if (accionActual == 5)
            {
                Player.QuickHeal();
            }

            int slot = ServidorPuenteIA.SlotSeleccionado;
            if (slot >= 0 && slot < 10)
            {
                Player.selectedItem = slot;
            }

            // Si se activa el uso de ítem (ATACAR/TALAR/MINAR), controlar movimiento inteligente y posición del ratón
            if (Player.controlUseItem)
            {
                ProcesarApuntadoYMovimientoInteligente();
            }
        }

        private void ProcesarApuntadoYMovimientoInteligente()
        {
            Vector2? posObjetivoMundo = null;

            // 1. Prioridad: Enemigo en combate
            NPC enemigoCercano = ObtenerEnemigoMasCercano();
            if (enemigoCercano != null)
            {
                posObjetivoMundo = enemigoCercano.Center;
            }
            // 2. Talar Árboles (si sostiene Hacha)
            else if (Player.HeldItem != null && Player.HeldItem.axe > 0)
            {
                posObjetivoMundo = EscanearArbolCercano();
            }
            // 3. Minar Piedra (si sostiene Pico)
            else if (Player.HeldItem != null && Player.HeldItem.pick > 0)
            {
                posObjetivoMundo = EscanearPiedraCercana();
            }

            if (posObjetivoMundo.HasValue)
            {
                Vector2 objetivo = posObjetivoMundo.Value;

                // Desplazamiento automático hacia el objetivo si está alejado
                float diffX = objetivo.X - Player.Center.X;
                if (diffX > 35f)
                {
                    Player.controlRight = true;
                }
                else if (diffX < -35f)
                {
                    Player.controlLeft = true;
                }

                // Salto automático si choca contra bloques mientras camina
                if ((Player.controlLeft || Player.controlRight) && Player.velocity.X == 0f && Player.velocity.Y == 0f)
                {
                    Player.controlJump = true;
                }

                // Orientación de dirección
                Player.direction = (diffX >= 0) ? 1 : -1;

                // Convertir posición del mundo a posición de pantalla en píxeles para el ratón
                Vector2 posPantalla = objetivo - Main.screenPosition;
                int mouseX = (int)MathHelper.Clamp(posPantalla.X, 10f, Main.screenWidth - 10f);
                int mouseY = (int)MathHelper.Clamp(posPantalla.Y, 10f, Main.screenHeight - 10f);

                Main.mouseX = mouseX;
                Main.mouseY = mouseY;
            }
            else
            {
                // Si no hay objetivo detectado, avanzar a la derecha y apuntar al frente
                Player.controlRight = true;
                if (Player.velocity.X == 0f)
                {
                    Player.controlJump = true;
                }

                Vector2 posFrente = Player.Center + new Vector2(Player.direction * 80f, 0f) - Main.screenPosition;
                Main.mouseX = (int)MathHelper.Clamp(posFrente.X, 10f, Main.screenWidth - 10f);
                Main.mouseY = (int)MathHelper.Clamp(posFrente.Y, 10f, Main.screenHeight - 10f);
            }
        }

        private Vector2? EscanearArbolCercano()
        {
            int playerTileX = (int)(Player.Center.X / 16f);
            int playerTileY = (int)(Player.Center.Y / 16f);

            int rangoX = 35;
            int rangoY = 20;

            for (int r = 1; r <= rangoX; r++)
            {
                for (int dir = -1; dir <= 1; dir += 2)
                {
                    int x = playerTileX + (r * dir);
                    for (int y = playerTileY - rangoY; y <= playerTileY + rangoY; y++)
                    {
                        if (x < 0 || x >= Main.maxTilesX || y < 0 || y >= Main.maxTilesY) continue;
                        Tile tile = Main.tile[x, y];
                        if (tile != null && tile.HasTile)
                        {
                            ushort type = tile.TileType;
                            if (type == TileID.Trees || type == TileID.PalmTree || TileID.Sets.IsATreeTrunk[type])
                            {
                                return new Vector2(x * 16f + 8f, y * 16f + 8f);
                            }
                        }
                    }
                }
            }
            return null;
        }

        private Vector2? EscanearPiedraCercana()
        {
            int playerTileX = (int)(Player.Center.X / 16f);
            int playerTileY = (int)(Player.Center.Y / 16f);

            int rangoX = 25;
            int rangoY = 15;

            for (int r = 1; r <= rangoX; r++)
            {
                for (int dir = -1; dir <= 1; dir += 2)
                {
                    int x = playerTileX + (r * dir);
                    for (int y = playerTileY - 5; y <= playerTileY + rangoY; y++)
                    {
                        if (x < 0 || x >= Main.maxTilesX || y < 0 || y >= Main.maxTilesY) continue;
                        Tile tile = Main.tile[x, y];
                        if (tile != null && tile.HasTile)
                        {
                            ushort type = tile.TileType;
                            if (type == TileID.Stone || TileID.Sets.Ore[type])
                            {
                                return new Vector2(x * 16f + 8f, y * 16f + 8f);
                            }
                        }
                    }
                }
            }
            return null;
        }

        public override void PostUpdate()
        {
            if (!ServidorPuenteIA.EstaClienteConectado)
                return;

            // Recopilar información del jugador actual
            EstadoJuego estadoActual = new EstadoJuego();
            estadoActual.jugador.vida = Player.statLife;
            estadoActual.jugador.vidaMaxima = Player.statLifeMax2;
            estadoActual.jugador.posicionX = Player.position.X;
            estadoActual.jugador.posicionY = Player.position.Y;
            estadoActual.jugador.velocidadX = Player.velocity.X;
            estadoActual.jugador.velocidadY = Player.velocity.Y;
            estadoActual.jugador.defensa = Player.statDefense;
            estadoActual.jugador.estaMuerto = Player.dead;
            estadoActual.jugador.itemMano = Player.HeldItem != null && !Player.HeldItem.IsAir ? Player.HeldItem.Name : "";

            // Datos del mundo (día/noche)
            estadoActual.mundo.esDia = Main.dayTime;
            estadoActual.mundo.tiempo = Main.time;

            // Escaneo de recursos del mundo (árboles y piedra)
            Vector2? arbol = EscanearArbolCercano();
            if (arbol.HasValue)
            {
                estadoActual.mundo.recursos.hayArbolCercano = true;
                estadoActual.mundo.recursos.distanciaArbolX = arbol.Value.X - Player.Center.X;
                estadoActual.mundo.recursos.distanciaArbolY = arbol.Value.Y - Player.Center.Y;
            }

            Vector2? piedra = EscanearPiedraCercana();
            if (piedra.HasValue)
            {
                estadoActual.mundo.recursos.hayPiedraCercana = true;
                estadoActual.mundo.recursos.distanciaPiedraX = piedra.Value.X - Player.Center.X;
                estadoActual.mundo.recursos.distanciaPiedraY = piedra.Value.Y - Player.Center.Y;
            }

            // Recopilar Hotbar (primeras 10 ranuras, 0 a 9)
            estadoActual.jugador.hotbar = new List<string>();
            for (int i = 0; i < 10; i++)
            {
                Item item = Player.inventory[i];
                string nombreItem = (item != null && !item.IsAir && item.stack > 0) ? item.Name : "";
                estadoActual.jugador.hotbar.Add(nombreItem);
            }

            // Recopilar Inventario completo (ranuras 0 a 57)
            estadoActual.jugador.inventario = new Dictionary<string, int>();
            for (int i = 0; i < 58; i++)
            {
                Item item = Player.inventory[i];
                if (item != null && !item.IsAir && item.stack > 0)
                {
                    string nombreItem = item.Name;
                    if (estadoActual.jugador.inventario.ContainsKey(nombreItem))
                        estadoActual.jugador.inventario[nombreItem] += item.stack;
                    else
                        estadoActual.jugador.inventario[nombreItem] = item.stack;
                }
            }

            // Recopilar información del enemigo relevante
            NPC enemigo = ObtenerEnemigoMasCercano();
            if (enemigo != null)
            {
                estadoActual.enemigoCercano.activo = true;
                estadoActual.enemigoCercano.vida = enemigo.life;
                estadoActual.enemigoCercano.vidaMaxima = enemigo.lifeMax;
                estadoActual.enemigoCercano.distanciaRelativaX = enemigo.Center.X - Player.Center.X;
                estadoActual.enemigoCercano.distanciaRelativaY = enemigo.Center.Y - Player.Center.Y;
                estadoActual.enemigoCercano.esJefe = enemigo.boss;
                estadoActual.enemigoCercano.nombre = enemigo.FullName;
            }
            else
            {
                estadoActual.enemigoCercano.activo = false;
                estadoActual.enemigoCercano.nombre = "";
            }

            estadoActual.hayJefeActivo = ComprobarSiHayJefeActivo();

            // Transmitir objeto EstadoJuego
            _ = ServidorPuenteIA.EnviarEstadoAsync(estadoActual);
        }

        private NPC ObtenerEnemigoMasCercano()
        {
            NPC enemigoMasCercano = null;
            float distanciaMinima = 1500f;

            for (int i = 0; i < Main.maxNPCs; i++)
            {
                NPC npcActual = Main.npc[i];

                if (npcActual.active && !npcActual.friendly && npcActual.life > 0 && npcActual.damage > 0)
                {
                    float distancia = Vector2.Distance(Player.Center, npcActual.Center);
                    if (distancia < distanciaMinima)
                    {
                        distanciaMinima = distancia;
                        enemigoMasCercano = npcActual;
                    }
                }
            }

            return enemigoMasCercano;
        }

        private bool ComprobarSiHayJefeActivo()
        {
            for (int i = 0; i < Main.maxNPCs; i++)
            {
                if (Main.npc[i].active && Main.npc[i].boss)
                {
                    return true;
                }
            }
            return false;
        }
    }
}