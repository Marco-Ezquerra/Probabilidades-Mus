"""
Generador de Políticas Óptimas de Descarte mediante Rollout (Q-Learning).

Este script implementa un sistema de Q-Learning donde:
1. Genera universos válidos (los 4 dan Mus en Fase 1)
2. Para cada universo, evalúa las 15 máscaras de descarte del Jugador 1
3. Simula el resto de la ronda (rollout) con cada máscara
4. Calcula el diferencial de puntos (Equipo A - Equipo B)
5. Acumula rewards en una Q-Table: Q(mano, posicion, mascara) = reward promedio
6. Exporta las políticas óptimas a CSV

El resultado es una tabla que indica, para cada (mano, posición), 
cuál es la mejor máscara de descarte según el diferencial de puntos esperado.
"""

import sys
from pathlib import Path
import random
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import multiprocessing
import os

# Añadir paths para imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from calculadoramus import inicializar_baraja
from motor_decision import MotorDecisionMus
from mascaras_descarte import generar_mascaras, aplicar_mascara, MASCARAS_DESCARTE
from descarte_heuristico import descarte_heuristico_base
from evaluador_ronda import evaluar_ronda_rapida
from params import (
    N_ITERACIONES_ROLLOUT,
    ARCHIVO_POLITICAS_FASE2,
    MODO_8_REYES,
    PRINT_PROGRESO_CADA,
    RANDOM_SEED,
    TASA_MUS_OBJETIVO,
    FACTOR_K_POS
)

# Máscaras precalculadas a nivel de módulo
_MASCARAS = MASCARAS_DESCARTE  # 15 máscaras precalculadas
_N_MASCARAS = len(_MASCARAS)


class QTableDescarte:
    """
    Tabla Q para almacenar rewards de (mano, posicion, mascara).
    Incluye tracking de información de descartes por jugador.
    """
    
    def __init__(self):
        # Estructura: {(mano_tuple, posicion, mascara_idx): [total_reward, n_visitas, info_descartes]}
        # info_descartes: {pos: total_cartas_descartadas} acumuladas en todas las visitas
        self.q_table = defaultdict(lambda: [0.0, 0, {1: 0, 2: 0, 3: 0, 4: 0}])
        self.mascaras = _MASCARAS
    
    def actualizar(self, mano, posicion, mascara_idx, reward, info_descartes=None):
        """
        Actualiza la Q-Table con un nuevo reward y opcionalmente info de descartes.
        
        Args:
            mano: Lista de 4 cartas
            posicion: Posición del jugador (1-4)
            mascara_idx: Índice de la máscara (0-14)
            reward: Reward obtenido (diferencial de puntos)
            info_descartes: Dict {pos: n_cartas_descartadas} para las 4 posiciones (opcional)
        """
        key = (tuple(sorted(mano)), posicion, mascara_idx)
        entry = self.q_table[key]
        entry[0] += reward
        entry[1] += 1
        
        # Actualizar info de descartes si se proporciona
        if info_descartes is not None:
            for pos, n_cartas in info_descartes.items():
                entry[2][pos] += n_cartas
    
    def obtener_promedio(self, mano, posicion, mascara_idx):
        """
        Obtiene el reward promedio para una entrada.
        
        Returns:
            float: Reward promedio (0.0 si no hay visitas)
        """
        key = (tuple(sorted(mano)), posicion, mascara_idx)
        entry = self.q_table[key]
        if entry[1] == 0:
            return 0.0
        return entry[0] / entry[1]
    
    def exportar_csv(self, filepath):
        """
        Exporta la Q-Table a CSV.
        
        Columnas: mano, posicion, mascara_idx, reward_promedio, n_visitas,
                  n_descarte_j1, n_descarte_j2, n_descarte_j3, n_descarte_j4
        """
        rows = []
        for (mano_tuple, posicion, mascara_idx), data in self.q_table.items():
            if data[1] > 0:  # Solo exportar entradas visitadas
                reward_promedio = data[0] / data[1]
                n_visitas = data[1]
                info_descartes = data[2]
                
                # Calcular promedios de descartes por jugador
                n_desc_j1 = info_descartes[1] / n_visitas
                n_desc_j2 = info_descartes[2] / n_visitas
                n_desc_j3 = info_descartes[3] / n_visitas
                n_desc_j4 = info_descartes[4] / n_visitas
                
                rows.append({
                    "mano": str(list(mano_tuple)),
                    "posicion": posicion,
                    "mascara_idx": mascara_idx,
                    "reward_promedio": reward_promedio,
                    "n_visitas": n_visitas,
                    "n_descarte_j1": n_desc_j1,
                    "n_descarte_j2": n_desc_j2,
                    "n_descarte_j3": n_desc_j3,
                    "n_descarte_j4": n_desc_j4
                })
        
        df = pd.DataFrame(rows)
        df = df.sort_values(["mano", "posicion", "reward_promedio"], ascending=[True, True, False])
        df.to_csv(filepath, index=False)
        
        return len(rows)
    
    def obtener_mejor_mascara(self, mano, posicion):
        """
        Obtiene la máscara con mejor reward promedio.
        
        Returns:
            int: Índice de la mejor máscara (0-14)
        """
        mejor_idx = 0
        mejor_reward = float('-inf')
        
        for mascara_idx in range(_N_MASCARAS):
            reward = self.obtener_promedio(mano, posicion, mascara_idx)
            if reward > mejor_reward:
                mejor_reward = reward
                mejor_idx = mascara_idx
        
        return mejor_idx
    
    def merge(self, other):
        """
        Fusiona otra QTable en esta (para combinar resultados de workers).
        """
        for key, data in other.q_table.items():
            entry = self.q_table[key]
            entry[0] += data[0]
            entry[1] += data[1]


