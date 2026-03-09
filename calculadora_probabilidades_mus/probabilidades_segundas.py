"""
Estimación Monte Carlo de Probabilidades de Victoria "A Segundas"
Condicionadas al Número de Cartas Guardadas por Cada Rival.

==============================================================================
MODELO MATEMÁTICO
==============================================================================

PROBLEMA DE ESTIMACIÓN
──────────────────────
Sea h₁ ∈ H la mano final (conocida) del jugador focal J1, pos₁ ∈ {1,2,3,4}
su posición en la mesa, y k_j ∈ {0,1,2,3} el número de cartas que el jugador
j ha guardado tras la fase de descarte (señal observable). Se desea estimar:

    P(J1 gana lance L | h₁, pos₁, k₂, k₃, k₄)   ∀ L ∈ {Grande, Chica, Pares, Juego}

ESPACIO DE PROBABILIDAD
───────────────────────
Sea B la baraja (|B| = 40 con 8 reyes, |B| = 36 con 4 reyes). Fijada h₁,
el espacio muestral elemental es el conjunto de asignaciones de manos finales:

    Ω = { (h₂, h₃, h₄) : hⱼ ⊂ B \ h₁, |hⱼ| = 4, h₂ ∩ h₃ = h₂ ∩ h₄ = h₃ ∩ h₄ = ∅ }

PROCESO DE DESCARTE
───────────────────
En la fase de Mus, cada jugador j recibe un reparto inicial rⱼ (4 cartas
tomadas uniformemente de B \ h₁ \ repartidas_previas), aplica una política
de descarte πⱼ : H × {1..4} → P({0,1,2,3}) que selecciona los índices de
las cartas a eliminar, y roba tantas cartas como descartó para completar 4.
Definimos:

    n_kept_j := 4 − |πⱼ(rⱼ, posⱼ)|  ∈ {0, 1, 2, 3}

    n_kept = 0  →  descarta las 4 cartas (cambio de Mus completo)
    n_kept = 3  →  descarta únicamente 1 carta
    n_kept = 4  es imposible: si un jugador pide Mus, descarta al menos 1.

POLÍTICA ÓPTIMA π*
──────────────────
La política π* se obtiene de la Q-table calculada en la Fase 2 del proyecto.
Para cada par (mano, posición) se elige la máscara de descarte que maximiza
el reward esperado (valor de juego estimado):

    π*(h, pos) = arg max_{m ∈ M} Q(h, pos, m)

donde M = MASCARAS_DESCARTE contiene las 15 máscaras posibles de descarte
de un subconjunto no vacío de {0,1,2,3} (índices de la mano ordenada desc.).

ESTIMADOR POR REJECTION SAMPLING
─────────────────────────────────
El estimador es una media de Monte Carlo condicionada bajo π*:

    P̂(J1 gana L) = (1 / N_acc) · Σᵢ₌₁^{N_acc}  1[J1 gana L en ωᵢ]

donde {ωᵢ} son muestras aceptadas mediante el siguiente algoritmo:

  Algoritmo RS (Rejection Sampling bajo política óptima):
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ for t = 1 … MAX_ATTEMPTS:                                                │
  │   1. Proponer  : muestrear uniformemente (r₂, r₃, r₄) ⊂ B \ h₁         │
  │   2. Políticas : calcular π*(rⱼ, posⱼ) para cada j ∈ {comp, r1, r2}    │
  │   3. Observables: n̂ⱼ = 4 − |π*(rⱼ, posⱼ)|                             │
  │   4. Aceptar si: n̂₂ = k₂  ∧  n̂₃ = k₃  ∧  n̂₄ = k₄                    │
  │      Rechazar (continue) en otro caso                                    │
  │   5. Completar : cada rival roba (4 − n̂ⱼ) cartas del pozo residual     │
  │   6. Evaluar   : computar ganadores de cada lance L sobre {h₁,h₂,h₃,h₄} │
  │   7. Acumular  : incrementar win_L si J1 gana el lance L                │
  │ devolver P̂ si N_acc ≥ N_SIMS_MIN; None si la config es inviable bajo π* │
  └──────────────────────────────────────────────────────────────────────────┘

La distribución muestral aceptada es proporcional a:

    P_acc(r₂, r₃, r₄) ∝  P_prior(r₂, r₃, r₄) · 1[π* produce (k₂, k₃, k₄)]

lo que equivale, por el teorema de Bayes, a la distribución condicional
  P(r₂, r₃, r₄ | k₂, k₃, k₄) bajo la hipótesis de que los rivales juegan con π*.

GARANTÍAS ESTADÍSTICAS
──────────────────────
Por el Teorema Central del Límite, P̂ es asintóticamente normal:

    √N_acc · (P̂ − p)  →ᵈ  N(0, p(1−p))

El intervalo de confianza al 95% (z = 1.96) es:

    P̂  ±  1.96 · √( P̂(1−P̂) / N_acc )

El peor caso en varianza es p = 0.5, con anchura máxima 1.96 · √(0.25 / n):

    Error máx. E = 1.96 · √(0.25 / n)   ⟹   n_min = ⌈ (1.96 / E)² · 0.25 ⌉

    ┌─────────┬────────────┬──────────────────────────────────────────────────┐
    │   E     │   n_min    │  Uso en este módulo                              │
    ├─────────┼────────────┼──────────────────────────────────────────────────┤
    │   1 %   │   9 604    │  N_SIMS_TARGET — objetivo para estados comunes   │
    │   5 %   │     385    │  N_SIMS_MIN    — mínimo; si N_acc < 385 → None   │
    └─────────┴────────────┴──────────────────────────────────────────────────┘

DIMENSIONAMIENTO DE MAX_ATTEMPTS
─────────────────────────────────
Sea αⱼ = P(π*(rⱼ, posⱼ) produce exactamente kⱼ cartas guardadas) la tasa de
aceptación marginal para el jugador j. Bajo independencia de los repartos:

    α_config = α₂ · α₃ · α₄     →     E[N_acc] = MAX_ATTEMPTS · α_config

  Config frecuente  (kⱼ ≈ 2): αⱼ ≈ 35 %  →  α_config ≈ 4.3 %  →  E[N_acc] ≈ 21 500 ✓
  Config rara       (kⱼ = 0): αⱼ ≈  5 %  →  α_config ≈ 0.01 % →  E[N_acc] ≈    62  → None ✓

Con MAX_ATTEMPTS = 500 000 se cubren todas las configs con α_config ≥ 0.08 %
(equivalente a αⱼ ≥ 43 % en cada jugador o αⱼ ≥ 8 % si los otros dos son 100 %).

OUTPUTS
───────
  probabilidades_segundas.csv   330 manos × 4 posiciones × 64 configs = 84 480 filas
                                columnas: mano, posicion_focal, n_kept_comp,
                                          n_kept_rival1, n_kept_rival2,
                                          prob_grande, prob_chica, prob_pares,
                                          prob_juego, n_sims
                                (prob_* = None para configs inviables bajo π*)

  resumen_segundas.csv          Agregado por (posicion_focal, config), promediando
                                sobre las manos; solo filas con prob_grande IS NOT NULL.
"""

