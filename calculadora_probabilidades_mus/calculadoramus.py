"""
Calculadora de Probabilidades de Mus mediante Monte Carlo
Calcula las probabilidades de victoria de todas las manos iniciales posibles
en los lances de GRANDE, CHICA, PARES y JUEGO/PUNTO.
"""

import random
import itertools
import pandas as pd


# ============================================================================
# CONFIGURACIÓN DE LA BARAJA
# ============================================================================

def inicializar_baraja(modo_8_reyes=False):
    """
    Inicializa la baraja española según el modo de juego.
    
    Args:
        modo_8_reyes: Si es True, usa 8 reyes (1x8, 2x4, 3x4, 12x4)
                     donde 2=2 y 3=12 para efectos de juego
                     Si es False, usa 4 reyes tradicional (1x8, 12x8)
    
    Returns:
        Lista con las 40 cartas de la baraja
    """
    if modo_8_reyes:
        # 8 reyes: 
       
        return [1, 1, 1, 1, 1, 1, 1, 1,                      
                12, 12, 12, 12, 12, 12, 12, 12,           
                4, 4, 4, 4,
                5, 5, 5, 5,
                6, 6, 6, 6,
                7, 7, 7, 7,
                10, 10, 10, 10,
                11, 11, 11, 11
                ]            
    else:
        # 4 reyes tradicional
        return [1, 1, 1, 1, 2, 2, 2, 2,     
                4, 4, 4, 4,
                5, 5, 5, 5,
                6, 6, 6, 6,
                7, 7, 7, 7,
                10, 10, 10, 10,
                11, 11, 11, 11,
                3, 3, 3, 3, 12, 12, 12, 12] 


# ============================================================================
# GENERACIÓN DE MANOS ÚNICAS
# ============================================================================

def generar_manos_unicas(baraja):
    """Genera todas las combinaciones únicas de 4 cartas."""
    combinaciones = itertools.combinations(baraja, 4)
    manos_unicas = {tuple(sorted(mano)): list(mano) for mano in combinaciones}
    return list(manos_unicas.values())



# ============================================================================
# LANCES: PARES
# ============================================================================

def clasificar_pares(mano):
    """
    Clasifica los pares de una mano.
    
    Returns:
        tupla (tipo, valor_principal, valor_secundario)
        tipo: "sin_pares", "pares", "medias", "duples"
    """
    conteo = {}
    for carta in mano:
        conteo[carta] = conteo.get(carta, 0) + 1
    
    repeticiones = {valor: count for valor, count in conteo.items() if count > 1}
    
    if not repeticiones:
        return "sin_pares", 0, 0
    elif len(repeticiones) == 1:
        valor = list(repeticiones.keys())[0]
        count = repeticiones[valor]
        if count == 4:
            return "duples", valor, valor
        elif count == 3:
            return "medias", valor, 0
        else:  # count == 2
            return "pares", valor, 0
    else:  # len(repeticiones) == 2, ambos con 2 cartas
        valores = sorted(repeticiones.keys(), reverse=True)
        return "duples", valores[0], valores[1]


def comparar_pares(tipo1, valor1_1, valor1_2, tipo2, valor2_1, valor2_2, es_mano):
    """Compara dos manos en el lance de PARES."""
    jerarquia = {"sin_pares": 0, "pares": 1, "medias": 2, "duples": 3}
    
    if jerarquia[tipo1] != jerarquia[tipo2]:
        return 1 if jerarquia[tipo1] > jerarquia[tipo2] else -1
    
    # Mismo tipo, comparar valores
    if valor1_1 != valor2_1:
        return 1 if valor1_1 > valor2_1 else -1
    if valor1_2 != valor2_2:
        return 1 if valor1_2 > valor2_2 else -1
    
    return 1 if es_mano else -1  # Empate: gana la mano


# ============================================================================
# LANCES: GRANDE Y CHICA
# ============================================================================

def comparar_grande_chica(mano1, mano2, es_mano):
    """
    Compara dos manos carta por carta.
    Para GRANDE se ordenan de mayor a menor.
    Para CHICA se ordenan de menor a mayor.
    """
    for carta1, carta2 in zip(mano1, mano2):
        if carta1 != carta2:
            return 1 if carta1 > carta2 else -1
    return 1 if es_mano else -1  # Empate: gana la mano


