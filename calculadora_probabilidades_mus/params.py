"""
Parámetros de configuración para la Fase 2: Descarte y Rollout.

Centraliza todas las constantes y configuraciones necesarias para:
1. Simulación de rollouts (Monte Carlo con descarte)
2. Generación de políticas óptimas (Q-learning)
3. Sistema de puntuación real por equipos
4. Softmax estocástico para variabilidad
"""

# ==============================================================================
# SIMULACIÓN Y ROLLOUTS
# ==============================================================================

# Temperatura para Softmax estocástico
# Controla la aleatoriedad al elegir máscaras según sus EVs
# - tau < 1: Más explotación (elegir la mejor)
# - tau = 1: Balance neutral
# - tau > 1: Más exploración (probar subóptimas)
TAU = 0.5

# ==============================================================================
# TEMPERATURA ADAPTATIVA
# ==============================================================================
# En lugar de un TAU fijo, se adapta según la diferencia entre el mejor
# y el segundo mejor reward de las máscaras disponibles.
# - Diferencia alta → TAU bajo (explotar, la decisión es clara)
# - Diferencia baja → TAU alto (explorar, opciones similares)

TAU_ADAPTATIVO = True  # True = usar temperatura adaptativa, False = usar TAU fijo
TAU_MIN = 0.4          # Temperatura mínima (explotación cuando hay clara ventaja)
TAU_MAX = 1.5          # Temperatura máxima (exploración cuando opciones similares)
UMBRAL_DIFERENCIA_ALTO = 0.5   # Diferencia de reward para TAU mínimo
UMBRAL_DIFERENCIA_BAJO = 0.05  # Diferencia de reward para TAU máximo

# ==============================================================================
# TASA DE MUS OBJETIVO Y PARÁMETROS POSITION-AWARE
# ==============================================================================
# Tasa de mus objetivo: porcentaje esperado de manos donde los 4 jugadores
# dan mus (todos piden descarte). En partidas reales suele estar en 15-25%.
TASA_MUS_OBJETIVO = 0.20  # 20% objetivo (configurable)

# Factor de agresividad por posición para k.
# Las posiciones 1 y 3 (equipo Mano) tienden a dar más mus en el juego real
# porque se benefician de los descartes sucesivos.
# Factor < 1.0 → k más bajo → más probabilidad de dar mus.
# Factor == 1.0 → sin ajuste.
FACTOR_K_POS = {
    1: 0.75,  # Mano: 25% más agresivo pidiendo mus
    2: 1.0,   # Normal
    3: 0.75,  # Pareja de Mano: 25% más agresivo pidiendo mus
    4: 1.0    # Postre: normal
}

# Bonus adicional al EV efectivo antes del sigmoide, por posición.
# Representa el valor implícito de «quitar mano»: cortar desde postre priva
# a los rivales de puntos de desempate que, al amplificarse por las apuestas,
# valen ~2-3 pts reales. El bonus se escala con (1 − factor_desempate) y se
# calibra para que la tasa de mus del perfil normal siga siendo ~20%.
# Calibración: sweeping b4 ∈ [0,1.5] con ratio 2:1 → b4=0.30 → tasa=0.2025.
EV_CORTE_BONUS = {
    1: 0.0,   # Mano: gana todos los desempates → sin bonus por cortar
    2: 0.15,  # Interior izda. (equipo Postre): pierde la mitad de desempates
    3: 0.0,   # Interior dcha. (equipo Mano): sin bonus
    4: 0.30,  # Postre: pierde todos los desempates → máximo bonus
}

# ==================== CONFIGURACIÓN DE ITERACIONES ====================
# FASE 2: Rollout Monte Carlo para generar políticas óptimas de descarte

# Iteraciones para Q-Learning (generar_politicas_rollout.py)
# - Aumentado a 10M (100x inicial) para estadística SÓLIDA
# - Objetivo: ≥1000 visitas por estado (mano, posición, máscara)
# - Con ~20% Mus rate → ~8M universos válidos
# - 4 posiciones × 15 máscaras = 60 rollouts/universo
# - Tiempo estimado: ~8-12 horas
N_ITERACIONES_ROLLOUT = 40_000_000

