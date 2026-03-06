"""
Módulo para gestionar máscaras de descarte en el Mus.

Una máscara de descarte especifica qué cartas de una mano (4 cartas) 
se deben descartar. Se representa como una tupla de índices.

Ejemplo:
    mano = [12, 12, 11, 10]
    mascara = (0, 1)  # Descartar posiciones 0 y 1 (ambos 12)
    -> Resultado: Descartar [12, 12], Quedan [11, 10]
"""

from itertools import combinations
import random


def generar_mascaras(n_cartas=4):
    """
    Genera todas las máscaras de descarte posibles para una mano.
    
    No incluye la máscara vacía (descartar 0 cartas) ya que no tiene 
    sentido pedir Mus y no descartar.
    
    Args:
        n_cartas: Número de cartas en la mano (default: 4)
    
    Returns:
        list[tuple]: Lista de 15 tuplas representando máscaras.
                     Ejemplo: [(0,), (1,), (2,), (3,), (0,1), ..., (0,1,2,3)]
    """
    mascaras = []
    for k in range(1, n_cartas + 1):  # k = 1, 2, 3, 4 cartas a descartar
        for combo in combinations(range(n_cartas), k):
            mascaras.append(combo)
    return mascaras


def aplicar_mascara(mano, mascara):
    """
    Aplica una máscara de descarte a una mano.
    
    Args:
        mano: Lista de 4 cartas (integers)
        mascara: Tupla de índices a descartar, ej: (0, 2)
    
    Returns:
        tuple: (mano_restante, cartas_descartadas)
            - mano_restante: Lista con las cartas que quedan
            - cartas_descartadas: Lista con las cartas descartadas
    
    Ejemplo:
        >>> aplicar_mascara([12, 12, 11, 10], (0, 1))
        ([11, 10], [12, 12])
    """
    mano_restante = [mano[i] for i in range(len(mano)) if i not in mascara]
    cartas_descartadas = [mano[i] for i in mascara]
    return mano_restante, cartas_descartadas


def robar_cartas(baraja_disponible, n):
    """
    Roba n cartas aleatorias de una baraja y las remueve.
    
    Args:
        baraja_disponible: Lista de cartas disponibles (se modifica in-place)
        n: Número de cartas a robar
    
    Returns:
        list: Lista de cartas robadas
    
    Raises:
        ValueError: Si no hay suficientes cartas en la baraja
    
    Nota:
        Esta función MODIFICA la baraja_disponible (remueve las cartas robadas)
    """
    if len(baraja_disponible) < n:
        raise ValueError(f"No hay suficientes cartas. Disponibles: {len(baraja_disponible)}, Pedidas: {n}")
    
    cartas_robadas = random.sample(baraja_disponible, n)
    for carta in cartas_robadas:
        baraja_disponible.remove(carta)
    
    return cartas_robadas


def completar_mano(mano_parcial, baraja_disponible):
    """
    Completa una mano parcial robando cartas hasta tener 4.
    
    Args:
        mano_parcial: Lista con 0-3 cartas restantes tras descarte
        baraja_disponible: Lista de cartas disponibles (se modifica in-place)
    
    Returns:
        list: Mano completa de 4 cartas (ordenada descendente)
    
    Ejemplo:
        >>> completar_mano([11, 10], baraja_disponible)
        [12, 11, 10, 7]  # Robó un 12 y un 7
    """
    n_cartas_necesarias = 4 - len(mano_parcial)
    cartas_nuevas = robar_cartas(baraja_disponible, n_cartas_necesarias)
    mano_completa = mano_parcial + cartas_nuevas
    return sorted(mano_completa, reverse=True)


def encontrar_mascara(cartas_a_descartar, mano):
    """
    Encuentra el índice de la máscara que descarta las cartas especificadas.
    
    Útil para convertir decisiones heurísticas en índices de máscara.
    
    Args:
        cartas_a_descartar: Lista de cartas a descartar
        mano: Mano original de 4 cartas
    
    Returns:
        tuple: Tupla de índices que corresponde a la máscara
    
    Ejemplo:
        >>> encontrar_mascara([12, 12], [12, 12, 11, 10])
        (0, 1)
    """
    indices = []
    mano_copia = list(mano)
    
    for carta in cartas_a_descartar:
        if carta in mano_copia:
            idx = mano_copia.index(carta)
            indices.append(idx)
            mano_copia[idx] = None  # Marcar como usada
    
    return tuple(sorted(indices))


def mascara_a_indice(mascara, todas_mascaras=None):
    """
    Convierte una máscara (tupla) a su índice en la lista de máscaras.
    
    Args:
        mascara: Tupla de índices, ej: (0, 1)
        todas_mascaras: Lista de todas las máscaras (si None, se genera)
    
    Returns:
        int: Índice de la máscara (0-14)
    
    Ejemplo:
        >>> mascara_a_indice((0,))
        0
        >>> mascara_a_indice((0, 1, 2, 3))
        14
    """
    if todas_mascaras is None:
        todas_mascaras = generar_mascaras()
    
    return todas_mascaras.index(mascara)


def indice_a_mascara(indice, todas_mascaras=None):
    """
    Convierte un índice de máscara a la tupla correspondiente.
    
    Args:
        indice: Índice entero (0-14)
        todas_mascaras: Lista de todas las máscaras (si None, se genera)
    
    Returns:
        tuple: Máscara correspondiente
    
    Ejemplo:
        >>> indice_a_mascara(0)
        (0,)
        >>> indice_a_mascara(14)
        (0, 1, 2, 3)
    """
    if todas_mascaras is None:
        todas_mascaras = generar_mascaras()
    
    return todas_mascaras[indice]


# Precalcular las 15 máscaras para uso global
MASCARAS_DESCARTE = generar_mascaras()


if __name__ == "__main__":
    # Test rápido
    print("=" * 70)
    print("TEST: Máscaras de Descarte")
    print("=" * 70)
    
    mascaras = generar_mascaras()
    print(f"\n✓ Generadas {len(mascaras)} máscaras:")
    for i, m in enumerate(mascaras):
        print(f"  [{i:2d}] {m}")
    
    print("\n" + "=" * 70)
    print("Ejemplos de aplicación:")
    print("=" * 70)
    
    mano_ejemplo = [12, 12, 11, 10]
    print(f"\nMano original: {mano_ejemplo}")
    
    # Descartar solo la primera carta
    mano_rest, desc = aplicar_mascara(mano_ejemplo, (0,))
    print(f"Máscara (0,): Quedan {mano_rest}, Descartadas {desc}")
    
    # Descartar las dos primeras
    mano_rest, desc = aplicar_mascara(mano_ejemplo, (0, 1))
    print(f"Máscara (0,1): Quedan {mano_rest}, Descartadas {desc}")
    
    # Descartar todo
    mano_rest, desc = aplicar_mascara(mano_ejemplo, (0, 1, 2, 3))
    print(f"Máscara (0,1,2,3): Quedan {mano_rest}, Descartadas {desc}")
    
    print("\n✓ Tests completados")