import sys
import os
import random
import multiprocessing
import pandas as pd
import numpy as np
import ast
from pathlib import Path
from collections import defaultdict
from itertools import product
from tqdm import tqdm

# Paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from calculadoramus import inicializar_baraja
from evaluador_ronda import evaluar_grande, evaluar_chica, evaluar_pares, evaluar_juego
from params import obtener_equipo, MODO_8_REYES
from mascaras_descarte import MASCARAS_DESCARTE
from descarte_heuristico import descarte_heuristico_base

# ==============================================================================
# CONFIGURACIÓN — dimensionamiento estadístico del estimador
# ==============================================================================
# Fórmula de tamaño muestral para IC 95% (z_{0.025}=1.96), peor caso p=0.5:
#
#   n_min(E) = ⌈ (1.96 / E)² · 0.25 ⌉
#
#   E = 1 %  →  n_min =  9 604   →  N_SIMS_TARGET  (objetivo nominal)
#   E = 5 %  →  n_min =    385   →  N_SIMS_MIN    (cota inferior; por debajo → None)
#
# Justificación de MAX_ATTEMPTS (número de propuestas máximo por config):
#   α_config = α₂ · α₃ · α₄  (probabilidad de aceptación conjunta bajo π*)
#   Para que E[N_acc] ≥ N_SIMS_TARGET se necesita MAX_ATTEMPTS ≥ N_SIMS_TARGET / α_config
#   Config objetivo (α_config ≈ 4.3 %):  500 000 × 0.043 ≈ 21 500 ≥ N_SIMS_TARGET  ✓
#   Config rara    (α_config ≈ 0.012%):  500 000 × 0.00012 ≈ 62 < N_SIMS_MIN → None  ✓
N_SIMS_TARGET = 10_000   # N_acc objetivo        →  IC95% con E ≤ 1 %  (peor caso p = 0.5)
N_SIMS_MIN    =    400   # N_acc mínimo aceptable →  IC95% con E ≤ 5 %  (peor caso p = 0.5)
MAX_ATTEMPTS  = 500_000  # propuestas máximas     →  cubre toda config con α_config ≥ 0.08 %

