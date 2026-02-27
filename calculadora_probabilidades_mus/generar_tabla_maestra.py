#!/usr/bin/env python3
"""
Genera tabla maestra con manos ordenadas por EV en cada posición.
"""

import pandas as pd
import sys


def formatear_mano(mano_str):
    """Formatea la mano de manera compacta."""
    return mano_str.replace('[', '').replace(']', '').replace(',', '')


def generar_descripcion(row):
    """Genera descripción compacta de la mano."""
    partes = []
    
    # Pares
    if row['tiene_pares']:
        tipo = row['tipo_pares']
        if tipo == 'duples':
            partes.append('Duples')
        elif tipo == 'medias':
            partes.append('Medias')
        elif tipo == 'pares':
            partes.append('Pares')
    
    # Juego o Punto
    if row['tiene_juego']:
        partes.append(f"J{int(row['valor_juego'])}")
    else:
        partes.append(f"P{int(row['valor_punto'])}")
    
    return ' '.join(partes) if partes else 'Sin pares'


def generar_tabla_posicion(df, posicion):
    """Genera tabla para una posición específica."""
    col_ev = f'EV_pos{posicion}'
    
    # Ordenar por EV descendente
    df_sorted = df.sort_values(col_ev, ascending=False).reset_index(drop=True)
    
    # Crear tabla markdown
    lineas = []
    lineas.append(f"\n## 🎯 Posición {posicion}")
    lineas.append("")
    
    # Nombres de posición
    nombres_pos = {
        1: "MANO (Posición 1)",
        2: "ZAGUERO (Posición 2)",
        3: "DELANTERO (Posición 3)",
        4: "POSTRE (Posición 4)"
    }
    lineas.append(f"**{nombres_pos[posicion]}**")
    lineas.append("")
    
    # Header
    lineas.append("| Rank | Mano         | Descripción      | EV      | Grande | Chica  | Pares  | J/P    |")
    lineas.append("|------|--------------|------------------|---------|--------|--------|--------|--------|")
    
    # Top 50 manos
    for idx, row in df_sorted.head(50).iterrows():
        rank = idx + 1
        mano = formatear_mano(row['mano_str'])
        desc = generar_descripcion(row)
        ev = f"{row[col_ev]:.3f}"
        
        # Probabilidades
        pg = f"{row['prob_grande']:.3f}"
        pch = f"{row['prob_chica']:.3f}"
        
        # Pares
        if row['tiene_pares']:
            pp = f"{row['probabilidad_pares']:.3f}"
        else:
            pp = "-"
        
        # Juego/Punto (probabilidad_juego incluye punto)
        pj = f"{row['probabilidad_juego']:.3f}"
        
        lineas.append(f"| {rank:2d}   | {mano:12s} | {desc:16s} | {ev:7s} | {pg:6s} | {pch:6s} | {pp:6s} | {pj:6s} |")
    
    return '\n'.join(lineas)


def generar_resumen_estadistico(df):
    """Genera resumen estadístico general."""
    lineas = []
    lineas.append("\n## 📊 Resumen Estadístico General")
    lineas.append("")
    
    # EV por posición
    lineas.append("### Valor Esperado por Posición")
    lineas.append("")
    lineas.append("| Posición | EV Promedio | EV Min  | EV Max  | Desv. Est. |")
    lineas.append("|----------|-------------|---------|---------|------------|")
    
    for pos in [1, 2, 3, 4]:
        col = f'EV_pos{pos}'
        media = df[col].mean()
        minimo = df[col].min()
        maximo = df[col].max()
        std = df[col].std()
        
        nombres = {1: "Mano (1)", 2: "Zaguero (2)", 3: "Delantero (3)", 4: "Postre (4)"}
        lineas.append(f"| {nombres[pos]:12s} | {media:11.3f} | {minimo:7.3f} | {maximo:7.3f} | {std:10.3f} |")
    
    lineas.append("")
    
    # Top 10 manos absolutas (pos 1)
    lineas.append("### 🏆 Top 10 Mejores Manos (Posición Mano)")
    lineas.append("")
    df_sorted = df.sort_values('EV_pos1', ascending=False).reset_index(drop=True)
    
    for idx, row in df_sorted.head(10).iterrows():
        mano = formatear_mano(row['mano_str'])
        desc = generar_descripcion(row)
        ev = row['EV_pos1']
        lineas.append(f"{idx+1}. **{mano}** - {desc} - EV: {ev:.3f}")
    
    lineas.append("")
    
    # Bottom 10 manos (pos 1)
    lineas.append("### 🔻 Top 10 Peores Manos (Posición Mano)")
    lineas.append("")
    
    for idx, row in df_sorted.tail(10).iterrows():
        mano = formatear_mano(row['mano_str'])
        desc = generar_descripcion(row)
        ev = row['EV_pos1']
        rank = len(df) - list(df_sorted.tail(10).index).index(idx)
        lineas.append(f"{rank}. **{mano}** - {desc} - EV: {ev:.3f}")
    
    return '\n'.join(lineas)


def main():
    # Leer CSV
    print("Cargando datos de sanity_check_ev_8reyes.csv...")
    df = pd.read_csv('sanity_check_ev_8reyes.csv')
    
    # Leer probabilidades adicionales de resultados_8reyes.csv
    print("Cargando probabilidades adicionales...")
    df_probs = pd.read_csv('resultados_8reyes.csv')
    
    # Merge para obtener probabilidad_pares y probabilidad_juego
    # Crear columna de merge compatible
    df['mano_join'] = df['mano_str'].apply(lambda x: str(sorted(eval(x))))
    df_probs['mano_join'] = df_probs['mano'].apply(lambda x: str(sorted(eval(x))))
    
    df = df.merge(
        df_probs[['mano_join', 'probabilidad_pares', 'probabilidad_juego']],
        on='mano_join',
        how='left'
    )
    
    print(f"Total manos cargadas: {len(df)}")
    
    # Crear archivo markdown
    output_file = 'TABLA_MAESTRA_EV.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# 📊 Tabla Maestra de Valor Esperado (EV) por Posición\n")
        f.write("\n")
        f.write("> **Análisis completo**: 330 manos únicas en modo 8 reyes  \n")
        f.write("> **Fecha**: 27 de febrero de 2026  \n")
        f.write("> **Versión**: v2.3 (Fase 1 completa)  \n")
        f.write("\n")
        f.write("---\n")
        
        # Resumen estadístico
        f.write(generar_resumen_estadistico(df))
        f.write("\n")
        f.write("---\n")
        
        # Tablas por posición
        for pos in [1, 2, 3, 4]:
            f.write(generar_tabla_posicion(df, pos))
            f.write("\n")
            if pos < 4:
                f.write("\n---\n")
    
    print(f"\n✅ Tabla maestra generada: {output_file}")
    print(f"   - 330 manos analizadas")
    print(f"   - Top 50 por cada posición")
    print(f"   - Resumen estadístico incluido")


if __name__ == "__main__":
    main()