# Iteraciones para simulador final (simulador_fase2.py)  
# - Aumentado a 10M (20x inicial) para máxima precisión
# - Con ~20% Mus rate → ~2M rondas válidas
# - Tiempo estimado: ~1-2 horas
N_ITERACIONES_SIMULADOR_FASE2 = 10_000_000

# ==============================================================================
# SISTEMA DE PUNTUACIÓN REAL POR LANCES
# ==============================================================================

# Puntos base por tipo de jugada (Pares)
VALORES_PUNTOS_PARES = {
    "sin_pares": 0,
    "pares": 1,
    "medias": 2,
    "duples": 3
}

# Puntos base por tipo de jugada (Juego)
# Nota: La 31 vale 3 puntos, el resto de juegos 2 puntos
VALORES_PUNTOS_JUEGO = {
    31: 3,  # El mejor juego
    32: 2,
    33: 2,
    34: 2,
    35: 2,
    36: 2,
    37: 2,
    40: 2,  # Cuatro dieces
    # Punto (< 31) no aplica aquí, vale 1 punto fijo
}

# Puntos fijos para lances lineales
PUNTOS_GRANDE = 1
PUNTOS_CHICA = 1
PUNTOS_PUNTO = 1  # Cuando no hay juego

# ==============================================================================
# EQUIPOS Y POSICIONES
# ==============================================================================

# Mapeo de posición a equipo
# Equipo A: Posiciones 1 (Mano) y 3
# Equipo B: Posiciones 2 y 4 (Postre)
EQUIPOS = {
    1: "A",
    2: "B",
    3: "A",
    4: "B"
}

# Nombres de equipos
EQUIPO_A = "A"
EQUIPO_B = "B"

# ==============================================================================
# DESEMPATES
# ==============================================================================

# Factores de desempate por posición (usado en Fase 1)
# En Fase 2 usamos desempate estricto por posición: 1 > 2 > 3 > 4
FACTORES_DESEMPATE = {
    1: 1.0,  # Mano: Gana todos los empates
    2: 0.5,
    3: 0.5,
    4: 0.0   # Postre: Pierde todos los empates
}

# ==============================================================================
# MÁSCARAS DE DESCARTE
# ==============================================================================

# Total de máscaras posibles (descartar 1, 2, 3 o 4 cartas)
N_MASCARAS = 15

# ==============================================================================
# ARCHIVOS DE ENTRADA/SALIDA
# ==============================================================================

# Archivo con políticas óptimas generadas por Q-learning
ARCHIVO_POLITICAS_FASE2 = "politicas_optimas_fase2.csv"

# Archivo con probabilidades tras descarte óptimo
ARCHIVO_PROBABILIDADES_FASE2 = "probabilidades_fase2.csv"

# Archivo con estadísticas de Fase 1 (primeras dadas)
ARCHIVO_ESTADISTICAS_FASE1_8REYES = "resultados_8reyes.csv"
ARCHIVO_ESTADISTICAS_FASE1_4REYES = "resultados_4reyes.csv"

# ==============================================================================
# MODOS DE BARAJA
# ==============================================================================

# Modo de baraja predeterminado para Fase 2
MODO_8_REYES = True  # True para 8 reyes, False para 4 reyes tradicional

# ==============================================================================
# PARÁMETROS DE Q-LEARNING
# ==============================================================================

# Mínimo de visitas para considerar una entrada válida en Q-Table
MIN_VISITAS_QTABLE = 10

# Factor de descuento para rewards futuros (no usado aún, para extensión)
GAMMA = 1.0  # Sin descuento (juego de una ronda)

# ==============================================================================
# CONFIGURACIÓN DE VERBOSIDAD
# ==============================================================================

# Mostrar progreso cada N iteraciones
PRINT_PROGRESO_CADA = 10_000

# Modo silencioso (no imprimir durante simulaciones)
SILENT_MODE = False

# ==============================================================================
# VALIDACIÓN Y SANITY CHECKS
# ==============================================================================

# Límite de diferencia esperada vs real para validar simulaciones
TOLERANCIA_VALIDACION = 0.05  # 5% de margen