ARCHIVO_SALIDA = Path(__file__).parent / "probabilidades_segundas.csv"
ARCHIVO_RESUMEN = Path(__file__).parent / "resumen_segundas.csv"

# Estructura de equipos: A = {J1, J3},  B = {J2, J4}.
# Para cada posición focal se precalculan el compañero y los dos rivales.
# Formato: { pos_focal: (pos_compañero, [pos_rival1, pos_rival2]) }
_EQUIPO_MAP = {
    1: (3, [2, 4]),
    2: (4, [1, 3]),
    3: (1, [2, 4]),
    4: (2, [1, 3]),
}

def _otras_ordenadas(focal_pos):
    """Devuelve (compañero, rival1, rival2) ordenados por posición global ascendente."""
    partner, rivales = _EQUIPO_MAP[focal_pos]
    return partner, rivales[0], rivales[1]


# ==============================================================================
# Q-TABLE π* — cargada una vez por worker mediante Pool initializer
# ==============================================================================
# Formato del diccionario:
#   _POLITICAS_DICT[(h, pos)] = mascara
#   h       : tuple[int] — mano ordenada descendente (|h| = 4)
#   pos     : int        — posición global del jugador (1..4)
#   mascara : tuple[int] — índices de las cartas a descartar (subconjunto de {0,1,2,3})
#                          según MASCARAS_DESCARTE[mascara_idx] de politicas_optimas_fase2.csv

_POLITICAS_DICT = {}  # (mano_desc_tuple, pos_int) → mascara_tuple


def _worker_init():
    """
    Inicializador del pool de workers multiprocessing.

    Lee ``politicas_optimas_fase2.csv`` y construye el diccionario global
    ``_POLITICAS_DICT`` con la política óptima π* para cada par (mano, posición):

        π*(h, pos) = arg max_{m ∈ M} Q(h, pos, m)

    Se elige la máscara de mayor reward_promedio para cada (mano, posición).
    Las manos se normalizan a orden descendente para garantizar consistencia
    con la representación usada en simular_config.

    Complejidad: O(|politicas| · log|politicas|) por el sort interno.
    Se ejecuta una única vez por proceso worker, antes de procesar tareas.
    """
    global _POLITICAS_DICT
    politicas_path = Path(__file__).parent / "politicas_optimas_fase2.csv"
    df = pd.read_csv(politicas_path)
    df = df.sort_values('reward_promedio', ascending=False)
    df_best = df.drop_duplicates(subset=['mano', 'posicion'], keep='first')
    for _, row in df_best.iterrows():
        mano = tuple(sorted(ast.literal_eval(str(row['mano'])), reverse=True))
        pos = int(row['posicion'])
        mascara_idx = int(row['mascara_idx'])
        _POLITICAS_DICT[(mano, pos)] = MASCARAS_DESCARTE[mascara_idx]


