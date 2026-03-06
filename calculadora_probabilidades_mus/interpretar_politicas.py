#!/usr/bin/env python3
"""
Interpretador de Políticas Óptimas de Descarte
===============================================
Convierte politicas_optimas_fase2.csv en recomendaciones humanas legibles.
Muestra para cada mano y posición:
  - Qué cartas mantener (keep)
  - Qué cartas descartar (discard)
  - Reward esperado
  - Nivel de confianza (basado en n_visitas)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import pandas as pd
import numpy as np
from utils.mascaras_descarte import generar_mascaras
from params import TAU
import ast
from collections import defaultdict

# ==================== CONSTANTES ====================
MASCARAS = generar_mascaras()
N_TOP_RECOMMENDATIONS = 3  # Top N estrategias por mano

NOMBRES_POSICIONES = {
    1: "MANO (J1)",
    2: "POSTRE (J2)", 
    3: "MANO (J3)",
    4: "POSTRE (J4)"
}

CARTA_NOMBRES = {
    1: "As", 4: "4", 5: "5", 6: "6", 7: "7",
    10: "Sota", 11: "Caballo", 12: "Rey"
}

# ==================== FUNCIONES AUXILIARES ====================

def mano_str(mano):
    """Convierte [12, 12, 10, 1] → 'Rey-Rey-Sota-As'"""
    return "-".join([CARTA_NOMBRES.get(c, str(c)) for c in sorted(mano, reverse=True)])

def mascara_str(mano, mascara_idx):
    """
    Devuelve descripción de la acción de descarte.
    Ej: "Mantener [Rey,Rey,Sota], descartar [As]"
    """
    if mascara_idx >= len(MASCARAS):
        return "MÁSCARA INVÁLIDA"
    
    mascara = MASCARAS[mascara_idx]  # Tupla de índices a descartar, ej: (0, 2)
    
    # Aplicar máscara - máscara contiene índices de posiciones a DESCARTAR
    mano_sorted = sorted(mano, reverse=True)
    descartar = [mano_sorted[i] for i in mascara]
    mantener = [c for i, c in enumerate(mano_sorted) if i not in mascara]
    
    mantener_str = ",".join([CARTA_NOMBRES.get(c, str(c)) for c in mantener]) if mantener else "Nada"
    descartar_str = ",".join([CARTA_NOMBRES.get(c, str(c)) for c in descartar]) if descartar else "Nada"
    
    return f"Mantener [{mantener_str}] / Descartar [{descartar_str}]"

def nivel_confianza(n_visitas):
    """Clasifica confianza estadística de la recomendación"""
    if n_visitas >= 100:
        return "ALTA"
    elif n_visitas >= 30:
        return "MEDIA"
    elif n_visitas >= 10:
        return "BAJA"
    else:
        return "MUY BAJA"

def calcular_probabilidad_softmax(rewards, tau=TAU):
    """
    Calcula probabilidades softmax para cada máscara.
    Retorna array de probabilidades que suma 1.0
    """
    exp_rewards = np.exp(np.array(rewards) / tau)
    return exp_rewards / exp_rewards.sum()

# ==================== ANÁLISIS PRINCIPAL ====================

def cargar_politicas(csv_path):
    """Carga CSV y agrupa por (mano, posicion)"""
    df = pd.read_csv(csv_path)
    
    # Convertir string "[1,2,3,4]" a lista
    df['mano_list'] = df['mano'].apply(ast.literal_eval)
    
    return df

def analizar_mano_posicion(df_mano_pos, mano, posicion):
    """
    Analiza todas las máscaras probadas para una (mano, posición).
    Retorna recomendaciones ordenadas por reward.
    """
    # Ordenar por reward descendente
    df_sorted = df_mano_pos.sort_values('reward_promedio', ascending=False)
    
    recomendaciones = []
    for idx, row in df_sorted.head(N_TOP_RECOMMENDATIONS).iterrows():
        mascara_idx = row['mascara_idx']
        reward = row['reward_promedio']
        n_visitas = row['n_visitas']
        
        recomendaciones.append({
            'mascara_idx': mascara_idx,
            'accion': mascara_str(mano, mascara_idx),
            'reward': reward,
            'n_visitas': n_visitas,
            'confianza': nivel_confianza(n_visitas)
        })
    
    # Calcular distribución softmax sobre TODAS las máscaras
    all_rewards = df_sorted['reward_promedio'].values
    all_masks = df_sorted['mascara_idx'].values
    probs = calcular_probabilidad_softmax(all_rewards)
    
    # Añadir probabilidad de selección
    for i, rec in enumerate(recomendaciones):
        mask_idx = rec['mascara_idx']
        # Buscar probabilidad de esta máscara
        prob_idx = np.where(all_masks == mask_idx)[0][0]
        rec['prob_seleccion'] = probs[prob_idx] * 100
    
    return recomendaciones

def generar_reporte_completo(csv_path, output_txt="interpretacion_politicas.txt", output_csv="politicas_legibles.csv"):
    """
    Genera:
    1. Archivo TXT con reporte legible completo
    2. CSV con recomendaciones estructuradas
    """
    print("Cargando políticas...")
    df = cargar_politicas(csv_path)
    
    # Agrupar por (mano, posicion)
    grupos = df.groupby(['mano', 'posicion'])
    
    print(f"Total de (mano, posición) únicas: {len(grupos)}")
    
    # Preparar CSV de salida
    resultados = []
    
    # Abrir archivo TXT
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("INTERPRETACIÓN DE POLÍTICAS ÓPTIMAS DE DESCARTE - FASE 2\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total de combinaciones analizadas: {len(grupos)}\n")
        f.write(f"Temperatura softmax (τ): {TAU}\n")
        f.write(f"Top recomendaciones por mano: {N_TOP_RECOMMENDATIONS}\n\n")
        
        # Iterar por cada grupo
        for (mano_str_raw, posicion), df_grupo in grupos:
            mano = ast.literal_eval(mano_str_raw)
            mano_legible = mano_str(mano)
            pos_nombre = NOMBRES_POSICIONES.get(posicion, f"Pos {posicion}")
            
            # Estadísticas del grupo
            n_mascaras_probadas = len(df_grupo)
            n_total_visitas = df_grupo['n_visitas'].sum()
            
            f.write("-" * 80 + "\n")
            f.write(f"MANO: {mano_legible} ({mano})\n")
            f.write(f"POSICIÓN: {pos_nombre}\n")
            f.write(f"Máscaras probadas: {n_mascaras_probadas}/15\n")
            f.write(f"Total visitas: {n_total_visitas}\n")
            f.write("-" * 80 + "\n\n")
            
            # Analizar
            recomendaciones = analizar_mano_posicion(df_grupo, mano, posicion)
            
            # Escribir recomendaciones
            for i, rec in enumerate(recomendaciones, 1):
                f.write(f"  #{i} RECOMENDACIÓN (Prob. selección: {rec['prob_seleccion']:.1f}%)\n")
                f.write(f"      Acción: {rec['accion']}\n")
                f.write(f"      Reward promedio: {rec['reward']:+.2f} puntos\n")
                f.write(f"      Visitas: {rec['n_visitas']} ({rec['confianza']})\n\n")
                
                # Guardar para CSV
                resultados.append({
                    'mano': mano_str_raw,
                    'mano_legible': mano_legible,
                    'posicion': posicion,
                    'posicion_nombre': pos_nombre,
                    'rank': i,
                    'mascara_idx': rec['mascara_idx'],
                    'accion': rec['accion'],
                    'reward_promedio': rec['reward'],
                    'n_visitas': rec['n_visitas'],
                    'confianza': rec['confianza'],
                    'prob_seleccion_pct': rec['prob_seleccion']
                })
            
            f.write("\n")
    
    print(f"✓ Reporte TXT generado: {output_txt}")
    
    # Guardar CSV
    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_csv(output_csv, index=False)
    print(f"✓ CSV estructurado generado: {output_csv}")
    
    return df_resultado

def analisis_estadistico_confianza(df):
    """Analiza confianza estadística global de las políticas"""
    print("\n" + "=" * 60)
    print("ANÁLISIS DE CONFIANZA ESTADÍSTICA")
    print("=" * 60)
    
    # Total de visitas por estado (mano, posicion)
    estados_unicos = df.groupby(['mano', 'posicion']).agg({
        'n_visitas': 'sum'
    }).reset_index()
    
    print(f"\nEstados únicos (mano, posición): {len(estados_unicos)}")
    print(f"Visitas promedio por estado: {estados_unicos['n_visitas'].mean():.1f}")
    print(f"Visitas mediana por estado: {estados_unicos['n_visitas'].median():.0f}")
    print(f"Visitas mínimas: {estados_unicos['n_visitas'].min()}")
    print(f"Visitas máximas: {estados_unicos['n_visitas'].max()}")
    
    # Distribución de confianza
    total_rows = len(df)
    confianza_dist = df['confianza'].value_counts().sort_index()
    
    print(f"\nDistribución de confianza (sobre {total_rows} entradas):")
    for nivel, count in confianza_dist.items():
        pct = count / total_rows * 100
        print(f"  {nivel:10s}: {count:5d} ({pct:5.1f}%)")
    
    # Análisis por posición
    print("\nPromedio de visitas por posición:")
    for pos in sorted(df['posicion'].unique()):
        df_pos = estados_unicos[estados_unicos['posicion'] == pos]
        avg_visitas = df_pos['n_visitas'].mean()
        n_estados = len(df_pos)
        print(f"  {NOMBRES_POSICIONES.get(pos, f'Pos {pos}'):15s}: {avg_visitas:6.1f} visitas/estado ({n_estados} estados)")
    
    # Recomendaciones
    estados_baja_confianza = (estados_unicos['n_visitas'] < 30).sum()
    pct_baja = estados_baja_confianza / len(estados_unicos) * 100
    
    print(f"\n⚠️  Estados con visitas < 30: {estados_baja_confianza}/{len(estados_unicos)} ({pct_baja:.1f}%)")
    
    if pct_baja > 20:
        print(f"\n🔴 ADVERTENCIA: {pct_baja:.0f}% de estados tienen confianza BAJA o inferior.")
        print("   Se recomienda aumentar N_ITERACIONES_ROLLOUT sustancialmente (≥1M).")
    elif pct_baja > 10:
        print(f"\n🟡 PRECAUCIÓN: {pct_baja:.0f}% de estados tienen confianza limitada.")
        print("   Considera aumentar N_ITERACIONES_ROLLOUT para mayor robustez.")
    else:
        print(f"\n🟢 Confianza estadística adecuada ({pct_baja:.0f}% estados con <30 visitas).")

def buscar_mano_especifica(df_resultado, mano_buscar):
    """Busca y muestra recomendaciones para una mano específica en todas las posiciones"""
    print("\n" + "=" * 60)
    print(f"BÚSQUEDA: {mano_str(mano_buscar)} ({mano_buscar})")
    print("=" * 60)
    
    mano_tuple_str = str(mano_buscar)
    df_mano = df_resultado[df_resultado['mano'] == mano_tuple_str]
    
    if df_mano.empty:
        print("⚠️  Mano no encontrada en las políticas generadas.")
        return
    
    for posicion in sorted(df_mano['posicion'].unique()):
        df_pos = df_mano[df_mano['posicion'] == posicion]
        print(f"\n{df_pos.iloc[0]['posicion_nombre']}:")
        for _, row in df_pos.iterrows():
            print(f"  #{row['rank']}: {row['accion']}")
            print(f"       Reward: {row['reward_promedio']:+.2f} | Prob: {row['prob_seleccion_pct']:.1f}% | Visitas: {row['n_visitas']} ({row['confianza']})")

# ==================== MAIN ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Interpretar políticas óptimas de descarte")
    parser.add_argument('--csv', default='politicas_optimas_fase2.csv', 
                       help='Archivo CSV de políticas (default: politicas_optimas_fase2.csv)')
    parser.add_argument('--buscar', type=str, 
                       help='Buscar mano específica, ej: "[12,12,10,1]" (opcional)')
    
    args = parser.parse_args()
    
    # Generar reportes
    df_resultado = generar_reporte_completo(
        args.csv,
        output_txt="interpretacion_politicas.txt",
        output_csv="politicas_legibles.csv"
    )
    
    # Análisis estadístico
    analisis_estadistico_confianza(df_resultado)
    
    # Búsqueda específica
    if args.buscar:
        try:
            mano_buscar = ast.literal_eval(args.buscar)
            buscar_mano_especifica(df_resultado, mano_buscar)
        except Exception as e:
            print(f"Error parseando mano: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Análisis completado")
    print("=" * 60)
    print(f"Archivos generados:")
    print(f"  - interpretacion_politicas.txt (reporte legible)")
    print(f"  - politicas_legibles.csv (datos estructurados)")
