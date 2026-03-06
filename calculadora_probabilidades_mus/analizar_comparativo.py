"""
Script de análisis comparativo: Fase 1 (sin descarte) vs Fase 2 (con descarte óptimo).

Compara las probabilidades de victoria en cada lance antes y después de aplicar
la estrategia óptima de descarte, mostrando la mejora obtenida.
"""

import pandas as pd
import sys
from pathlib import Path

# Rutas de archivos
FASE1_FILE = Path(__file__).parent / "resultados_8reyes.csv"
FASE2_FILE = Path(__file__).parent / "probabilidades_fase2.csv"


def cargar_datos():
    """Carga los datos de Fase 1 y Fase 2."""
    print("=" * 70)
    print("ANÁLISIS COMPARATIVO: FASE 1 vs FASE 2")
    print("=" * 70)
    
    if not FASE1_FILE.exists():
        print(f"\n❌ Error: No se encuentra {FASE1_FILE}")
        return None, None
    
    if not FASE2_FILE.exists():
        print(f"\n❌ Error: No se encuentra {FASE2_FILE}")
        print("   Ejecuta primero: python simulador_fase2.py")
        return None, None
    
    print(f"\n📁 Cargando datos...")
    fase1 = pd.read_csv(FASE1_FILE)
    fase2 = pd.read_csv(FASE2_FILE)
    
    print(f"   ✓ Fase 1: {len(fase1)} manos")
    print(f"   ✓ Fase 2: {len(fase2)} manos")
    
    return fase1, fase2


def comparar_estadisticas_generales(fase1, fase2):
    """Compara estadísticas generales entre fases."""
    print("\n" + "=" * 70)
    print("ESTADÍSTICAS GENERALES")
    print("=" * 70)
    
    lances = ["grande", "chica", "pares", "juego"]
    columnas_fase1 = [f"probabilidad_{lance}" for lance in lances]
    columnas_fase2 = [f"prob_{lance}" for lance in lances]
    
    print("\n{:<15} {:>15} {:>15} {:>15}".format("Lance", "Fase 1 (media)", "Fase 2 (media)", "Mejora"))
    print("-" * 70)
    
    for lance, col1, col2 in zip(lances, columnas_fase1, columnas_fase2):
        media_fase1 = fase1[col1].mean()
        media_fase2 = fase2[col2].mean()
        mejora = media_fase2 - media_fase1
        
        print("{:<15} {:>14.4f}  {:>14.4f}  {:>14.4f}".format(
            lance.capitalize(), media_fase1, media_fase2, mejora
        ))


def encontrar_mejoras(fase1, fase2):
    """Encuentra las manos con mayor mejora tras descarte."""
    print("\n" + "=" * 70)
    print("TOP 10 MANOS CON MAYOR MEJORA EN PARES")
    print("=" * 70)
    
    # Normalizar columna mano para merge
    fase1['mano_norm'] = fase1['mano'].astype(str)
    fase2['mano_norm'] = fase2['mano'].astype(str)
    
    # Merge por mano
    comparacion = fase1.merge(
        fase2, 
        left_on='mano_norm', 
        right_on='mano_norm',
        suffixes=('_f1', '_f2')
    )
    
    # Calcular mejoras
    comparacion['mejora_pares'] = comparacion['prob_pares'] - comparacion['probabilidad_pares']
    comparacion['mejora_juego'] = comparacion['prob_juego'] - comparacion['probabilidad_juego']
    comparacion['mejora_grande'] = comparacion['prob_grande'] - comparacion['probabilidad_grande']
    comparacion['mejora_chica'] = comparacion['prob_chica'] - comparacion['probabilidad_chica']
    
    # Top 10 mejoras en pares
    top_pares = comparacion.nlargest(10, 'mejora_pares')
    print("\n{:<20} {:>12} {:>12} {:>12}".format("Mano", "Fase 1", "Fase 2", "Mejora"))
    print("-" * 70)
    
    for _, row in top_pares.iterrows():
        print("{:<20} {:>12.4f} {:>12.4f} {:>12.4f}".format(
            row['mano_f1'][:18],
            row['probabilidad_pares'],
            row['prob_pares'],
            row['mejora_pares']
        ))
    
    # Top 10 mejoras en juego
    print("\n" + "=" * 70)
    print("TOP 10 MANOS CON MAYOR MEJORA EN JUEGO")
    print("=" * 70)
    
    top_juego = comparacion.nlargest(10, 'mejora_juego')
    print("\n{:<20} {:>12} {:>12} {:>12}".format("Mano", "Fase 1", "Fase 2", "Mejora"))
    print("-" * 70)
    
    for _, row in top_juego.iterrows():
        print("{:<20} {:>12.4f} {:>12.4f} {:>12.4f}".format(
            row['mano_f1'][:18],
            row['probabilidad_juego'],
            row['prob_juego'],
            row['mejora_juego']
        ))
    
    return comparacion