# ============================================================================
# LANCES: JUEGO Y PUNTO
# ============================================================================

def calcular_valor_juego(mano):
    """Calcula el valor de juego (31-40). Retorna 0 si no hay juego."""
    valor = sum(min(carta, 10) for carta in mano)
    return valor if valor >= 31 else 0


def convertir_valor_juego(valor):
    """Convierte el valor de juego a su equivalente en el Mus."""
    valores_juego = {31: 8, 32: 7, 40: 6, 37: 5, 36: 4, 35: 3, 34: 2, 33: 1}
    return valores_juego.get(valor, 0)


def comparar_juego(valor1, valor2, es_mano):
    """Compara dos valores de juego."""
    if valor1 != valor2:
        return 1 if valor1 > valor2 else -1
    return 1 if es_mano else -1


def calcular_valor_punto(mano):
    """Calcula el valor de punto (suma de cartas, máximo 10 por carta)."""
    return sum(min(carta, 10) for carta in mano)  #min(carta,10) devuelve el valor de la carta si es menor o igual a 10, o 10 si la carta es mayor (como el 11 o 12)


def comparar_punto(punto1, punto2, es_mano):
    """Compara dos puntos (gana el más cercano a 30)."""
    dist1 = abs(punto1 - 30)
    dist2 = abs(punto2 - 30)
    if dist1 != dist2:
        return 1 if dist1 < dist2 else -1
    return 1 if es_mano else -1



# ============================================================================
# SIMULACIÓN MONTE CARLO
# ============================================================================

def simular_mano(mano, baraja_original, iteraciones=10000):
    """
    Simula una mano contra manos aleatorias y calcula probabilidades.
    
    Args:
        mano: Lista de 4 cartas que representan la mano a simular
        baraja_original: Baraja completa (40 cartas)
        iteraciones: Número de simulaciones Monte Carlo
    
    Returns:
        Diccionario con las probabilidades de victoria en cada lance
    """
    # Preparar baraja sin las cartas de la mano
    baraja_disponible = baraja_original.copy()
    for carta in mano:
        baraja_disponible.remove(carta)
    
    # Contadores de victorias
    victorias = {"grande": 0, "chica": 0, "pares": 0, "juego": 0}
    es_mano = True
    
    for _ in range(iteraciones):
        # Repartir dos manos aleatorias
        baraja_temp = baraja_disponible.copy()
        mano1 = random.sample(baraja_temp, 4)
        for carta in mano1:
            baraja_temp.remove(carta)
        mano2 = random.sample(baraja_temp, 4)
        
        # GRANDE: comparar con mayor a menor
        mano_grande = sorted(mano, reverse=True)
        mano1_grande = sorted(mano1, reverse=True)
        mano2_grande = sorted(mano2, reverse=True)
        
        if (comparar_grande_chica(mano_grande, mano1_grande, es_mano) > 0 and
            comparar_grande_chica(mano_grande, mano2_grande, es_mano) > 0):
            victorias["grande"] += 1
        
        # CHICA: comparar con menor a mayor
        mano_chica = sorted(mano)
        mano1_chica = sorted(mano1)
        mano2_chica = sorted(mano2)
        
        if (comparar_grande_chica(mano_chica, mano1_chica, es_mano) < 0 and
            comparar_grande_chica(mano_chica, mano2_chica, es_mano) < 0):
            victorias["chica"] += 1
        
        # PARES
        tipo_mano, val1, val2 = clasificar_pares(mano)
        tipo_mano1, val1_m1, val2_m1 = clasificar_pares(mano1)
        tipo_mano2, val1_m2, val2_m2 = clasificar_pares(mano2)
        
        if (comparar_pares(tipo_mano, val1, val2, tipo_mano1, val1_m1, val2_m1, es_mano) > 0 and
            comparar_pares(tipo_mano, val1, val2, tipo_mano2, val1_m2, val2_m2, es_mano) > 0):
            victorias["pares"] += 1
        
        # JUEGO o PUNTO
        valor_juego = convertir_valor_juego(calcular_valor_juego(mano))
        valor_juego1 = convertir_valor_juego(calcular_valor_juego(mano1))
        valor_juego2 = convertir_valor_juego(calcular_valor_juego(mano2))
        
        if valor_juego > 0 or valor_juego1 > 0 or valor_juego2 > 0:
            # Hay juego
            if (comparar_juego(valor_juego, valor_juego1, es_mano) > 0 and
                comparar_juego(valor_juego, valor_juego2, es_mano) > 0):
                victorias["juego"] += 1
        else:
            # Se compara por punto
            punto = calcular_valor_punto(mano)
            punto1 = calcular_valor_punto(mano1)
            punto2 = calcular_valor_punto(mano2)
            
            if (comparar_punto(punto, punto1, es_mano) > 0 and
                comparar_punto(punto, punto2, es_mano) > 0):
                victorias["juego"] += 1
    
    # Calcular probabilidades
    return {
        "mano": mano,
        "probabilidad_grande": victorias["grande"] / iteraciones,
        "probabilidad_chica": victorias["chica"] / iteraciones,
        "probabilidad_pares": victorias["pares"] / iteraciones,
        "probabilidad_juego": victorias["juego"] / iteraciones
    }


