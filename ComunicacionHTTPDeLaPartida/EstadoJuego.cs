using System;
using System.Collections.Generic;

namespace ComunicacionHTTPDeLaPartida
{
    [Serializable]
    public class DatosJugador
    {
        public int vida { get; set; }
        public int vidaMaxima { get; set; }
        public float posicionX { get; set; }
        public float posicionY { get; set; }
        public float velocidadX { get; set; }
        public float velocidadY { get; set; }
        public float defensa { get; set; }
        public bool estaMuerto { get; set; }
        public List<string> hotbar { get; set; } = new List<string>();
        public string itemMano { get; set; } = "";
        public Dictionary<string, int> inventario { get; set; } = new Dictionary<string, int>();
    }

    [Serializable]
    public class DatosEnemigo
    {
        public bool activo { get; set; }
        public int vida { get; set; }
        public int vidaMaxima { get; set; }
        public float distanciaRelativaX { get; set; }
        public float distanciaRelativaY { get; set; }
        public bool esJefe { get; set; }
        public string nombre { get; set; } = "";
    }

    [Serializable]
    public class DatosRecursosMundo
    {
        public bool hayArbolCercano { get; set; }
        public float distanciaArbolX { get; set; }
        public float distanciaArbolY { get; set; }
        public bool hayPiedraCercana { get; set; }
        public float distanciaPiedraX { get; set; }
        public float distanciaPiedraY { get; set; }
        public string bloqueBajoPies { get; set; } = "";
    }

    [Serializable]
    public class DatosMundo
    {
        public bool esDia { get; set; } = true;
        public double tiempo { get; set; }
        public DatosRecursosMundo recursos { get; set; } = new DatosRecursosMundo();
    }

    [Serializable]
    public class EstadoJuego
    {
        public DatosJugador jugador { get; set; } = new DatosJugador();
        public DatosEnemigo enemigoCercano { get; set; } = new DatosEnemigo();
        public DatosMundo mundo { get; set; } = new DatosMundo();
        public bool hayJefeActivo { get; set; }
    }
}