# Semilla aleatoria para reproducibilidad (None = aleatoria)
RANDOM_SEED = None  # Cambiar a int para reproducibilidad

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def obtener_equipo(posicion):
    """
    Obtiene el equipo de una posición.
    
    Args:
        posicion: Posición del jugador (1-4)
    
    Returns:
        str: "A" o "B"
    """
    return EQUIPOS[posicion]


def son_pareja(posicion1, posicion2):
    """
    Verifica si dos posiciones son pareja (mismo equipo).
    
    Args:
        posicion1: Primera posición (1-4)
        posicion2: Segunda posición (1-4)
    
    Returns:
        bool: True si son del mismo equipo
    """
    return EQUIPOS[posicion1] == EQUIPOS[posicion2]


def obtener_companero(posicion):
    """
    Obtiene la posición del compañero.
    
    Args:
        posicion: Posición del jugador (1-4)
    
    Returns:
        int: Posición del compañero
        
    Ejemplo:
        >>> obtener_companero(1)
        3
        >>> obtener_companero(2)
        4
    """
    if posicion == 1:
        return 3
    elif posicion == 2:
        return 4
    elif posicion == 3:
        return 1
    else:  # posicion == 4
        return 2


def obtener_rivales(posicion):
    """
    Obtiene las posiciones de los rivales.
    
    Args:
        posicion: Posición del jugador (1-4)
    
    Returns:
        list: Lista con las dos posiciones rivales
        
    Ejemplo:
        >>> obtener_rivales(1)
        [2, 4]
        >>> obtener_rivales(2)
        [1, 3]
    """
    if posicion in [1, 3]:  # Equipo A
        return [2, 4]
    else:  # Equipo B
        return [1, 3]


if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURACIÓN DE PARÁMETROS - FASE 2")
    print("=" * 70)
    
    print("\n📊 SIMULACIÓN:")
    print(f"  - Temperatura Softmax (τ fija): {TAU}")
    print(f"  - Temperatura adaptativa: {TAU_ADAPTATIVO}")
    if TAU_ADAPTATIVO:
        print(f"    - TAU_MIN: {TAU_MIN}, TAU_MAX: {TAU_MAX}")
        print(f"    - Umbral diferencia alto: {UMBRAL_DIFERENCIA_ALTO}")
        print(f"    - Umbral diferencia bajo: {UMBRAL_DIFERENCIA_BAJO}")
    print(f"  - Iteraciones Rollout: {N_ITERACIONES_ROLLOUT:,}")
    print(f"  - Iteraciones Simulador: {N_ITERACIONES_SIMULADOR_FASE2:,}")
    print(f"  - Tasa de Mus objetivo: {TASA_MUS_OBJETIVO:.0%}")
    
    print("\n🎯 FACTOR K POR POSICIÓN:")
    for pos, factor in FACTOR_K_POS.items():
        equipo = obtener_equipo(pos)
        ajuste = f"{(1-factor)*100:.0f}% más agresivo" if factor < 1.0 else "sin ajuste"
        print(f"  Posición {pos} (Equipo {equipo}): factor={factor} ({ajuste})")
    
    print("\n💰 PUNTUACIÓN:")
    print(f"  - Grande: {PUNTOS_GRANDE} punto")
    print(f"  - Chica: {PUNTOS_CHICA} punto")
    print(f"  - Pares: {VALORES_PUNTOS_PARES}")
    print(f"  - Juego: {VALORES_PUNTOS_JUEGO}")
    
    print("\n👥 EQUIPOS:")
    for pos in [1, 2, 3, 4]:
        equipo = obtener_equipo(pos)
        companero = obtener_companero(pos)
        rivales = obtener_rivales(pos)
        print(f"  Posición {pos}: Equipo {equipo} | Compañero: {companero} | Rivales: {rivales}")
    
    print("\n🎭 MÁSCARAS:")
    print(f"  - Total de máscaras: {N_MASCARAS}")
    
    print("\n📁 ARCHIVOS:")
    print(f"  - Políticas: {ARCHIVO_POLITICAS_FASE2}")
    print(f"  - Probabilidades: {ARCHIVO_PROBABILIDADES_FASE2}")
    
    print("\n✓ Configuración cargada correctamente")
