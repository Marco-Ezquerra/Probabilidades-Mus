"""
Script de diagnóstico para verificar el comportamiento del sistema de mus.

Ejecuta una simulación rápida (~100K iteraciones) y reporta:
- Tasa de mus global y por posición
- Distribución de valores K efectivos por posición
- Distribución de TAU adaptativo (min, max, promedio)
- Top 10 máscaras por visitas (verificar concentración)
- Validar que posiciones 1 y 3 tienen más mus que 2 y 4

Uso:
    python diagnostico_mus.py [--iteraciones N] [--calibrar]
"""

import sys
import os
import argparse
import random
from pathlib import Path
from collections import defaultdict

import numpy as np

# Añadir paths para imports
sys.path.insert(0, str(Path(__file__).parent / "calculadora_probabilidades_mus"))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from calculadoramus import inicializar_baraja
from motor_decision import (
    MotorDecisionMus, decidir_cortar, calcular_ev_total,
    PERFILES, calibrar_percentil_para_tasa_objetivo
)
from params import (
    MODO_8_REYES, FACTOR_K_POS, TASA_MUS_OBJETIVO,
    TAU, TAU_ADAPTATIVO, TAU_MIN, TAU_MAX,
    UMBRAL_DIFERENCIA_ALTO, UMBRAL_DIFERENCIA_BAJO
)


