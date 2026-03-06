"""
Simulador de Fase 2 con Políticas Óptimas de Descarte.

Usa las políticas óptimas generadas por generar_politicas_rollout.py
para simular partidas completas y calcular probabilidades de victoria
en cada lance tras aplicar descartes óptimos.

Diferencia con Fase 1:
- Fase 1: Probabilidades con manos iniciales (sin descarte)
- Fase 2: Probabilidades con manos finales (tras descarte óptimo)

Output: CSV con probabilidades de victoria por lance para cada mano final
"""

import sys
from pathlib import Path
import random
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import numpy as np
import ast

# Añadir paths para imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from calculadoramus import inicializar_baraja
from motor_decision import MotorDecisionMus
from mascaras_descarte import generar_mascaras, aplicar_mascara, completar_mano
from evaluador_ronda import evaluar_grande, evaluar_chica, evaluar_pares, evaluar_juego
from params import (
    N_ITERACIONES_SIMULADOR_FASE2,
    ARCHIVO_POLITICAS_FASE2,
    ARCHIVO_PROBABILIDADES_FASE2,
    MODO_8_REYES,
    PRINT_PROGRESO_CADA,
    RANDOM_SEED,
    TAU,
    TAU_ADAPTATIVO,
    TAU_MIN,
    TAU_MAX,
    UMBRAL_DIFERENCIA_ALTO,
    UMBRAL_DIFERENCIA_BAJO,
    obtener_equipo
)


def calcular_tau_adaptativo(rewards):
    """
    Calcula la temperatura adaptativa basada en la diferencia entre
    el mejor y el segundo mejor reward.
    
    - Diferencia alta → TAU bajo (explotar, decisión clara)
    - Diferencia baja → TAU alto (explorar, opciones similares)
    
    Interpola linealmente entre TAU_MIN y TAU_MAX según la diferencia.
    
    Args:
        rewards: np.array con los rewards de las máscaras disponibles
    
    Returns:
        float: Temperatura adaptativa calculada
    """
    if len(rewards) <= 1:
        return TAU_MIN  # Solo una opción, usar explotación máxima
    
    # Ordenar descendente y obtener diferencia top-1 vs top-2
    sorted_rewards = np.sort(rewards)[::-1]
    diferencia = sorted_rewards[0] - sorted_rewards[1]
    
    # Interpolar linealmente
    if diferencia >= UMBRAL_DIFERENCIA_ALTO:
        return TAU_MIN  # Decisión clara → explotar
    elif diferencia <= UMBRAL_DIFERENCIA_BAJO:
        return TAU_MAX  # Opciones similares → explorar
    else:
        # Interpolación lineal entre TAU_MAX y TAU_MIN
        t = (diferencia - UMBRAL_DIFERENCIA_BAJO) / (UMBRAL_DIFERENCIA_ALTO - UMBRAL_DIFERENCIA_BAJO)
        return TAU_MAX - t * (TAU_MAX - TAU_MIN)