def repartir_manos_iniciales(baraja):
    """
    Reparte 4 manos de 4 cartas cada una.
    
    Args:
        baraja: Lista con las 40 cartas
    
    Returns:
        tuple: (manos_dict, mazo_restante)
            - manos_dict: {1: mano1, 2: mano2, 3: mano3, 4: mano4}
            - mazo_restante: Lista con las 24 cartas restantes
    """
    baraja_temp = baraja.copy()
    random.shuffle(baraja_temp)
    
    manos = {}
    for pos in [1, 2, 3, 4]:
        mano = baraja_temp[:4]
        manos[pos] = sorted(mano, reverse=True)
        baraja_temp = baraja_temp[4:]
    
    return manos, baraja_temp


def _completar_mano_rapida(mano_parcial, mazo_shuffled, offset):
    """
    Completa una mano parcial usando un mazo ya barajado.
    Más rápido que random.sample + list.remove.
    
    Args:
        mano_parcial: Lista con cartas restantes tras descarte
        mazo_shuffled: Mazo ya barajado (no se modifica)
        offset: Posición desde donde tomar cartas del mazo
    
    Returns:
        tuple: (mano_completa_sorted, nuevo_offset)
    """
    n = 4 - len(mano_parcial)
    mano_completa = mano_parcial + mazo_shuffled[offset:offset + n]
    mano_completa.sort(reverse=True)
    return mano_completa, offset + n


def simular_rollout_mascara_rapida(mano_objetivo, posicion_objetivo, mascara_idx,
                                    mazo_restante, otros_manos_rest):
    """
    Versión optimizada de simular_rollout_mascara.
    Recibe los restos de mano de los otros jugadores ya precomputados.
    
    Args:
        mano_objetivo: Mano original del jugador objetivo
        posicion_objetivo: Posición del jugador objetivo (1-4)
        mascara_idx: Índice de la máscara a evaluar (0-14)
        mazo_restante: Lista con las 24 cartas disponibles
        otros_manos_rest: Dict {pos: mano_rest} con las cartas que quedan tras descarte heurístico
    
    Returns:
        tuple: (diferencial, info_descartes)
            - diferencial: float, diferencial de puntos desde perspectiva del jugador objetivo
            - info_descartes: dict {pos: n_cartas_descartadas} para las 4 posiciones
    """
    mascara = _MASCARAS[mascara_idx]
    
    # Inicializar info de descartes
    info_descartes = {1: 0, 2: 0, 3: 0, 4: 0}
    
    # Barajar mazo una vez y usar offset para repartir
    mazo_shuffled = mazo_restante.copy()
    random.shuffle(mazo_shuffled)
    offset = 0
    
    # Jugador objetivo descarta según la máscara y roba
    mano_restante = [mano_objetivo[i] for i in range(4) if i not in mascara]
    n_descartadas_obj = len(mascara)
    info_descartes[posicion_objetivo] = n_descartadas_obj
    
    mano_final, offset = _completar_mano_rapida(mano_restante, mazo_shuffled, offset)
    manos_finales = {posicion_objetivo: mano_final}
    
    # Los otros 3 jugadores: ya tenemos sus cartas restantes, solo robar
    for pos, mano_rest in otros_manos_rest.items():
        n_descartadas = 4 - len(mano_rest)
        info_descartes[pos] = n_descartadas
        
        mano_fin, offset = _completar_mano_rapida(list(mano_rest), mazo_shuffled, offset)
        manos_finales[pos] = mano_fin
    
    # Evaluar ronda con versión rápida (solo retorna diferencial)
    diferencial = evaluar_ronda_rapida(manos_finales)
    
    # Retornar diferencial desde perspectiva del jugador objetivo
    if posicion_objetivo in (1, 3):
        return diferencial, info_descartes
    else:
        return -diferencial, info_descartes


