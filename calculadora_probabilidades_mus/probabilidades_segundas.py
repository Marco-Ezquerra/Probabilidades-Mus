"""
Probabilidades de Victoria "A Segundas" Condicionadas al Descarte Rival.

Para cada combinación de (mano_final_j1, n_cartas_guardadas_j2, n_cartas_guardadas_j3,
n_cartas_guardadas_j4), calcula mediante simulación Monte Carlo:
  - P(J1 gana Grande)
  - P(J1 gana Chica)
  - P(Equipo A gana Pares)
  - P(Equipo A gana Juego/Punto)

Modelo de simulación:
  - J1 tiene su mano final conocida (4 cartas fijas)
  - Los 36 cartas restantes se reparten: 4 iniciales a J2, 4 a J3, 4 a J4 + 24 sin repartir
  - Cada jugador "guarda" n_kept cartas de su mano inicial (aleatorio) y descarta el resto
  - Los descartados se devuelven al pozo y cada jugador roba hasta completar 4 cartas

Outputs:
  - probabilidades_segundas.csv   : tabla completa (330 manos × 64 configs)
  - resumen_segundas.csv          : agregado por config (64 configs) promediando manos
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

# Paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from calculadoramus import inicializar_baraja
from evaluador_ronda import evaluar_grande, evaluar_chica, evaluar_pares, evaluar_juego
from params import obtener_equipo, MODO_8_REYES
from mascaras_descarte import MASCARAS_DESCARTE
from descarte_heuristico import descarte_heuristico_base

# ==============================================================================
# CONFIGURACIÓN — dimensionamiento estadístico
# ==============================================================================
# IC 95% (z=1.96) para proporción p, peor caso p=0.5:  n = (1.96/E)^2 × 0.25
#   E=1%  → n = 9604   ← objetivo para estados comunes
#   E=5%  → n = 385    ← mínimo aceptable para estados raros
#
# Acceptance rate mínima estimada bajo Q-policy:
#   Cada jugador: P(n_kept=0 | política) ≈ 5%  → config más rara (0,0,0): 0.05³ = 0.0125%
#   Con MAX_ATTEMPTS=500_000: esperamos 0.0125% × 500k = 62 muestras < N_SIMS_MIN
#   → esas configs imposibles quedan marcadas como None (correcto semánticamente).
#   Config más frecuente (2,2,2): acceptance ≈ 0.35³ = 4.3% → 500k × 0.043 = 21.500 ≥ 9604 ✓
N_SIMS_TARGET = 10_000   # aceptadas deseadas → IC95% con E ≤ 1%  (peor caso p=0.5)
N_SIMS_MIN    =    400   # mínimo aceptable   → IC95% con E ≤ 5%  (peor caso p=0.5)
MAX_ATTEMPTS  = 500_000  # tope de intentos por config (cubre acceptance ≥ 2%)

ARCHIVO_SALIDA = Path(__file__).parent / "probabilidades_segundas.csv"
ARCHIVO_RESUMEN = Path(__file__).parent / "resumen_segundas.csv"

# Equipos: A=(1,3), B=(2,4)
# Para cada posición focal, calcula quién es compañero y quiénes son rivales
# La clave de esta tabla es: {focal_pos: (partner_pos, [rival1_pos, rival2_pos])}
_EQUIPO_MAP = {
    1: (3, [2, 4]),
    2: (4, [1, 3]),
    3: (1, [2, 4]),
    4: (2, [1, 3]),
}

def _otras_ordenadas(focal_pos):
    """Devuelve (partner, rival1, rival2) en orden global de pos ascendente."""
    partner, rivales = _EQUIPO_MAP[focal_pos]
    return partner, rivales[0], rivales[1]


# ==============================================================================
# Q-TABLE POLICY — cargada una vez por worker (Pool initializer)
# ==============================================================================

_POLITICAS_DICT = {}  # {(mano_tuple_desc, pos): mascara_tuple_de_indices}


def _worker_init():
    """
    Inicializador del pool de workers. Carga la política óptima de descarte
    (Q-table) en el proceso worker para usarla en rejection sampling.
    La clave es (mano_sorted_desc, posicion) → máscara de índices a descartar.
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
    Un intento de muestreo con rejection sampling bajo política Q-table.

    Reparte 4 cartas a cada uno de los 3 rivales/compañero desde `remaining_36`,
    aplica la política óptima a cada uno y comprueba si el n_kept resultante
    coincide con el observable `n_kept_targets`. Si alguno no coincide → REJECTION.

    Args:
        remaining_36  : list[int] — las 36 cartas que no tiene el jugador focal
        n_kept_targets: list[int] — [n_comp, n_r1, n_r2] cartas observadas guardadas
        pos_otros     : list[int] — posiciones globales en el mismo orden

    Returns:
        (manos_finales, True)  si todos los n_kept coinciden con la política
        (None, False)          si alguno no coincide (rejection)
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
    """Carga las 330 manos únicas de politicas_optimas_fase2.csv."""
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
    Simula las manos finales de los 3 jugadores restantes dado cuántas cartas
    ha guardado cada uno (n_kept_otros = [n2, n3, n4]).

    Proceso:
      1. Barajar los 36 cartas restantes
      2. Repartir 4 iniciales a cada jugador (12 en total)
      3. Cada jugador guarda n_i cartas aleatorias de su mano inicial
      4. Los descartados van al pozo (24 undealt + descartados)
      5. Cada jugador roba hasta completar 4

    Returns:
        list[list]: [mano_j2_final, mano_j3_final, mano_j4_final]
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
    Worker: estima P(victoria lance) para un estado (mano_focal, pos, n_comp, n_r1, n_r2)
    mediante rejection sampling bajo política Q-table.

    Ejecuta hasta MAX_ATTEMPTS intentos. Acepta solo los intentos en que los
    tres rivales/compañero aplican su política óptima y obtienen exactamente
    n_kept_* cartas guardadas. Si n_accepted < N_SIMS_MIN → devuelve None en
    todas las probabilidades (config imposible bajo política óptima).

    n_kept ∈ {0,1,2,3}: 0=descarta todas las cartas, 3=descarta solo 1.
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

    try:
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(n_workers, initializer=_worker_init) as pool:
            results = pool.map(simular_config, worker_args, chunksize=64)
    except Exception as e:
        print(f"Multiprocessing fallo ({e}), modo single-process...")
        _worker_init()  # cargar politicas en proceso principal
        results = [simular_config(a) for a in worker_args]

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
