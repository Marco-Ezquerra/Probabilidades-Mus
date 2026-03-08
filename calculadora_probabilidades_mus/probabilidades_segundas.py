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

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
N_SIMS_PER_CONFIG = 3000   # Simulaciones por (mano, posicion, n_comp, n_rival1, n_rival2)
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
    Worker: simula N_SIMS para una (mano_focal, focal_pos, n_comp, n_rival1, n_rival2).

    Parámetros de args:
        mano_focal   : tuple con 4 cartas del jugador focal
        focal_pos    : posición del jugador focal (1-4)
        n_kept_comp  : cartas guardadas por el compañero
        n_kept_rival1: cartas guardadas por el rival 1
        n_kept_rival2: cartas guardadas por el rival 2
        baraja_full  : lista completa de 40 cartas
        n_sims       : número de simulaciones

    Returns dict con probabilidades estimadas.
    """
    mano_focal, focal_pos, n_kept_comp, n_kept_rival1, n_kept_rival2, baraja_full, n_sims = args

    # Determinar otras posiciones en orden global ascendente
    partner_pos, rival1_pos, rival2_pos = _otras_ordenadas(focal_pos)
    # Mapear cuántas guardan según su posición global
    n_kept_other = {}  # {pos_global: n_kept}
    n_kept_other[partner_pos] = n_kept_comp
    n_kept_other[rival1_pos]  = n_kept_rival1
    n_kept_other[rival2_pos]  = n_kept_rival2

    # Orden esperado por simular_manos_rivales: otras posiciones en orden global
    otras_pos = sorted(n_kept_other.keys())
    n_kept_otros = [n_kept_other[p] for p in otras_pos]

    # Construir deck sin las cartas de la mano focal
    remaining = list(baraja_full)
    for card in mano_focal:
        remaining.remove(card)

    equipo_focal = obtener_equipo(focal_pos)

    win_grande = 0
    win_chica = 0
    win_pares = 0
    win_juego = 0

    for _ in range(n_sims):
        manos_otros = simular_manos_rivales(remaining, n_kept_otros)
        manos = {focal_pos: list(mano_focal)}
        for i, pos in enumerate(otras_pos):
            manos[pos] = manos_otros[i]

        # Grande
        gan_grande = evaluar_grande(manos)
        if gan_grande == focal_pos:
            win_grande += 1

        # Chica
        gan_chica = evaluar_chica(manos)
        if gan_chica == focal_pos:
            win_chica += 1

        # Pares
        gan_pares, tipo_pares, _, _ = evaluar_pares(manos)
        if gan_pares is not None and obtener_equipo(gan_pares) == equipo_focal:
            win_pares += 1

        # Juego/Punto
        gan_juego, _, _ = evaluar_juego(manos)
        if obtener_equipo(gan_juego) == equipo_focal:
            win_juego += 1

    return {
        'mano': list(mano_focal),
        'posicion_focal': focal_pos,
        'n_kept_comp': n_kept_comp,
        'n_kept_rival1': n_kept_rival1,
        'n_kept_rival2': n_kept_rival2,
        'prob_grande': win_grande / n_sims,
        'prob_chica': win_chica / n_sims,
        'prob_pares': win_pares / n_sims,
        'prob_juego': win_juego / n_sims,
        'n_sims': n_sims,
    }


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 70)
    print("PROBABILIDADES A SEGUNDAS - CONDICIONADO A CARTAS GUARDADAS")
    print("=" * 70)
    print(f"Posiciones : 1, 2, 3, 4 (todas)")
    print(f"Configs/pos: 64  (comp x rival1 x rival2 ∈ {{1,2,3,4}}^3)")
    print(f"Sims/config: {N_SIMS_PER_CONFIG:,}")

    # Cargar manos únicas
    manos = cargar_manos_unicas()
    print(f"Manos unicas: {len(manos)}")

    # Baraja base
    baraja_full = inicializar_baraja(MODO_8_REYES)

    # Configs (n_comp, n_rival1, n_rival2) ∈ {1,2,3,4}^3
    configs = list(product([1, 2, 3, 4], repeat=3))  # 64 configs
    n_total = len(manos) * len(configs) * 4           # 4 posiciones
    print(f"Total tareas: {n_total:,}")
    print()

    # Construir argumentos: (mano, focal_pos, n_comp, n_rival1, n_rival2, baraja, n_sims)
    worker_args = []
    for focal_pos in [1, 2, 3, 4]:
        for mano in manos:
            for n_comp, n_r1, n_r2 in configs:
                worker_args.append((
                    mano, focal_pos, n_comp, n_r1, n_r2,
                    baraja_full, N_SIMS_PER_CONFIG
                ))

    # Lanzar pool multiproceso
    n_workers = min(multiprocessing.cpu_count(), 4)
    print(f"Lanzando {n_workers} workers en paralelo ({len(worker_args):,} tareas)...")

    try:
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(n_workers) as pool:
            results = pool.map(simular_config, worker_args, chunksize=64)
    except Exception as e:
        print(f"Multiprocessing fallo ({e}), modo single-process...")
        results = [simular_config(a) for a in worker_args]

    # Construir DataFrame
    df = pd.DataFrame(results)
    df['mano'] = df['mano'].apply(str)
    df = df.sort_values(
        ['posicion_focal', 'n_kept_comp', 'n_kept_rival1', 'n_kept_rival2', 'mano']
    ).reset_index(drop=True)

    # Guardar tabla completa
    df.to_csv(ARCHIVO_SALIDA, index=False)
    print(f"\nTabla completa guardada: {ARCHIVO_SALIDA}")
    print(f"  Filas: {len(df):,}  |  Columnas: {list(df.columns)}")

    # ── Tabla resumen por posicion + config ──────────────────────────────────
    resumen = df.groupby(
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
    print(f"  Filas resumen: {len(resumen):,}  (4 posiciones × 64 configs)")

    # ── Estadísticas rápidas ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RESUMEN: P(VICTORIA) SEGÚN CARTAS GUARDADAS (promedio sobre manos)")
    print("=" * 70)

    for pos in [1, 2, 3, 4]:
        sub = df[df['posicion_focal'] == pos]
        print(f"\n--- Posición {pos} ---")
        rival_g = sub.groupby(['n_kept_rival1', 'n_kept_rival2'])[
            ['prob_grande', 'prob_chica', 'prob_pares', 'prob_juego']
        ].mean().round(3)
        comp_g = sub.groupby('n_kept_comp')[
            ['prob_grande', 'prob_chica', 'prob_pares', 'prob_juego']
        ].mean().round(3)
        print(" Efecto compañero (por n_kept_comp):")
        print(comp_g.to_string())

    print()
    print("Archivos generados:")
    print(f"  {ARCHIVO_SALIDA.name}  ({len(df):,} filas)")
    print(f"  {ARCHIVO_RESUMEN.name}  ({len(resumen):,} filas)")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