def _worker_rollout(args):
    """
    Worker para multiprocessing. Ejecuta un chunk de iteraciones.
    
    Args:
        args: tuple (worker_id, n_iteraciones, modo_8_reyes, seed)
    
    Returns:
        dict con q_table_data, contadores
    """
    worker_id, n_iteraciones, modo_8_reyes, seed = args
    
    # Cada worker tiene su propia semilla para evitar duplicados
    if seed is not None:
        random.seed(seed + worker_id)
    else:
        random.seed(os.getpid() + worker_id * 1000)
    
    baraja = inicializar_baraja(modo_8_reyes)
    motor = MotorDecisionMus(modo_8_reyes=modo_8_reyes, silent=True)
    q_table = QTableDescarte()
    
    universos_validos = 0
    universos_descartados = 0
    cortes_por_posicion = {1: 0, 2: 0, 3: 0, 4: 0}
    mus_por_posicion = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for iteracion in range(n_iteraciones):
        manos_iniciales, mazo_restante = repartir_manos_iniciales(baraja)
        
        todos_dan_mus = True
        for pos in (1, 2, 3, 4):
            decision, P_cortar, EV_total, desglose = motor.decidir(manos_iniciales[pos], pos)
            mus_por_posicion[pos] += 1
            if decision:
                todos_dan_mus = False
                cortes_por_posicion[pos] += 1
                break
        
        if not todos_dan_mus:
            universos_descartados += 1
            continue
        
        universos_validos += 1
        
        for posicion_objetivo in (1, 2, 3, 4):
            mano_obj = manos_iniciales[posicion_objetivo]
            
            # Precomputar descarte heurístico de los otros 3 jugadores (se reutiliza 15 veces)
            otros_manos_rest = {}
            for pos in (1, 2, 3, 4):
                if pos == posicion_objetivo:
                    continue
                mascara_h = descarte_heuristico_base(manos_iniciales[pos], pos)
                otros_manos_rest[pos] = [manos_iniciales[pos][i] for i in range(4) if i not in mascara_h]
            
            for mascara_idx in range(_N_MASCARAS):
                reward, info_descartes = simular_rollout_mascara_rapida(
                    mano_obj, posicion_objetivo, mascara_idx,
                    mazo_restante, otros_manos_rest
                )
                q_table.actualizar(mano_obj, posicion_objetivo, mascara_idx, reward, info_descartes)
        
        # Progreso periódico por worker (cada 30k iteraciones)
        if (iteracion + 1) % 30000 == 0:
            tasa = 100 * universos_validos / (iteracion + 1)
            print(f"  [Worker {worker_id}] {iteracion + 1:,}/{n_iteraciones:,} - {universos_validos:,} válidos ({tasa:.1f}%)", flush=True)
    
    # Convertir q_table a dict regular para pickle
    q_data = dict(q_table.q_table)
    
    return {
        'q_data': q_data,
        'universos_validos': universos_validos,
        'universos_descartados': universos_descartados,
        'cortes_por_posicion': cortes_por_posicion,
        'mus_por_posicion': mus_por_posicion,
        'n_iteraciones': n_iteraciones,
    }


