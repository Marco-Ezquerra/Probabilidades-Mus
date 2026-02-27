"""
Script para ordenar y analizar los resultados de la calculadora de Mus
"""

import pandas as pd
import os
import sys


def listar_archivos_csv():
    """Lista todos los archivos CSV en el directorio actual."""
    archivos = [f for f in os.listdir('.') if f.endswith('.csv') and 'resultados' in f]
    return archivos


def ordenar_resultados(archivo_csv, criterio="probabilidad_grande"):
    """
    Ordena los resultados según el criterio especificado.
    
    Args:
        archivo_csv: Nombre del archivo CSV a ordenar
        criterio: Columna por la cual ordenar
    """
    if not os.path.exists(archivo_csv):
        print(f"❌ Error: No se encuentra el archivo '{archivo_csv}'")
        return
    
    # Cargar datos
    df = pd.read_csv(archivo_csv)
    
    # Verificar que la columna existe
    if criterio not in df.columns:
        print(f"❌ Error: La columna '{criterio}' no existe.")
        print(f"Columnas disponibles: {', '.join(df.columns)}")
        return
    
    # Ordenar
    df_ordenado = df.sort_values(by=criterio, ascending=False)
    
    # Generar nombres de salida
    base_name = archivo_csv.replace('.csv', '')
    salida_csv = f"{base_name}_ordenado_{criterio}.csv"
    salida_txt = f"{base_name}_ordenado_{criterio}.txt"
    
    # Guardar
    df_ordenado.to_csv(salida_csv, index=False)
    with open(salida_txt, 'w') as f:
        f.write(df_ordenado.to_string(index=False))
    
    print(f"\n✓ Resultados ordenados por '{criterio}':")
    print(f"  - {salida_csv}")
    print(f"  - {salida_txt}")
    
    # Mostrar top 10
    print(f"\n{'='*70}")
    print(f"TOP 10 MANOS - {criterio.upper()}")
    print(f"{'='*70}")
    print(df_ordenado.head(10).to_string(index=False))
    print(f"\n{'='*70}\n")


def main():
    """Función principal."""
    print("\n" + "="*70)
    print(" ORDENADOR DE RESULTADOS - CALCULADORA DE MUS")
    print("="*70 + "\n")
    
    # Listar archivos disponibles
    archivos = listar_archivos_csv()
    
    if not archivos:
        print("❌ No se encontraron archivos de resultados CSV en el directorio actual.")
        print("Ejecuta primero 'calculadoramus.py' para generar resultados.")
        return
    
    print("Archivos disponibles:")
    for i, archivo in enumerate(archivos, 1):
        print(f"  {i}. {archivo}")
    
    # Seleccionar archivo
    if len(archivos) == 1:
        archivo_seleccionado = archivos[0]
        print(f"\nUsando: {archivo_seleccionado}")
    else:
        while True:
            try:
                opcion = int(input(f"\nSelecciona un archivo [1-{len(archivos)}]: "))
                if 1 <= opcion <= len(archivos):
                    archivo_seleccionado = archivos[opcion - 1]
                    break
            except ValueError:
                pass
            print("Opción inválida.")
    
    # Seleccionar criterio de ordenación
    print("\nCriterios de ordenación:")
    print("  1. probabilidad_grande")
    print("  2. probabilidad_chica")
    print("  3. probabilidad_pares")
    print("  4. probabilidad_juego")
    
    criterios = {
        "1": "probabilidad_grande",
        "2": "probabilidad_chica",
        "3": "probabilidad_pares",
        "4": "probabilidad_juego"
    }
    
    while True:
        opcion = input("\nSelecciona criterio [1-4] (por defecto: 1): ").strip() or "1"
        if opcion in criterios:
            criterio = criterios[opcion]
            break
        print("Opción inválida.")
    
    # Ordenar y mostrar resultados
    ordenar_resultados(archivo_seleccionado, criterio)


if __name__ == "__main__":
    main()