def analizar_por_tipo_mano(comparacion):
    """Analiza mejoras por tipo de mano."""
    print("\n" + "=" * 70)
    print("ANÁLISIS POR TIPO DE MANO")
    print("=" * 70)
    
    # Clasificar manos por su valor inicial
    print("\nDistribución de mejoras en Pares:")
    print("-" * 70)
    
    mejora_positiva = (comparacion['mejora_pares'] > 0).sum()
    mejora_negativa = (comparacion['mejora_pares'] < 0).sum()
    sin_cambio = (comparacion['mejora_pares'] == 0).sum()
    
    total = len(comparacion)
    print(f"Mejoran:      {mejora_positiva:4d} manos ({100*mejora_positiva/total:.1f}%)")
    print(f"Empeoran:     {mejora_negativa:4d} manos ({100*mejora_negativa/total:.1f}%)")
    print(f"Sin cambio:   {sin_cambio:4d} manos ({100*sin_cambio/total:.1f}%)")
    
    print("\nDistribución de mejoras en Juego:")
    print("-" * 70)
    
    mejora_positiva = (comparacion['mejora_juego'] > 0).sum()
    mejora_negativa = (comparacion['mejora_juego'] < 0).sum()
    sin_cambio = (comparacion['mejora_juego'] == 0).sum()
    
    print(f"Mejoran:      {mejora_positiva:4d} manos ({100*mejora_positiva/total:.1f}%)")
    print(f"Empeoran:     {mejora_negativa:4d} manos ({100*mejora_negativa/total:.1f}%)")
    print(f"Sin cambio:   {sin_cambio:4d} manos ({100*sin_cambio/total:.1f}%)")


def resumen_ejecutivo(comparacion):
    """Genera un resumen ejecutivo de los resultados."""
    print("\n" + "=" * 70)
    print("RESUMEN EJECUTIVO")
    print("=" * 70)
    
    mejora_pares_media = comparacion['mejora_pares'].mean()
    mejora_juego_media = comparacion['mejora_juego'].mean()
    mejora_grande_media = comparacion['mejora_grande'].mean()
    mejora_chica_media = comparacion['mejora_chica'].mean()
    
    print("\n📊 Mejoras promedio tras descarte óptimo:")
    print(f"   • Grande: {mejora_grande_media:+.4f} ({100*mejora_grande_media:+.2f}%)")
    print(f"   • Chica:  {mejora_chica_media:+.4f} ({100*mejora_chica_media:+.2f}%)")
    print(f"   • Pares:  {mejora_pares_media:+.4f} ({100*mejora_pares_media:+.2f}%)")
    print(f"   • Juego:  {mejora_juego_media:+.4f} ({100*mejora_juego_media:+.2f}%)")
    
    # Máxima mejora observada
    max_mejora_pares = comparacion['mejora_pares'].max()
    max_mejora_juego = comparacion['mejora_juego'].max()
    
    mano_max_pares = comparacion.loc[comparacion['mejora_pares'].idxmax(), 'mano_f1']
    mano_max_juego = comparacion.loc[comparacion['mejora_juego'].idxmax(), 'mano_f1']
    
    print(f"\n🏆 Máxima mejora en Pares: {max_mejora_pares:+.4f}")
    print(f"   Mano: {mano_max_pares}")
    
    print(f"\n🏆 Máxima mejora en Juego: {max_mejora_juego:+.4f}")
    print(f"   Mano: {mano_max_juego}")
    
    # Conclusiones
    print("\n💡 Conclusiones:")
    if mejora_pares_media > 0.01:
        print("   ✓ El descarte óptimo mejora significativamente las probabilidades de Pares")
    if mejora_juego_media > 0.01:
        print("   ✓ El descarte óptimo mejora significativamente las probabilidades de Juego")
    if mejora_grande_media > 0.005:
        print("   ✓ Mejora moderada en Grande (posiblemente por mejor distribución)")
    if mejora_chica_media < -0.005:
        print("   ⚠ Pequeña disminución en Chica (trade-off por optimizar otros lances)")


def main():
    """Función principal."""
    # Cargar datos
    fase1, fase2 = cargar_datos()
    
    if fase1 is None or fase2 is None:
        print("\n❌ No se pudieron cargar los datos")
        return
    
    # Análisis
    comparar_estadisticas_generales(fase1, fase2)
    comparacion = encontrar_mejoras(fase1, fase2)
    
    if comparacion is not None and len(comparacion) > 0:
        analizar_por_tipo_mano(comparacion)
        resumen_ejecutivo(comparacion)
        
        # Exportar comparación completa
        output_file = Path(__file__).parent / "analisis_fase1_vs_fase2.csv"
        comparacion.to_csv(output_file, index=False)
        print(f"\n📁 Análisis completo exportado a: {output_file}")
    
    print("\n" + "=" * 70)
    print("✓ ANÁLISIS COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