def _one_attempt(remaining_36, n_kept_targets, pos_otros):
    """
    Ejecuta una única iteración del Algoritmo RS (ver docstring del módulo).

    Implementa los pasos 1–5 del algoritmo:
      1. Propone un reparto aleatorio uniforme: baraja ``remaining_36`` y
         toma 4 cartas consecutivas para cada jugador j ∈ pos_otros.
      2. Aplica π*(rⱼ, posⱼ). Si la mano no está en _POLITICAS_DICT
         (mano no vista en entrenamiento), usa descarte_heuristico_base como
         fallback conservador.
      3. Calcula n̂ⱼ = 4 − |π*(rⱼ, posⱼ)|.
      4. Acepta si n̂ⱼ = kⱼ ∀j; rechaza (return None, False) en otro caso.
      5. Completa las manos finales robando (4 − n̂ⱼ) cartas del pozo residual
         (24 cartas sin repartir + todas las descartadas en este intento).

    Nota: el rechazo ocurre en cuanto falla el primer jugador, sin procesar
    los restantes, para minimizar el coste por intento rechazado.

    Args:
        remaining_36   : list[int]  — 36 cartas disponibles (B \ h₁)
        n_kept_targets : list[int]  — [k_comp, k_r1, k_r2] observables
        pos_otros      : list[int]  — posiciones globales en el mismo orden

    Returns:
        (manos_finales, True)   si todos los n̂ⱼ coinciden con kⱼ
        (None, False)           si algún n̂ⱼ ≠ kⱼ  (rechazo)
    """
    pool = remaining_36.copy()
    random.shuffle(pool)
    manos_iniciales = [pool[i*4:(i+1)*4] for i in range(3)]
    deck_undealt = pool[12:]

    manos_kept = []
    descartadas = []

    for i, (n_target, pos) in enumerate(zip(n_kept_targets, pos_otros)):
        orig = sorted(manos_iniciales[i], reverse=True)
        orig_tuple = tuple(orig)

        # Política óptima de la Q-table; fallback heurístico si mano no vista
        if (orig_tuple, pos) in _POLITICAS_DICT:
            mascara = _POLITICAS_DICT[(orig_tuple, pos)]
        else:
            mascara = tuple(descarte_heuristico_base(orig, pos))

        actual_kept = 4 - len(mascara)
        if actual_kept != n_target:
            return None, False   # Rejection: política no produce el observable

        kept = [orig[j] for j in range(4) if j not in mascara]
        disc = [orig[j] for j in mascara]
        manos_kept.append(kept)
        descartadas.extend(disc)

    draw_pool = deck_undealt + descartadas
    random.shuffle(draw_pool)
    offset = 0
    manos_finales = []
    for i, n_kept in enumerate(n_kept_targets):
        n_robar = 4 - n_kept
        nueva_mano = sorted(manos_kept[i] + draw_pool[offset:offset + n_robar], reverse=True)
        offset += n_robar
        manos_finales.append(nueva_mano)

    return manos_finales, True


# ==============================================================================
# CARGA DE MANOS ÚNICAS
# ==============================================================================

def cargar_manos_unicas():
    """
    Carga el universo de manos únicas presentes en ``politicas_optimas_fase2.csv``.

    El conjunto de manos únicas corresponde a todas las combinaciones con
    repetición de 4 cartas de la baraja (orden no relevante), que en una
    baraja de 40 cartas asciende a C(40+4-1,4) sin repetición = C(43,4);
    con el filtro de las manos efectivamente vistas en la Q-table, la cifra
    práctica es 330 manos.

    Returns:
        list[tuple[int]] — manos ordenadas descendentemente (consistente con
        la representación interna de comparar_grande_chica y _POLITICAS_DICT).
    """
    politicas_path = Path(__file__).parent / "politicas_optimas_fase2.csv"
    df = pd.read_csv(politicas_path)
    # Las manos están como string "[x, y, z, w]", convertir a tupla
    manos = set()
    for mano_str in df['mano']:
        mano = tuple(ast.literal_eval(mano_str))
        manos.add(mano)
    return sorted(manos, reverse=True)


# ==============================================================================
# SIMULACIÓN CORE
# ==============================================================================