def generar_politicas_rollout(n_iteraciones=None, modo_8_reyes=True, silent=False):
    """
    Genera políticas óptimas de descarte mediante rollouts.
    Usa multiprocessing para aprovechar varios cores.
    
    Args:
        n_iteraciones: Número de iteraciones (default: N_ITERACIONES_ROLLOUT)
        modo_8_reyes: Usar baraja de 8 reyes (default: True)
        silent: Modo silencioso sin prints (default: False)
    
    Returns:
        QTableDescarte: Tabla Q con los rewards acumulados
    """
    if n_iteraciones is None:
        n_iteraciones = N_ITERACIONES_ROLLOUT
    
    n_workers = min(multiprocessing.cpu_count(), 4)  # max 4 workers
    
    if not silent:
        print("=" * 70)
        print("GENERADOR DE POLÍTICAS ÓPTIMAS - FASE 2 (ROLLOUT)")
        print("=" * 70)
        print(f"Iteraciones: {n_iteraciones:,}")
        print(f"Modo: {'8 Reyes' if modo_8_reyes else '4 Reyes'}")
        print(f"Máscaras por iteración: {_N_MASCARAS} × 4 posiciones = {_N_MASCARAS * 4}")
        print(f"Workers: {n_workers}")
        print("=" * 70)
    
    # Dividir iteraciones entre workers
    iters_per_worker = n_iteraciones // n_workers
    remainder = n_iteraciones % n_workers
    
    worker_args = []
    for w in range(n_workers):
        iters_w = iters_per_worker + (1 if w < remainder else 0)
        worker_args.append((w, iters_w, modo_8_reyes, RANDOM_SEED))
    
    if n_workers > 1:
        if not silent:
            print(f"\nLanzando {n_workers} workers en paralelo...")
        with multiprocessing.Pool(n_workers) as pool:
            results = pool.map(_worker_rollout, worker_args)
    else:
        # Single-process fallback
        results = [_worker_rollout(worker_args[0])]
    
    # Fusionar resultados
    q_table = QTableDescarte()
    total_validos = 0
    total_descartados = 0
    total_cortes = {1: 0, 2: 0, 3: 0, 4: 0}
    total_mus = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for result in results:
        for key, data in result['q_data'].items():
            entry = q_table.q_table[key]
            entry[0] += data[0]
            entry[1] += data[1]
        total_validos += result['universos_validos']
        total_descartados += result['universos_descartados']
        for pos in (1, 2, 3, 4):
            total_cortes[pos] += result['cortes_por_posicion'][pos]
            total_mus[pos] += result['mus_por_posicion'][pos]
    
    if not silent:
        print("\n" + "=" * 70)
        print("ESTADÍSTICAS FINALES")
        print("=" * 70)
        print(f"Iteraciones totales: {n_iteraciones:,}")
        print(f"Universos válidos (todos Mus): {total_validos:,}")
        print(f"Universos descartados (alguien corta): {total_descartados:,}")
        print(f"Tasa de Mus: {100 * total_validos / n_iteraciones:.2f}% (objetivo: {TASA_MUS_OBJETIVO:.0%})")
        print(f"Entradas en Q-Table: {len(q_table.q_table):,}")
        
        print("\n  🎯 Estadísticas por posición:")
        print(f"  {'Pos':>3s} {'Equipo':>6s} {'Decisiones':>10s} {'Cortes':>7s} {'% Corte':>8s} {'Factor K':>9s}")
        for pos in [1, 2, 3, 4]:
            n_decisiones = total_mus[pos]
            n_cortes = total_cortes[pos]
            pct_corte = 100 * n_cortes / n_decisiones if n_decisiones > 0 else 0
            equipo = "A" if pos in [1, 3] else "B"
            factor_k = FACTOR_K_POS.get(pos, 1.0)
            print(f"  {pos:>3d} {equipo:>6s} {n_decisiones:>10,d} {n_cortes:>7,d} {pct_corte:>7.1f}% {factor_k:>9.2f}")
    
    return q_table


def main():
    """Función principal."""
    # Generar políticas
    q_table = generar_politicas_rollout(
        n_iteraciones=N_ITERACIONES_ROLLOUT,
        modo_8_reyes=MODO_8_REYES,
        silent=False
    )
    
    # Exportar a CSV
    output_path = Path(__file__).parent / ARCHIVO_POLITICAS_FASE2
    n_entradas = q_table.exportar_csv(output_path)
    
    print("\n" + "=" * 70)
    print("EXPORTACIÓN COMPLETADA")
    print("=" * 70)
    print(f"Archivo: {output_path}")
    print(f"Entradas exportadas: {n_entradas:,}")
    
    # Análisis rápido
    df = pd.read_csv(output_path)
    
    print("\n📊 ANÁLISIS DE POLÍTICAS:")
    print(f"  - Manos únicas: {df['mano'].nunique()}")
    print(f"  - Posiciones: {sorted(df['posicion'].unique())}")
    print(f"  - Máscaras únicas: {sorted(df['mascara_idx'].unique())}")
    
    print("\n🎯 TOP 10 MEJORES RECOMPENSAS:")
    print(df.nlargest(10, "reward_promedio")[["mano", "posicion", "mascara_idx", "reward_promedio", "n_visitas"]].to_string(index=False))
    
    print("\n⚠️ TOP 10 PEORES RECOMPENSAS:")
    print(df.nsmallest(10, "reward_promedio")[["mano", "posicion", "mascara_idx", "reward_promedio", "n_visitas"]].to_string(index=False))
    
    print("\n✓ Generación de políticas completada exitosamente")


if __name__ == "__main__":
    main()