class PoliticasDescarte:
    """
    Gestor de políticas óptimas de descarte.
    """
    
    def __init__(self, filepath):
        """
        Carga políticas desde CSV.
        
        Args:
            filepath: Ruta al CSV con políticas
        """
        self.df = pd.read_csv(filepath)
        self.mascaras = generar_mascaras()
        
        # Convertir columna 'mano' de string a lista
        self.df['mano'] = self.df['mano'].apply(ast.literal_eval)
        
        # Crear índice para búsqueda rápida
        self._crear_indice()
    
    def _crear_indice(self):
        """Crea índice para búsqueda rápida."""
        self.indice = {}
        for _, row in self.df.iterrows():
            mano_tuple = tuple(sorted(row['mano']))
            posicion = row['posicion']
            mascara_idx = row['mascara_idx']
            reward = row['reward_promedio']
            
            key = (mano_tuple, posicion)
            if key not in self.indice:
                self.indice[key] = []
            self.indice[key].append((mascara_idx, reward))
    
    def obtener_mejor_mascara(self, mano, posicion):
        """
        Obtiene la mejor máscara para una (mano, posicion).
        
        Args:
            mano: Lista de 4 cartas
            posicion: Posición del jugador (1-4)
        
        Returns:
            int: Índice de la mejor máscara (0-14)
        """
        key = (tuple(sorted(mano)), posicion)
        if key not in self.indice:
            # Si no hay datos, usar máscara aleatoria
            return random.randint(0, 14)
        
        mascaras_rewards = self.indice[key]
        # Ordenar por reward descendente y tomar la mejor
        mascaras_rewards.sort(key=lambda x: x[1], reverse=True)
        return mascaras_rewards[0][0]
    
    def obtener_mascara_softmax(self, mano, posicion, tau=None):
        """
        Elige una máscara usando softmax sobre los rewards.
        
        Soporta temperatura adaptativa: si TAU_ADAPTATIVO está activado,
        calcula tau dinámicamente basándose en la diferencia entre
        el mejor y segundo mejor reward.
        
        Args:
            mano: Lista de 4 cartas
            posicion: Posición del jugador (1-4)
            tau: Temperatura para softmax (None = usar configuración global)
        
        Returns:
            int: Índice de la máscara elegida (0-14)
        """
        key = (tuple(sorted(mano)), posicion)
        if key not in self.indice:
            # Si no hay datos, usar máscara aleatoria
            return random.randint(0, 14)
        
        mascaras_rewards = self.indice[key]
        
        # Si solo hay una máscara, retornarla
        if len(mascaras_rewards) == 1:
            return mascaras_rewards[0][0]
        
        # Extraer índices y rewards
        indices = [mr[0] for mr in mascaras_rewards]
        rewards = np.array([mr[1] for mr in mascaras_rewards])
        
        # Determinar tau a usar
        if tau is not None:
            tau_efectivo = tau  # Parámetro explícito tiene prioridad
        elif TAU_ADAPTATIVO:
            tau_efectivo = calcular_tau_adaptativo(rewards)
        else:
            tau_efectivo = TAU  # Temperatura fija global
        
        # Softmax con temperatura
        # P(mascara) ∝ exp(reward / tau)
        exp_rewards = np.exp(rewards / tau_efectivo)
        probabilidades = exp_rewards / exp_rewards.sum()
        
        # Elegir según probabilidades
        mascara_idx = np.random.choice(indices, p=probabilidades)
        return mascara_idx


def repartir_manos_iniciales(baraja):
    """
    Reparte 4 manos de 4 cartas cada una.
    
    Returns:
        tuple: (manos_dict, mazo_restante)
    """
    baraja_temp = baraja.copy()
    random.shuffle(baraja_temp)
    
    manos = {}
    for pos in [1, 2, 3, 4]:
        mano = baraja_temp[:4]
        manos[pos] = sorted(mano, reverse=True)
        baraja_temp = baraja_temp[4:]
    
    return manos, baraja_temp


def simular_ronda_con_politicas(politicas, motor, baraja):
    """
    Simula una ronda completa usando políticas óptimas.
    
    Returns:
        dict or None: {
            "manos_finales": {pos: mano},
            "info_descartes": {pos: n_cartas_descartadas},
            "ganadores": {
                "grande": pos,
                "chica": pos,
                "pares": (pos, tipo, val1, val2),
                "juego": (pos, es_juego, valor)
            }
        }
        Retorna None si alguien corta en Fase 1
    """
    # 1. Repartir manos iniciales
    manos_iniciales, mazo_restante = repartir_manos_iniciales(baraja)
    
    # 2. Fase 1: ¿Todos dan Mus?
    for pos in [1, 2, 3, 4]:
        decision, P_cortar, EV_total, desglose = motor.decidir(manos_iniciales[pos], pos)
        if decision:  # decision es True si corta
            return None  # Alguien cortó
    
    # 3. Fase 2: Descartar según políticas (con softmax)
    manos_finales = {}
    info_descartes = {1: 0, 2: 0, 3: 0, 4: 0}
    mazo_temp = mazo_restante.copy()
    
    for pos in [1, 2, 3, 4]:
        # Elegir máscara con softmax (usa temperatura adaptativa si configurado)
        mascara_idx = politicas.obtener_mascara_softmax(manos_iniciales[pos], pos)
        mascara = politicas.mascaras[mascara_idx]
        
        # Registrar cuántas cartas se descartan
        info_descartes[pos] = len(mascara)
        
        # Aplicar descarte
        mano_restante, _ = aplicar_mascara(manos_iniciales[pos], mascara)
        mano_final = completar_mano(mano_restante, mazo_temp)
        manos_finales[pos] = mano_final
    
    # 4. Evaluar lances
    ganador_grande = evaluar_grande(manos_finales)
    ganador_chica = evaluar_chica(manos_finales)
    resultado_pares = evaluar_pares(manos_finales)
    resultado_juego = evaluar_juego(manos_finales)
    
    ganadores = {
        "grande": ganador_grande,
        "chica": ganador_chica,
        "pares": resultado_pares,
        "juego": resultado_juego
    }
    
    return {
        "manos_finales": manos_finales,
        "info_descartes": info_descartes,
        "ganadores": ganadores
    }