def simular_manos_rivales(remaining_36, n_kept_otros):
    """
    [DEPRECATED — no se usa en la simulación principal]

    Genera las manos finales de 3 jugadores con descarte ALEATORIO (no bajo π*).
    Conservada únicamente como referencia; el estimador correcto usa rejection
    sampling bajo la política óptima a través de ``_one_attempt``.

    Diferencia fundamental con ``_one_attempt``:
      • Esta función muestrea de P(h₂, h₃, h₄) incondicional (prior uniforme).
      • ``_one_attempt`` muestrea de P(h₂, h₃, h₄ | k₂, k₃, k₄) bajo π*.
    Usar esta función para estimar P(J1 gana | kⱼ) produce sesgo: la
    distribución marginal del descarte aleatorio no respeta la información
    contenida en la señal kⱼ, resultando en probabilidades prácticamente
    idénticas a las incondicionales (primeras).

    Args:
        remaining_36  : list[int]  — cartas disponibles (B \ h₁)
        n_kept_otros  : list[int]  — [n₂, n₃, n₄] cartas a guardar (aleatorio)

    Returns:
        list[list[int]] — [mano_j2_final, mano_j3_final, mano_j4_final]
    """
    pool = remaining_36.copy()
    random.shuffle(pool)

    # Reparto inicial: 4 cartas a cada uno de los 3 otros jugadores
    manos_iniciales = []
    for i in range(3):
        manos_iniciales.append(pool[i*4:(i+1)*4])
    deck_undealt = pool[12:]  # 24 cartas sin repartir

    # Descarte simulado
    manos_kept = []
    descartadas = []
    for i, n_kept in enumerate(n_kept_otros):
        orig = manos_iniciales[i]
        kept_idx = random.sample(range(4), n_kept)
        kept = [orig[j] for j in kept_idx]
        disc = [orig[j] for j in range(4) if j not in kept_idx]
        manos_kept.append(kept)
        descartadas.extend(disc)

    # Pozo con undealt + todos los descartados
    draw_pool = deck_undealt + descartadas
    random.shuffle(draw_pool)

    # Cada jugador roba hasta completar 4
    offset = 0
    manos_finales = []
    for i, n_kept in enumerate(n_kept_otros):
        n_robar = 4 - n_kept
        nueva_mano = sorted(manos_kept[i] + draw_pool[offset:offset + n_robar], reverse=True)
        offset += n_robar
        manos_finales.append(nueva_mano)

    return manos_finales


