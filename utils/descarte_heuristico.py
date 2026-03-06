"""
Heurística base de descarte para simular jugadores promedio en el Mus.

Esta heurística implementa reglas conservadoras/promedio para que los 
jugadores no humanos tomen decisiones de descarte realistas en las simulaciones.
"""

import sys
from pathlib import Path

# Añadir paths para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "calculadora_probabilidades_mus"))
sys.path.insert(0, str(Path(__file__).parent))

from mascaras_descarte import generar_mascaras, encontrar_mascara


def tiene_rey(mano):
    """Verifica si la mano tiene al menos un Rey (12)."""
    return 12 in mano


def contar_carta(mano, valor):
    """Cuenta cuántas cartas de un valor específico hay en la mano."""
    return mano.count(valor)


def tiene_pareja(mano, valor):
    """Verifica si hay pareja (2+) de un valor específico."""
    return contar_carta(mano, valor) >= 2


def clasificar_mano_basico(mano):
    """
    Clasifica rápidamente una mano para la heurística.
    
    Returns:
        dict: {
            'reyes': int,           # Cantidad de reyes
            'ases': int,            # Cantidad de ases  
            'pareja_ases': bool,    # Tiene 2+ ases
            'figuras_altas': int,   # Caballos (11) y Sotas (10)
            'basura': list          # Cartas 4-7
        }
    """
    return {
        'reyes': contar_carta(mano, 12),
        'ases': contar_carta(mano, 1),
        'pareja_ases': tiene_pareja(mano, 1),
        'figuras_altas': sum(1 for c in mano if c in [10, 11]),
        'basura': [i for i, c in enumerate(mano) if c in [4, 5, 6, 7]]
    }


def descarte_heuristico_base(mano, posicion):
    """
    Decide qué cartas descartar según heurística de jugador promedio.
    
    Reglas:
    1. Mantener siempre Reyes (12)
    2. Mantener pareja de Ases SOLO si posicion == 4 (Postre)
    3. Mantener As suelto SOLO si hay Rey (buscar 31)
    4. Mantener figuras altas (10, 11) SOLO si hay Rey
    5. Descartar basura (4, 5, 6, 7) siempre
    6. Descartar figuras sueltas sin soporte
    
    Args:
        mano: Lista de 4 cartas (integers)
        posicion: Posición del jugador (1=Mano, 2, 3, 4=Postre)
    
    Returns:
        tuple: Máscara de descarte (tupla de índices)
        
    Ejemplo:
        >>> descarte_heuristico_base([12, 11, 7, 4], posicion=1)
        (2, 3)  # Descarta el 7 y el 4, mantiene 12 y 11
    """
    info = clasificar_mano_basico(mano)
    indices_descartar = []
    
    # Lista de prioridades de qué mantener (en orden)
    mantener = [False] * 4
    
    # 1. REYES: Siempre mantener
    for i, carta in enumerate(mano):
        if carta == 12:
            mantener[i] = True
    
    # 2. PAREJA DE ASES: Solo mantener en posición 4 (Postre)
    if info['pareja_ases'] and posicion == 4:
        # Mantener ambos ases
        for i, carta in enumerate(mano):
            if carta == 1:
                mantener[i] = True
    
    # 3. AS SUELTO: Solo si hay Rey (buscar 31)
    elif info['ases'] > 0 and info['reyes'] > 0:
        # Mantener UN as (el primero que encontremos)
        as_encontrado = False
        for i, carta in enumerate(mano):
            if carta == 1 and not as_encontrado:
                mantener[i] = True
                as_encontrado = True
    
    # 4. FIGURAS ALTAS (10, 11): Solo si hay Rey
    if info['reyes'] > 0:
        for i, carta in enumerate(mano):
            if carta in [10, 11]:
                mantener[i] = True
    
    # 5. Identificar qué descartar (lo que NO se mantiene)
    indices_descartar = [i for i in range(4) if not mantener[i]]
    
    # Si no descartamos nada (caso raro: mano perfecta), descartar basura
    if not indices_descartar:
        # Buscar la carta más baja
        carta_min = min(mano)
        for i, carta in enumerate(mano):
            if carta == carta_min:
                indices_descartar = [i]
                break
    
    return tuple(indices_descartar)


def descarte_heuristico_indice(mano, posicion):
    """
    Versión que devuelve el índice de máscara (0-14) en lugar de la tupla.
    
    Args:
        mano: Lista de 4 cartas
        posicion: Posición del jugador (1-4)
    
    Returns:
        int: Índice de la máscara (0-14)
    """
    mascara = descarte_heuristico_base(mano, posicion)
    mascaras = generar_mascaras()
    return mascaras.index(mascara)


def simular_descarte_heuristico(mano, posicion, verbose=False):
    """
    Simula el proceso completo de descarte con la heurística base.
    
    Args:
        mano: Lista de 4 cartas
        posicion: Posición del jugador (1-4)
        verbose: Si True, imprime detalles
    
    Returns:
        dict: {
            'mascara': tuple,
            'indices_descarte': tuple,
            'cartas_descartadas': list,
            'cartas_mantenidas': list
        }
    """
    mascara = descarte_heuristico_base(mano, posicion)
    cartas_descartadas = [mano[i] for i in mascara]
    cartas_mantenidas = [mano[i] for i in range(4) if i not in mascara]
    
    resultado = {
        'mascara': mascara,
        'indices_descarte': mascara,
        'cartas_descartadas': cartas_descartadas,
        'cartas_mantenidas': cartas_mantenidas
    }
    
    if verbose:
        print(f"Mano: {mano} (Posición: {posicion})")
        print(f"  Mantiene: {cartas_mantenidas}")
        print(f"  Descarta: {cartas_descartadas}")
        print(f"  Máscara: {mascara}")
    
    return resultado


if __name__ == "__main__":
    print("=" * 70)
    print("TEST: Heurística Base de Descarte")
    print("=" * 70)
    
    casos_test = [
        ([12, 12, 11, 10], 1, "Duples de Reyes + Juego (Pos 1)"),
        ([12, 11, 7, 4], 1, "Rey + Caballo + Basura (Pos 1)"),
        ([1, 1, 5, 6], 4, "Pareja de Ases en Postre (Pos 4)"),
        ([1, 1, 5, 6], 1, "Pareja de Ases en Mano (Pos 1)"),
        ([12, 1, 10, 5], 2, "Rey + As + Caballo (Pos 2)"),
        ([7, 6, 5, 4], 3, "Pura basura (Pos 3)"),
        ([12, 12, 12, 1], 1, "Medias de Rey + As (Pos 1)"),
    ]
    
    print("\nCasos de prueba:")
    print("-" * 70)
    
    for mano, pos, descripcion in casos_test:
        print(f"\n{descripcion}")
        resultado = simular_descarte_heuristico(mano, pos, verbose=True)
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
