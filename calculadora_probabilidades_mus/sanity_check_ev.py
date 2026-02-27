"""
Sanity Check - Verificación de Cordura del Modelo EV (Fase 1)

Objetivo:
    Verificar que el modelo matemático del motor de decisión tiene sentido
    antes de hacer simulaciones masivas. Calcular EV de todas las manos
    en cada posición y verificar que el ordenamiento es coherente.

Verificaciones:
    1. Ordenamiento: Manos con mejores jugadas tienen mayor EV
    2. Posición: Posición 1 siempre tiene EV >= otras posiciones (desempates)
    3. Coherencia: Diferencias entre posiciones proporcionales a P(empate)
    4. Correlación: EV entre posiciones debe estar altamente correlacionado

Salida:
    - sanity_check_ev_8reyes.csv: Todas las manos ordenadas por EV y posición
    - sanity_check_report.txt: Reporte detallado de verificaciones

Autor: Motor de Decisión Mus v2.3
Fecha: 26 febrero 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from motor_decision import MotorDecisionMus, EstadisticasEstaticas, analizar_mano
from typing import List, Dict, Tuple
import time


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

MODO_8_REYES = True  # Cambiar a False para 4 reyes
PERFIL = 'normal'    # conservador, normal, agresivo
POSICIONES = [1, 2, 3, 4]  # Todas las posiciones de la mesa


# ============================================================================
# FUNCIONES DE ANÁLISIS
# ============================================================================

def calcular_evs_todas_manos(motor: MotorDecisionMus, 
                              estadisticas: EstadisticasEstaticas,
                              posiciones: List[int]) -> pd.DataFrame:
    """
    Calcula el EV de todas las manos posibles en cada posición.
    
    Args:
        motor: MotorDecisionMus
        estadisticas: EstadisticasEstaticas
        posiciones: Lista de posiciones a evaluar [1, 2, 3, 4]
    
    Returns:
        DataFrame con columnas: mano, EV_pos1, EV_pos2, EV_pos3, EV_pos4, 
                                tiene_pares, tiene_juego, etc.
    """
    print("\n" + "="*80)
    print("CALCULANDO EV DE TODAS LAS MANOS EN CADA POSICIÓN")
    print("="*80)
    
    manos = list(estadisticas.manos_dict.keys())
    total_manos = len(manos)
    
    print(f"\nTotal de manos únicas: {total_manos}")
    print(f"Posiciones a evaluar: {posiciones}")
    print(f"Total de cálculos: {total_manos * len(posiciones)}")
    
    datos = []
    start_time = time.time()
    
    for idx, mano_tuple in enumerate(manos, 1):
        mano = list(mano_tuple)
        
        # Progreso
        if idx % 50 == 0 or idx == total_manos:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total_manos - idx) / rate if rate > 0 else 0
            print(f"Progreso: {idx}/{total_manos} ({idx/total_manos*100:.1f}%) "
                  f"- {rate:.1f} manos/s - ETA: {eta:.1f}s")
        
        # Obtener información básica de la mano
        probs = estadisticas.obtener_probabilidades(mano)
        analisis = analizar_mano(mano)
        
        # Calcular EV en cada posición
        row = {
            'mano': str(mano),
            'mano_str': f"[{','.join(map(str, mano))}]",
            'prob_grande': probs['prob_grande'],
            'prob_chica': probs['prob_chica'],
            'tiene_pares': analisis['tiene_pares'],
            'tiene_juego': analisis['tiene_juego'],
            'tipo_pares': analisis['tipo_pares'],
            'valor_juego': analisis['valor_juego_raw'],  # Clave correcta
            'valor_punto': analisis['valor_punto'],
            'W_pares': analisis['W_pares'],
            'W_juego': analisis['W_juego'],
            'W_punto': analisis['W_punto'],
        }
        
        for pos in posiciones:
            _, _, ev, _ = motor.decidir(mano, posicion=pos)
            row[f'EV_pos{pos}'] = ev
        
        datos.append(row)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Cálculos completados en {elapsed:.2f}s ({total_manos/elapsed:.1f} manos/s)")
    
    df = pd.DataFrame(datos)
    
    # Añadir diferencias entre posiciones
    df['diff_pos1_pos4'] = df['EV_pos1'] - df['EV_pos4']
    df['diff_pos1_pos2'] = df['EV_pos1'] - df['EV_pos2']
    
    return df


def verificar_coherencia(df: pd.DataFrame) -> Dict[str, any]:
    """
    Verifica la coherencia matemática del ordenamiento de manos.
    
    Args:
        df: DataFrame con EVs calculados
    
    Returns:
        Dict con resultados de verificaciones
    """
    print("\n" + "="*80)
    print("VERIFICACIÓN DE COHERENCIA MATEMÁTICA")
    print("="*80)
    
    resultados = {}
    
    # 1. Verificar que posición 1 siempre tiene EV >= otras posiciones
    print("\n1. Verificación: Posición 1 debe tener EV >= otras posiciones")
    print("   (debido a ventaja en desempates)")
    
    pos1_mayor_pos2 = (df['EV_pos1'] >= df['EV_pos2']).all()
    pos1_mayor_pos3 = (df['EV_pos1'] >= df['EV_pos3']).all()
    pos1_mayor_pos4 = (df['EV_pos1'] >= df['EV_pos4']).all()
    
    print(f"   EV_pos1 >= EV_pos2: {pos1_mayor_pos2} ({'✓' if pos1_mayor_pos2 else '✗'})")
    print(f"   EV_pos1 >= EV_pos3: {pos1_mayor_pos3} ({'✓' if pos1_mayor_pos3 else '✗'})")
    print(f"   EV_pos1 >= EV_pos4: {pos1_mayor_pos4} ({'✓' if pos1_mayor_pos4 else '✗'})")
    
    resultados['pos1_siempre_mayor'] = pos1_mayor_pos2 and pos1_mayor_pos3 and pos1_mayor_pos4
    
    # 2. Calcular correlación entre posiciones
    print("\n2. Correlación entre posiciones:")
    print("   (debe ser muy alta: ~0.99+)")
    
    # Calcular correlación de Pearson usando numpy
    def pearson_corr(x, y):
        """Calcula correlación de Pearson entre dos arrays."""
        x_arr = np.array(x)
        y_arr = np.array(y)
        mean_x = np.mean(x_arr)
        mean_y = np.mean(y_arr)
        num = np.sum((x_arr - mean_x) * (y_arr - mean_y))
        den = np.sqrt(np.sum((x_arr - mean_x)**2) * np.sum((y_arr - mean_y)**2))
        return num / den if den != 0 else 0.0
    
    corr_1_2 = pearson_corr(df['EV_pos1'], df['EV_pos2'])
    corr_1_3 = pearson_corr(df['EV_pos1'], df['EV_pos3'])
    corr_1_4 = pearson_corr(df['EV_pos1'], df['EV_pos4'])
    corr_2_4 = pearson_corr(df['EV_pos2'], df['EV_pos4'])
    
    print(f"   Corr(pos1, pos2): {corr_1_2:.4f}")
    print(f"   Corr(pos1, pos3): {corr_1_3:.4f}")
    print(f"   Corr(pos1, pos4): {corr_1_4:.4f}")
    print(f"   Corr(pos2, pos4): {corr_2_4:.4f}")
    
    resultados['correlaciones'] = {
        'pos1_pos2': corr_1_2,
        'pos1_pos3': corr_1_3,
        'pos1_pos4': corr_1_4,
        'pos2_pos4': corr_2_4
    }
    
    # 3. Diferencias promedio entre posiciones
    print("\n3. Diferencias promedio entre posiciones:")
    
    diff_1_4_mean = df['diff_pos1_pos4'].mean()
    diff_1_4_std = df['diff_pos1_pos4'].std()
    diff_1_4_max = df['diff_pos1_pos4'].max()
    
    print(f"   Δ(pos1 - pos4): {diff_1_4_mean:.4f} ± {diff_1_4_std:.4f}")
    print(f"   Max diferencia: {diff_1_4_max:.4f}")
    
    resultados['diferencias'] = {
        'mean_pos1_pos4': diff_1_4_mean,
        'std_pos1_pos4': diff_1_4_std,
        'max_pos1_pos4': diff_1_4_max
    }
    
    # 4. Verificar coherencia: manos con juego 31 deben estar arriba
    print("\n4. Verificación: Manos con juego 31 en top rankings")
    
    top_20_pos1 = df.nlargest(20, 'EV_pos1')
    juego_31_en_top = (top_20_pos1['valor_juego'] == 31).sum()
    
    print(f"   Manos con juego 31 en top 20: {juego_31_en_top}/20")
    
    resultados['juego_31_en_top20'] = juego_31_en_top
    
    # 5. Verificar coherencia: manos sin jugadas deben estar abajo
    print("\n5. Verificación: Manos sin jugadas en bottom rankings")
    
    bottom_20_pos1 = df.nsmallest(20, 'EV_pos1')
    sin_jugadas_en_bottom = ((~bottom_20_pos1['tiene_pares']) & 
                             (~bottom_20_pos1['tiene_juego'])).sum()
    
    print(f"   Manos sin pares ni juego en bottom 20: {sin_jugadas_en_bottom}/20")
    
    resultados['sin_jugadas_en_bottom20'] = sin_jugadas_en_bottom
    
    # 6. Resumen de verificaciones
    print("\n" + "="*80)
    print("RESUMEN DE VERIFICACIONES")
    print("="*80)
    
    checks = [
        ("Posición 1 siempre mayor", resultados['pos1_siempre_mayor'], True),
        ("Correlaciones altas (>0.99)", all(c > 0.99 for c in resultados['correlaciones'].values()), True),
        ("Juego 31 en top rankings", juego_31_en_top >= 10, True),
        ("Sin jugadas en bottom", sin_jugadas_en_bottom >= 10, True),
    ]
    
    all_pass = all(check[1] == check[2] for check in checks)
    
    for nombre, resultado, esperado in checks:
        status = "✓" if resultado == esperado else "✗"
        print(f"   {status} {nombre}: {resultado}")
    
    resultados['all_checks_pass'] = all_pass
    
    if all_pass:
        print("\n🎉 TODAS LAS VERIFICACIONES PASARON - Modelo matemático coherente")
    else:
        print("\n⚠️  ALGUNAS VERIFICACIONES FALLARON - Revisar modelo")
    
    return resultados


def mostrar_rankings(df: pd.DataFrame, top_n: int = 20):
    """
    Muestra los rankings de manos por EV en cada posición.
    
    Args:
        df: DataFrame con EVs calculados
        top_n: Número de manos a mostrar en top/bottom
    """
    print("\n" + "="*80)
    print(f"RANKINGS - TOP {top_n} MEJORES Y PEORES MANOS")
    print("="*80)
    
    for pos in POSICIONES:
        col_ev = f'EV_pos{pos}'
        
        print(f"\n{'─'*80}")
        print(f"POSICIÓN {pos}")
        print(f"{'─'*80}")
        
        # Top N
        print(f"\n🏆 TOP {top_n} MEJORES MANOS (Posición {pos}):")
        print(f"{'Rank':<6} {'Mano':<18} {'EV':<9} {'Grande':<7} {'Pares':<10} {'Juego':<7}")
        print("─" * 80)
        
        top_manos = df.nlargest(top_n, col_ev)
        for idx, row in enumerate(top_manos.itertuples(), 1):
            pares_str = row.tipo_pares if row.tiene_pares else "-"
            juego_str = f"{row.valor_juego}" if row.tiene_juego else "-"
            
            print(f"{idx:<6} {row.mano_str:<18} {getattr(row, col_ev):<9.4f} "
                  f"{row.prob_grande:<7.3f} {pares_str:<10} {juego_str:<7}")
        
        # Bottom N
        print(f"\n💀 BOTTOM {top_n} PEORES MANOS (Posición {pos}):")
        print(f"{'Rank':<6} {'Mano':<18} {'EV':<9} {'Grande':<7} {'Pares':<10} {'Juego':<7}")
        print("─" * 80)
        
        bottom_manos = df.nsmallest(top_n, col_ev)
        for idx, row in enumerate(bottom_manos.itertuples(), 1):
            pares_str = row.tipo_pares if row.tiene_pares else "-"
            juego_str = f"{row.valor_juego}" if row.tiene_juego else "-"
            
            print(f"{idx:<6} {row.mano_str:<18} {getattr(row, col_ev):<9.4f} "
                  f"{row.prob_grande:<7.3f} {pares_str:<10} {juego_str:<7}")


def analizar_por_categoria(df: pd.DataFrame):
    """
    Analiza EVs por categoría de mano (con/sin pares, con/sin juego, etc.).
    
    Args:
        df: DataFrame con EVs calculados
    """
    print("\n" + "="*80)
    print("ANÁLISIS POR CATEGORÍA DE MANO")
    print("="*80)
    
    # 1. Por combinación de jugadas
    print("\n1. EV promedio por combinación de jugadas:")
    print(f"{'Categoría':<30} {'N':<8} {'EV_pos1':<10} {'EV_pos4':<10} {'Δ(1-4)':<10}")
    print("─" * 80)
    
    categorias = [
        ("Pares + Juego 31", (df['tiene_pares']) & (df['valor_juego'] == 31)),
        ("Pares + Juego (no 31)", (df['tiene_pares']) & (df['tiene_juego']) & (df['valor_juego'] != 31)),
        ("Solo Pares", (df['tiene_pares']) & (~df['tiene_juego'])),
        ("Solo Juego 31", (~df['tiene_pares']) & (df['valor_juego'] == 31)),
        ("Solo Juego (no 31)", (~df['tiene_pares']) & (df['tiene_juego']) & (df['valor_juego'] != 31)),
        ("Sin Pares ni Juego", (~df['tiene_pares']) & (~df['tiene_juego']))
    ]
    
    for nombre, mask in categorias:
        subset = df[mask]
        if len(subset) > 0:
            ev1_mean = subset['EV_pos1'].mean()
            ev4_mean = subset['EV_pos4'].mean()
            diff_mean = subset['diff_pos1_pos4'].mean()
            
            print(f"{nombre:<30} {len(subset):<8} {ev1_mean:<10.4f} {ev4_mean:<10.4f} {diff_mean:<10.4f}")
        else:
            print(f"{nombre:<30} {0:<8} {'N/A':<10} {'N/A':<10} {'N/A':<10}")
    
    # 2. Por tipo de pares
    print("\n2. EV promedio por tipo de pares:")
    print(f"{'Tipo Pares':<20} {'N':<8} {'EV_pos1':<10} {'EV_pos4':<10} {'Δ(1-4)':<10}")
    print("─" * 80)
    
    for tipo in ['duples', 'medias', 'pares', 'sin_pares']:
        subset = df[df['tipo_pares'] == tipo]
        if len(subset) > 0:
            ev1_mean = subset['EV_pos1'].mean()
            ev4_mean = subset['EV_pos4'].mean()
            diff_mean = subset['diff_pos1_pos4'].mean()
            
            print(f"{tipo:<20} {len(subset):<8} {ev1_mean:<10.4f} {ev4_mean:<10.4f} {diff_mean:<10.4f}")
    
    # 3. Por valor de juego
    print("\n3. EV promedio por valor de juego:")
    print(f"{'Juego':<20} {'N':<8} {'EV_pos1':<10} {'EV_pos4':<10} {'Δ(1-4)':<10}")
    print("─" * 80)
    
    juegos = sorted(df[df['tiene_juego']]['valor_juego'].unique(), reverse=True)
    for juego in juegos:
        subset = df[df['valor_juego'] == juego]
        ev1_mean = subset['EV_pos1'].mean()
        ev4_mean = subset['EV_pos4'].mean()
        diff_mean = subset['diff_pos1_pos4'].mean()
        
        print(f"{juego:<20} {len(subset):<8} {ev1_mean:<10.4f} {ev4_mean:<10.4f} {diff_mean:<10.4f}")


def guardar_resultados(df: pd.DataFrame, resultados_verificacion: Dict, 
                       modo_str: str = "8reyes"):
    """
    Guarda los resultados en archivos CSV y TXT.
    
    Args:
        df: DataFrame con EVs calculados
        resultados_verificacion: Dict con resultados de verificaciones
        modo_str: "8reyes" o "4reyes"
    """
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS")
    print("="*80)
    
    # 1. Guardar CSV con todas las manos ordenadas por EV_pos1
    csv_file = f"sanity_check_ev_{modo_str}.csv"
    df_sorted = df.sort_values('EV_pos1', ascending=False)
    df_sorted.to_csv(csv_file, index=False)
    print(f"\n✓ CSV guardado: {csv_file}")
    print(f"  Columnas: {', '.join(df_sorted.columns)}")
    print(f"  Filas: {len(df_sorted)}")
    
    # 2. Guardar reporte de verificación
    report_file = f"sanity_check_report_{modo_str}.txt"
    with open(report_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("SANITY CHECK - VERIFICACIÓN DE CORDURA DEL MODELO EV\n")
        f.write("="*80 + "\n\n")
        f.write(f"Modo: {modo_str}\n")
        f.write(f"Perfil: {PERFIL}\n")
        f.write(f"Fecha: 26 febrero 2026\n")
        f.write(f"Total manos únicas: {len(df)}\n\n")
        
        f.write("RESULTADOS DE VERIFICACIONES:\n")
        f.write("-" * 80 + "\n\n")
        
        f.write("1. Posición 1 siempre mayor o igual:\n")
        f.write(f"   ✓ Verificado: {resultados_verificacion['pos1_siempre_mayor']}\n\n")
        
        f.write("2. Correlaciones entre posiciones:\n")
        for key, val in resultados_verificacion['correlaciones'].items():
            f.write(f"   {key}: {val:.4f}\n")
        f.write("\n")
        
        f.write("3. Diferencias pos1 - pos4:\n")
        f.write(f"   Media: {resultados_verificacion['diferencias']['mean_pos1_pos4']:.4f}\n")
        f.write(f"   Std: {resultados_verificacion['diferencias']['std_pos1_pos4']:.4f}\n")
        f.write(f"   Max: {resultados_verificacion['diferencias']['max_pos1_pos4']:.4f}\n\n")
        
        f.write("4. Coherencia de rankings:\n")
        f.write(f"   Juego 31 en top 20: {resultados_verificacion['juego_31_en_top20']}/20\n")
        f.write(f"   Sin jugadas en bottom 20: {resultados_verificacion['sin_jugadas_en_bottom20']}/20\n\n")
        
        f.write("CONCLUSIÓN:\n")
        f.write("-" * 80 + "\n")
        if resultados_verificacion['all_checks_pass']:
            f.write("✓ TODAS LAS VERIFICACIONES PASARON\n")
            f.write("  El modelo matemático es coherente y puede usarse para simulaciones.\n")
        else:
            f.write("✗ ALGUNAS VERIFICACIONES FALLARON\n")
            f.write("  Revisar el modelo antes de hacer simulaciones masivas.\n")
    
    print(f"✓ Reporte guardado: {report_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal del sanity check."""
    print("="*80)
    print("SANITY CHECK - VERIFICACIÓN DE CORDURA DEL MODELO EV")
    print("="*80)
    print(f"\nConfiguración:")
    print(f"  Modo: {'8 reyes' if MODO_8_REYES else '4 reyes'}")
    print(f"  Perfil: {PERFIL}")
    print(f"  Posiciones: {POSICIONES}")
    
    # 1. Inicializar motor
    print("\nInicializando motor de decisión...")
    motor = MotorDecisionMus(modo_8_reyes=MODO_8_REYES, perfil=PERFIL)
    estadisticas = motor.estadisticas
    
    # 2. Calcular EVs de todas las manos
    df = calcular_evs_todas_manos(motor, estadisticas, POSICIONES)
    
    # 3. Verificar coherencia
    resultados = verificar_coherencia(df)
    
    # 4. Mostrar rankings
    mostrar_rankings(df, top_n=20)
    
    # 5. Análisis por categoría
    analizar_por_categoria(df)
    
    # 6. Guardar resultados
    modo_str = "8reyes" if MODO_8_REYES else "4reyes"
    guardar_resultados(df, resultados, modo_str)
    
    print("\n" + "="*80)
    print("SANITY CHECK COMPLETADO")
    print("="*80)
    
    if resultados['all_checks_pass']:
        print("\n🎉 ¡Éxito! El modelo matemático es coherente.")
        print("   Se puede proceder con simulaciones masivas en Fase 2.")
    else:
        print("\n⚠️  Advertencia: Algunas verificaciones fallaron.")
        print("   Revisar el modelo antes de continuar.")


if __name__ == "__main__":
    main()