def simular_config(args):
    """
    Función worker: estima el vector de probabilidades de victoria para un
    estado (h₁, pos₁, k₂, k₃, k₄) mediante el Algoritmo RS completo.

    Implementa el estimador de Monte Carlo condicionado:

        P̂_L = win_L / N_acc   ∀ L ∈ {Grande, Chica, Pares, Juego}

    donde N_acc = número de intentos aceptados (N_acc ≤ N_SIMS_TARGET).

    Criterio de calidad:
      • N_acc ≥ N_SIMS_TARGET  →  IC95% con E ≤ 1 %  (estado bien muestreado)
      • N_SIMS_MIN ≤ N_acc < N_SIMS_TARGET  →  IC95% con E ≤ 5 %  (aceptable)
      • N_acc < N_SIMS_MIN  →  config inviable bajo π*: se devuelven None
        en las cuatro probabilidades (señal de config estadísticamente inválida).

    Nota sobre el orden de la mano focal:
      ``comparar_grande_chica`` realiza comparación carta a carta por índice;
      todas las manos deben estar en el mismo orden (descendente). La mano
      focal se normaliza al inicio con sorted(reverse=True).

    Args:
        args : tuple — (mano, focal_pos, n_kept_comp, n_kept_rival1,
                        n_kept_rival2, baraja_full, _)
               El último elemento es ignorado (placeholder de compatibilidad).

    Returns:
        dict con claves: mano, posicion_focal, n_kept_comp, n_kept_rival1,
        n_kept_rival2, prob_grande, prob_chica, prob_pares, prob_juego, n_sims.
        Las probabilidades son float ∈ [0,1] o None si N_acc < N_SIMS_MIN.
    """
    mano_focal, focal_pos, n_kept_comp, n_kept_rival1, n_kept_rival2, baraja_full, _ = args

    # Ordenar descendente: comparar_grande_chica es carta-a-carta, el orden debe ser consistente
    mano_focal = tuple(sorted(mano_focal, reverse=True))

    # Otras posiciones en orden ascendente global
    partner_pos, rival1_pos, rival2_pos = _otras_ordenadas(focal_pos)
    n_kept_other = {
        partner_pos: n_kept_comp,
        rival1_pos:  n_kept_rival1,
        rival2_pos:  n_kept_rival2,
    }
    otras_pos    = sorted(n_kept_other.keys())
    n_kept_otros = [n_kept_other[p] for p in otras_pos]

    remaining = list(baraja_full)
    for card in mano_focal:
        remaining.remove(card)

    equipo_focal = obtener_equipo(focal_pos)
    win_grande = win_chica = win_pares = win_juego = accepted = 0

    for _ in range(MAX_ATTEMPTS):
        if accepted >= N_SIMS_TARGET:
            break

        manos_otros, ok = _one_attempt(remaining, n_kept_otros, otras_pos)
        if not ok:
            continue

        accepted += 1
        manos = {focal_pos: list(mano_focal)}
        for i, pos in enumerate(otras_pos):
            manos[pos] = manos_otros[i]

        if evaluar_grande(manos) == focal_pos:
            win_grande += 1
        if evaluar_chica(manos) == focal_pos:
            win_chica += 1
        gan_pares, _, _, _ = evaluar_pares(manos)
        if gan_pares is not None and obtener_equipo(gan_pares) == equipo_focal:
            win_pares += 1
        gan_juego, _, _ = evaluar_juego(manos)
        if obtener_equipo(gan_juego) == equipo_focal:
            win_juego += 1

    if accepted < N_SIMS_MIN:
        # Config inviable bajo política óptima: n_accepted demasiado bajo para IC fiable
        return {
            'mano': list(mano_focal), 'posicion_focal': focal_pos,
            'n_kept_comp': n_kept_comp, 'n_kept_rival1': n_kept_rival1,
            'n_kept_rival2': n_kept_rival2,
            'prob_grande': None, 'prob_chica': None,
            'prob_pares': None, 'prob_juego': None,
            'n_sims': accepted,
        }

    return {
        'mano': list(mano_focal),
        'posicion_focal': focal_pos,
        'n_kept_comp': n_kept_comp,
        'n_kept_rival1': n_kept_rival1,
        'n_kept_rival2': n_kept_rival2,
        'prob_grande': win_grande / accepted,
        'prob_chica':  win_chica  / accepted,
        'prob_pares':  win_pares  / accepted,
        'prob_juego':  win_juego  / accepted,
        'n_sims': accepted,
    }


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 70)
    print("PROBABILIDADES A SEGUNDAS - CONDICIONADO A CARTAS GUARDADAS")
    print("=" * 70)
    print(f"Posiciones : 1, 2, 3, 4 (todas)")
    print(f"Configs/pos: 64  (comp x rival1 x rival2 in {{0,1,2,3}}^3; 0=descarta todas, 3=descarta 1)")
    print(f"N_SIMS_TARGET : {N_SIMS_TARGET:,}  (aceptadas; IC95% E<=1% para estados comunes)")
    print(f"N_SIMS_MIN    : {N_SIMS_MIN:,}   (minimo; IC95% E<=5%; por debajo -> None)")
    print(f"MAX_ATTEMPTS  : {MAX_ATTEMPTS:,}  (tope intentos; cubre acceptance >= 2%)")

    # Cargar manos únicas
    manos = cargar_manos_unicas()
    print(f"Manos unicas: {len(manos)}")

    # Baraja base
    baraja_full = inicializar_baraja(MODO_8_REYES)

    # Configs (n_comp, n_rival1, n_rival2) en {0,1,2,3}^3
    # 0 = descarta todas las cartas (guarda 0); 3 = guarda 3 (descarta solo 1)
    configs = list(product([0, 1, 2, 3], repeat=3))  # 64 configs
    n_total = len(manos) * len(configs) * 4           # 4 posiciones
    print(f"Total tareas: {n_total:,}")
    print()

    # Construir argumentos: (mano, focal_pos, n_comp, n_rival1, n_rival2, baraja, _)
    # El último elemento es ignorado en simular_config (usa N_SIMS_TARGET global)
    worker_args = []
    for focal_pos in [1, 2, 3, 4]:
        for mano in manos:
            for n_comp, n_r1, n_r2 in configs:
                worker_args.append((
                    mano, focal_pos, n_comp, n_r1, n_r2,
                    baraja_full, None
                ))

    # Lanzar pool multiproceso
    n_workers = min(multiprocessing.cpu_count(), 4)
    print(f"Lanzando {n_workers} workers en paralelo ({len(worker_args):,} tareas)...")
    print(f"Estimacion de duracion: ~{len(worker_args)*3.7/n_workers/3600:.0f}h  "
          f"(benchmark: 1.2s configs comunes, 4s configs raras, media ~3.7s/tarea)")
    print()

    try:
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(n_workers, initializer=_worker_init) as pool:
            results = []
            with tqdm(total=len(worker_args), desc="Simulando", unit="cfg",
                      dynamic_ncols=True) as pbar:
                for result in pool.imap_unordered(simular_config, worker_args, chunksize=64):
                    results.append(result)
                    pbar.update(1)
    except Exception as e:
        print(f"Multiprocessing fallo ({e}), modo single-process...")
        _worker_init()  # cargar politicas en proceso principal
        results = []
        with tqdm(total=len(worker_args), desc="Simulando (single-process)",
                  unit="cfg") as pbar:
            for result in (simular_config(a) for a in worker_args):
                results.append(result)
                pbar.update(1)

    # Construir DataFrame
    df = pd.DataFrame(results)
    df['mano'] = df['mano'].apply(str)
    df = df.sort_values(
        ['posicion_focal', 'n_kept_comp', 'n_kept_rival1', 'n_kept_rival2', 'mano']
    ).reset_index(drop=True)

    # Guardar tabla completa (incluyendo None para configs inviables)
    df.to_csv(ARCHIVO_SALIDA, index=False)
    print(f"\nTabla completa guardada: {ARCHIVO_SALIDA}")
    print(f"  Filas: {len(df):,}  |  Columnas: {list(df.columns)}")
    n_none = df['prob_grande'].isna().sum()
    print(f"  Configs marcadas None (imposibles bajo politica): {n_none:,} / {len(df):,} ({100*n_none/len(df):.1f}%)")

    # ── Tabla resumen por posicion + config (solo filas validas) ────────────
    df_valid = df.dropna(subset=['prob_grande'])
    resumen = df_valid.groupby(
        ['posicion_focal', 'n_kept_comp', 'n_kept_rival1', 'n_kept_rival2']
    ).agg(
        prob_grande=('prob_grande', 'mean'),
        prob_chica=('prob_chica', 'mean'),
        prob_pares=('prob_pares', 'mean'),
        prob_juego=('prob_juego', 'mean'),
        n_manos=('mano', 'count')
    ).reset_index()
    resumen.to_csv(ARCHIVO_RESUMEN, index=False)
    print(f"Resumen guardado: {ARCHIVO_RESUMEN}")
    print(f"  Filas resumen: {len(resumen):,}  (4 posiciones x 64 configs)")

    # ── Estadísticas rápidas ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RESUMEN: P(VICTORIA) SEGÚN CARTAS GUARDADAS (promedio sobre manos)")
    print("=" * 70)

    for pos in [1, 2, 3, 4]:
        sub = df_valid[df_valid['posicion_focal'] == pos]
        print(f"\n--- Posicion {pos} ---")
        comp_g = sub.groupby('n_kept_comp')[
            ['prob_grande', 'prob_chica', 'prob_pares', 'prob_juego']
        ].mean().round(3)
        print(" Efecto companero (por n_kept_comp):")
        print(comp_g.to_string())

    n_valid = len(df_valid)
    print()
    print("Archivos generados:")
    print(f"  {ARCHIVO_SALIDA.name}  ({len(df):,} filas totales, {n_valid:,} con datos validos)")
    print(f"  {ARCHIVO_RESUMEN.name}  ({len(resumen):,} filas)")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