def simular_fase2(n_iteraciones=None, modo_8_reyes=True, filepath_politicas=None, silent=False):
    """
    Simulador principal de Fase 2.
    
    Args:
        n_iteraciones: Número de iteraciones (default: N_ITERACIONES_SIMULADOR_FASE2)
        modo_8_reyes: Usar baraja de 8 reyes (default: True)
        filepath_politicas: Ruta al CSV con políticas (default: ARCHIVO_POLITICAS_FASE2)
        silent: Modo silencioso (default: False)
    
    Returns:
        dict: Estadísticas de victorias por mano y lance
    """
    if n_iteraciones is None:
        n_iteraciones = N_ITERACIONES_SIMULADOR_FASE2
    
    if filepath_politicas is None:
        filepath_politicas = Path(__file__).parent / ARCHIVO_POLITICAS_FASE2
    
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
    
    # Inicializar
    baraja = inicializar_baraja(modo_8_reyes)
    motor = MotorDecisionMus(modo_8_reyes=modo_8_reyes, silent=True)
    politicas = PoliticasDescarte(filepath_politicas)
    
    if not silent:
        print("=" * 70)
        print("SIMULADOR DE FASE 2 - DESCARTE CON POLÍTICAS ÓPTIMAS")
        print("=" * 70)
        print(f"Iteraciones: {n_iteraciones:,}")
        print(f"Modo: {'8 Reyes' if modo_8_reyes else '4 Reyes'}")
        print(f"Temperatura Softmax: {'Adaptativa' if TAU_ADAPTATIVO else TAU}")
        if TAU_ADAPTATIVO:
            print(f"  TAU_MIN={TAU_MIN}, TAU_MAX={TAU_MAX}")
            print(f"  Umbral diferencia: [{UMBRAL_DIFERENCIA_BAJO}, {UMBRAL_DIFERENCIA_ALTO}]")
        print(f"Políticas: {filepath_politicas}")
        print("=" * 70)
    
    # Contadores
    victorias = defaultdict(lambda: {
        "grande": 0,
        "chica": 0,
        "pares": 0,
        "juego": 0,
        "total_apariciones": 0
    })
    
    # Tracking de descartes por posición
    descartes_por_posicion = {1: [], 2: [], 3: [], 4: []}
    
    rondas_validas = 0
    rondas_descartadas = 0
    
    # Simulación
    iterador = tqdm(range(n_iteraciones), desc="Simulando") if not silent else range(n_iteraciones)
    
    for iteracion in iterador:
        resultado = simular_ronda_con_politicas(politicas, motor, baraja)
        
        if resultado is None:
            rondas_descartadas += 1
            continue
        
        rondas_validas += 1
        
        # Registrar descartes
        info_descartes = resultado["info_descartes"]
        for pos, n_cartas in info_descartes.items():
            descartes_por_posicion[pos].append(n_cartas)
        
        # Registrar victorias por mano final
        manos_finales = resultado["manos_finales"]
        ganadores = resultado["ganadores"]
        
        for pos, mano_final in manos_finales.items():
            mano_key = tuple(sorted(mano_final))
            victorias[mano_key]["total_apariciones"] += 1
            
            # Grande
            if ganadores["grande"] == pos:
                victorias[mano_key]["grande"] += 1
            
            # Chica
            if ganadores["chica"] == pos:
                victorias[mano_key]["chica"] += 1
            
            # Pares
            pos_pares, tipo_pares, _, _ = ganadores["pares"]
            if pos_pares is not None:
                equipo_ganador = obtener_equipo(pos_pares)
                equipo_actual = obtener_equipo(pos)
                if equipo_ganador == equipo_actual:
                    victorias[mano_key]["pares"] += 1
            
            # Juego/Punto
            pos_juego, es_juego, _ = ganadores["juego"]
            equipo_ganador = obtener_equipo(pos_juego)
            equipo_actual = obtener_equipo(pos)
            if equipo_ganador == equipo_actual:
                victorias[mano_key]["juego"] += 1
        
        # Progreso periódico
        if not silent and (iteracion + 1) % PRINT_PROGRESO_CADA == 0:
            tasa_validos = 100 * rondas_validas / (iteracion + 1)
            tqdm.write(f"  Iteración {iteracion + 1:,}: {rondas_validas:,} rondas válidas ({tasa_validos:.1f}%)")
    
    if not silent:
        print("\n" + "=" * 70)
        print("ESTADÍSTICAS FINALES")
        print("=" * 70)
        print(f"Iteraciones totales: {n_iteraciones:,}")
        print(f"Rondas válidas (todos Mus): {rondas_validas:,}")
        print(f"Rondas descartadas (alguien corta): {rondas_descartadas:,}")
        print(f"Tasa de Mus: {100 * rondas_validas / n_iteraciones:.2f}%")
        print(f"Manos únicas observadas: {len(victorias):,}")
        
        # Estadísticas de descartes
        print("\n" + "=" * 70)
        print("🎴 ESTADÍSTICAS DE DESCARTES POR POSICIÓN")
        print("=" * 70)
        for pos in [1, 2, 3, 4]:
            descartes = descartes_por_posicion[pos]
            if len(descartes) > 0:
                promedio = np.mean(descartes)
                std = np.std(descartes)
                print(f"Posición {pos}: Promedio {promedio:.2f} ± {std:.2f} cartas")
                # Distribución
                distribucion = {i: descartes.count(i) for i in range(1, 5)}
                total = len(descartes)
                print(f"  Distribución: ", end="")
                for n_cartas in [1, 2, 3, 4]:
                    count = distribucion.get(n_cartas, 0)
                    pct = 100 * count / total if total > 0 else 0
                    print(f"{n_cartas}c: {pct:.1f}%  ", end="")
                print()  # Nueva línea
    
    return victorias