def calcular_todas_probabilidades(modo_8_reyes=False, iteraciones=10000):
    """
    Calcula las probabilidades de todas las manos únicas posibles.
    
    Args:
        modo_8_reyes: True para jugar con 8 reyes, False para 4 reyes
        iteraciones: Número de simulaciones por mano
    
    Returns:
        DataFrame con los resultados
    """
    baraja = inicializar_baraja(modo_8_reyes)
    manos_unicas = generar_manos_unicas(baraja)
    
    print(f"\n{'='*60}")
    print(f"Modo: {'8 REYES' if modo_8_reyes else '4 REYES'}")
    print(f"Total de manos únicas: {len(manos_unicas)}")
    print(f"Iteraciones por mano: {iteraciones:,}")
    print(f"{'='*60}\n")
    
    resultados = []
    for i, mano in enumerate(manos_unicas, 1):
        if i % 50 == 0:
            print(f"Procesando mano {i}/{len(manos_unicas)}...")
        resultado = simular_mano(mano, baraja, iteraciones)
        resultados.append(resultado)
    
    return pd.DataFrame(resultados)


def guardar_resultados(df, prefijo="resultados"):
    """Guarda los resultados en archivos CSV y TXT."""
    archivo_csv = f"{prefijo}.csv"
    archivo_txt = f"{prefijo}.txt"
    
    df.to_csv(archivo_csv, index=False)
    with open(archivo_txt, 'w') as f:
        f.write(df.to_string(index=False))
    
    print(f"\n✓ Resultados guardados:")
    print(f"  - {archivo_csv}")
    print(f"  - {archivo_txt}")


# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

def main():
    """Función principal del programa."""
    print("\n" + "="*60)
    print(" CALCULADORA DE PROBABILIDADES DE MUS - MONTE CARLO")
    print("="*60)
    
    # Selección de modo
    print("\nSelecciona el modo de juego:")
    print("  1. Modo 4 REYES (1x4, 12x4 - tradicional)")
    print("  2. Modo 8 REYES (1x8, 12x8 con 2=2 y 3=12)")
    
    while True:
        opcion = input("\nOpción [1/2]: ").strip()
        if opcion in ["1", "2"]:
            break
        print("Por favor, introduce 1 o 2.")
    
    modo_8_reyes = (opcion == "2")
    
    # Ejecutar simulación
    df_resultados = calcular_todas_probabilidades(modo_8_reyes)
    
    # Guardar resultados
    prefijo = "resultados_8reyes" if modo_8_reyes else "resultados_4reyes"
    guardar_resultados(df_resultados, prefijo)
    
    # Mostrar estadísticas generales
    print(f"\n{'='*60}")
    print("ESTADÍSTICAS GENERALES")
    print(f"{'='*60}")
    print(f"\nPrimeras 10 manos:")
    print(df_resultados.head(10).to_string(index=False))
    
    print(f"\n{'='*60}")
    print("Proceso completado exitosamente")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()