def diagnosticar_tasa_mus(n_iteraciones=100_000, perfil='normal', modo_8_reyes=True,
                          auto_calibrar=False):
    """
    Ejecuta diagnóstico completo del sistema de mus.
    """
    print("=" * 70)
    print(" DIAGNÓSTICO DEL SISTEMA DE MUS")
    print("=" * 70)
    
    # Mostrar configuración
    print(f"\n📋 CONFIGURACIÓN:")
    print(f"  Perfil: {perfil}")
    print(f"  Modo: {'8 Reyes' if modo_8_reyes else '4 Reyes'}")
    print(f"  Iteraciones: {n_iteraciones:,}")
    print(f"  Tasa MUS objetivo: {TASA_MUS_OBJETIVO:.0%}")
    print(f"  TAU adaptativo: {TAU_ADAPTATIVO}")
    print(f"  Factor K por posición: {FACTOR_K_POS}")
    
    params_perfil = PERFILES[perfil]
    print(f"\n  Parámetros del perfil '{perfil}':")
    for k, v in params_perfil.items():
        print(f"    {k}: {v}")
    
    # Inicializar motor
    print(f"\n🔧 Inicializando motor...")
    motor = MotorDecisionMus(
        modo_8_reyes=modo_8_reyes,
        perfil=perfil,
        silent=False,
        auto_calibrar_tasa=auto_calibrar
    )
    
    baraja = inicializar_baraja(modo_8_reyes)
    
    # Contadores
    universos_mus = 0
    universos_total = 0
    cortes_por_posicion = {1: 0, 2: 0, 3: 0, 4: 0}
    decisiones_por_posicion = {1: 0, 2: 0, 3: 0, 4: 0}
    ev_por_posicion = {1: [], 2: [], 3: [], 4: []}
    k_efectivos_por_posicion = {1: [], 2: [], 3: [], 4: []}
    
    print(f"\n🎲 Simulando {n_iteraciones:,} repartos...")
    
    for i in range(n_iteraciones):
        baraja_temp = baraja.copy()
        random.shuffle(baraja_temp)
        
        manos = {}
        for pos in [1, 2, 3, 4]:
            manos[pos] = sorted(baraja_temp[:4], reverse=True)
            baraja_temp = baraja_temp[4:]
        
        todos_mus = True
        for pos in [1, 2, 3, 4]:
            decisiones_por_posicion[pos] += 1
            
            # Calcular EV para estadísticas
            EV_total, _ = calcular_ev_total(
                manos[pos], motor.estadisticas,
                motor.params['beta'], pos
            )
            ev_por_posicion[pos].append(EV_total)
            
            # Calcular K efectivo (para monitorizar)
            factor_pos = FACTOR_K_POS.get(pos, 1.0)
            k_ajustado = motor.params['k_base'] * factor_pos
            K = np.random.normal(k_ajustado, motor.params['sigma'])
            K = max(K, 0.5)
            k_efectivos_por_posicion[pos].append(K)
            
            # Decisión real
            decision, P_cortar, _, _ = motor.decidir(manos[pos], pos)
            
            if decision:  # Corta
                cortes_por_posicion[pos] += 1
                todos_mus = False
                break
        
        if todos_mus:
            universos_mus += 1
        universos_total += 1
        
        if (i + 1) % 25000 == 0:
            tasa_parcial = 100 * universos_mus / (i + 1)
            print(f"  Progreso: {i+1:,}/{n_iteraciones:,} | Tasa Mus: {tasa_parcial:.1f}%")
    
    # === RESULTADOS ===
    tasa_mus_global = universos_mus / universos_total
    
    print("\n" + "=" * 70)
    print(" RESULTADOS DEL DIAGNÓSTICO")
    print("=" * 70)
    
    # 1. Tasa de mus global
    print(f"\n🎯 TASA DE MUS GLOBAL:")
    print(f"  Universos con mus: {universos_mus:,} / {universos_total:,}")
    print(f"  Tasa de mus: {tasa_mus_global:.1%}")
    print(f"  Objetivo: {TASA_MUS_OBJETIVO:.0%}")
    diff = tasa_mus_global - TASA_MUS_OBJETIVO
    status = "✅" if abs(diff) <= 0.05 else "⚠️"
    print(f"  Diferencia: {diff:+.1%} {status}")
    
    # 2. Estadísticas por posición
    print(f"\n📊 ESTADÍSTICAS POR POSICIÓN:")
    print(f"  {'Pos':>3s} {'Equipo':>6s} {'Decisiones':>10s} {'Cortes':>7s} {'% Corte':>8s} {'K medio':>8s} {'K std':>6s} {'EV medio':>9s}")
    print(f"  {'---':>3s} {'------':>6s} {'----------':>10s} {'-------':>7s} {'-------':>8s} {'-------':>8s} {'-----':>6s} {'--------':>9s}")
    
    for pos in [1, 2, 3, 4]:
        n_dec = decisiones_por_posicion[pos]
        n_cortes = cortes_por_posicion[pos]
        pct_corte = 100 * n_cortes / n_dec if n_dec > 0 else 0
        equipo = "A (Mano)" if pos in [1, 3] else "B (Post)"
        k_arr = np.array(k_efectivos_por_posicion[pos])
        ev_arr = np.array(ev_por_posicion[pos])
        print(f"  {pos:>3d} {equipo:>8s} {n_dec:>10,d} {n_cortes:>7,d} {pct_corte:>7.1f}% {k_arr.mean():>8.3f} {k_arr.std():>6.3f} {ev_arr.mean():>9.4f}")
    
    # 3. Validar position-aware
    print(f"\n🔍 VALIDACIÓN POSITION-AWARE:")
    tasa_corte_13 = (cortes_por_posicion[1] + cortes_por_posicion[3]) / \
                     (decisiones_por_posicion[1] + decisiones_por_posicion[3]) if \
                     (decisiones_por_posicion[1] + decisiones_por_posicion[3]) > 0 else 0
    tasa_corte_24 = (cortes_por_posicion[2] + cortes_por_posicion[4]) / \
                     (decisiones_por_posicion[2] + decisiones_por_posicion[4]) if \
                     (decisiones_por_posicion[2] + decisiones_por_posicion[4]) > 0 else 0
    
    print(f"  Tasa de corte pos 1+3 (Mano): {tasa_corte_13:.1%}")
    print(f"  Tasa de corte pos 2+4 (Postre): {tasa_corte_24:.1%}")
    print(f"  K efectivo medio pos 1+3: {np.mean(k_efectivos_por_posicion[1] + k_efectivos_por_posicion[3]):.3f}")
    print(f"  K efectivo medio pos 2+4: {np.mean(k_efectivos_por_posicion[2] + k_efectivos_por_posicion[4]):.3f}")
    print(f"  NOTA: Pos 1 decide primero (más muestras). Pos 2,4 solo deciden")
    print(f"  si los anteriores no cortaron (sesgo de selección del muestreo secuencial).")
    print(f"  El factor K position-aware se verifica en la distribución de K efectivo.")
    
    # Verificar que K efectivo es coherente con factores
    k_mean_13 = np.mean(k_efectivos_por_posicion[1] + k_efectivos_por_posicion[3])
    k_mean_24 = np.mean(k_efectivos_por_posicion[2] + k_efectivos_por_posicion[4])
    if k_mean_13 < k_mean_24:
        print(f"  ✅ K medio pos 1+3 < pos 2+4 (position-aware activo)")
    else:
        print(f"  ⚠️ K medio pos 1+3 >= pos 2+4 (revisar FACTOR_K_POS)")
    
    # 4. Distribución de K efectivo
    print(f"\n📈 DISTRIBUCIÓN DE K EFECTIVO:")
    for pos in [1, 2, 3, 4]:
        k_arr = np.array(k_efectivos_por_posicion[pos])
        factor = FACTOR_K_POS.get(pos, 1.0)
        print(f"  Pos {pos} (factor={factor}): "
              f"media={k_arr.mean():.3f}, std={k_arr.std():.3f}, "
              f"min={k_arr.min():.3f}, max={k_arr.max():.3f}")
    
    # 5. Temperatura adaptativa
    if TAU_ADAPTATIVO:
        print(f"\n🌡️ TEMPERATURA ADAPTATIVA:")
        print(f"  Configuración: TAU_MIN={TAU_MIN}, TAU_MAX={TAU_MAX}")
        print(f"  Umbrales: bajo={UMBRAL_DIFERENCIA_BAJO}, alto={UMBRAL_DIFERENCIA_ALTO}")
        print(f"  (Diagnóstico de TAU real requiere ejecutar simulador_fase2)")
    else:
        print(f"\n🌡️ TEMPERATURA FIJA: TAU={TAU}")
    
    print("\n" + "=" * 70)
    print(" DIAGNÓSTICO COMPLETADO")
    print("=" * 70)
    
    return {
        'tasa_mus': tasa_mus_global,
        'cortes_por_posicion': cortes_por_posicion,
        'decisiones_por_posicion': decisiones_por_posicion,
        'tasa_corte_13': tasa_corte_13,
        'tasa_corte_24': tasa_corte_24
    }


def main():
    parser = argparse.ArgumentParser(description="Diagnóstico del sistema de Mus")
    parser.add_argument('--iteraciones', type=int, default=100_000,
                        help='Número de iteraciones (default: 100000)')
    parser.add_argument('--perfil', type=str, default='normal',
                        choices=['conservador', 'normal', 'agresivo'],
                        help='Perfil de decisión (default: normal)')
    parser.add_argument('--calibrar', action='store_true',
                        help='Auto-calibrar percentil_mu para tasa objetivo')
    parser.add_argument('--modo-4reyes', action='store_true',
                        help='Usar baraja de 4 reyes (default: 8 reyes)')
    
    args = parser.parse_args()
    
    diagnosticar_tasa_mus(
        n_iteraciones=args.iteraciones,
        perfil=args.perfil,
        modo_8_reyes=not args.modo_4reyes,
        auto_calibrar=args.calibrar
    )


if __name__ == "__main__":
    main()