def exportar_probabilidades(victorias, filepath):
    """
    Exporta probabilidades a CSV.
    
    Args:
        victorias: Dict con estadísticas de victorias
        filepath: Ruta del archivo de salida
    
    Returns:
        int: Número de manos exportadas
    """
    rows = []
    for mano_tuple, stats in victorias.items():
        n = stats["total_apariciones"]
        if n >= 10:  # Mínimo de apariciones para considerar
            rows.append({
                "mano": str(list(mano_tuple)),
                "prob_grande": stats["grande"] / n,
                "prob_chica": stats["chica"] / n,
                "prob_pares": stats["pares"] / n,
                "prob_juego": stats["juego"] / n,
                "n_apariciones": n
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("mano")
    df.to_csv(filepath, index=False)
    
    return len(rows)


def main():
    """Función principal."""
    # Simular Fase 2
    victorias = simular_fase2(
        n_iteraciones=N_ITERACIONES_SIMULADOR_FASE2,
        modo_8_reyes=MODO_8_REYES,
        silent=False
    )
    
    # Exportar probabilidades
    output_path = Path(__file__).parent / ARCHIVO_PROBABILIDADES_FASE2
    n_manos = exportar_probabilidades(victorias, output_path)
    
    print("\n" + "=" * 70)
    print("EXPORTACIÓN COMPLETADA")
    print("=" * 70)
    print(f"Archivo: {output_path}")
    print(f"Manos exportadas: {n_manos:,}")
    
    # Análisis rápido
    df = pd.read_csv(output_path)
    
    print("\n📊 ESTADÍSTICAS GENERALES:")
    print(df[["prob_grande", "prob_chica", "prob_pares", "prob_juego"]].describe().to_string())
    
    print("\n🏆 TOP 10 MEJORES MANOS (Grande):")
    print(df.nlargest(10, "prob_grande")[["mano", "prob_grande", "prob_pares", "prob_juego", "n_apariciones"]].to_string(index=False))
    
    print("\n🎯 TOP 10 MEJORES MANOS (Juego):")
    print(df.nlargest(10, "prob_juego")[["mano", "prob_juego", "prob_grande", "prob_pares", "n_apariciones"]].to_string(index=False))
    
    print("\n✓ Simulación de Fase 2 completada exitosamente")


if __name__ == "__main__":
    main()
