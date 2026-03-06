"""
Evaluador de ronda completa en el Mus.

Evalúa los 4 lances (Grande, Chica, Pares, Juego/Punto) con 4 manos
y calcula los puntos reales obtenidos por cada equipo según las reglas:

- Grande y Chica: 1 punto para el equipo ganador
- Pares: Suma de los valores base de AMBOS miembros del equipo ganador
- Juego: Suma de los valores base de AMBOS miembros del equipo ganador
- Punto: 1 punto para el equipo ganador (cuando nadie tiene juego)

Resuelve empates estrictamente por posición: 1 > 2 > 3 > 4
"""

import sys
from pathlib import Path

# Añadir paths para imports
sys.path.insert(0, str(Path(__file__).parent))

from calculadoramus import (
    clasificar_pares,
    comparar_pares,
    comparar_grande_chica,
    calcular_valor_juego,
    comparar_juego,
    calcular_valor_punto,
    comparar_punto
)
from params import (
    VALORES_PUNTOS_PARES,
    VALORES_PUNTOS_JUEGO,
    PUNTOS_GRANDE,
    PUNTOS_CHICA,
    PUNTOS_PUNTO,
    obtener_equipo,
    obtener_companero
)


def evaluar_grande(manos, posiciones=[1, 2, 3, 4]):
    """
    Evalúa el lance de Grande.
    
    Args:
        manos: Dict {posicion: mano} con las 4 manos
        posiciones: Lista de posiciones en orden [1, 2, 3, 4]
    
    Returns:
        int: Posición del ganador (1-4)
    """
    ganador = posiciones[0]
    
    for pos in posiciones[1:]:
        # comparar_grande_chica devuelve 1 si mano1 gana, -1 si pierde
        # En empate, el parámetro es_mano (True) hace que gane el primero
        resultado = comparar_grande_chica(manos[ganador], manos[pos], es_mano=True)
        if resultado == -1:  # El retador gana
            ganador = pos
    
    return ganador


def evaluar_chica(manos, posiciones=[1, 2, 3, 4]):
    """
    Evalúa el lance de Chica.
    
    Args:
        manos: Dict {posicion: mano} con las 4 manos
        posiciones: Lista de posiciones en orden [1, 2, 3, 4]
    
    Returns:
        int: Posición del ganador (1-4)
    """
    ganador = posiciones[0]
    
    for pos in posiciones[1:]:
        # Para chica, queremos la mano más baja
        # Verificar si las manos son iguales
        if manos[ganador] == manos[pos]:
            # Empate: gana la posición menor
            if pos < ganador:
                ganador = pos
        else:
            # No empate: comparar valores
            resultado = comparar_grande_chica(manos[ganador], manos[pos], es_mano=True)
            if resultado == 1:  # mano[ganador] es MAYOR -> mano[pos] es mejor para chica
                ganador = pos
    
    return ganador


def evaluar_pares(manos, posiciones=[1, 2, 3, 4]):
    """
    Evalúa el lance de Pares.
    
    Args:
        manos: Dict {posicion: mano} con las 4 manos
        posiciones: Lista de posiciones en orden [1, 2, 3, 4]
    
    Returns:
        tuple: (posicion_ganador, tipo_ganador, valor1_ganador, valor2_ganador)
               Si nadie tiene pares, retorna (None, "sin_pares", 0, 0)
    """
    # Clasificar pares de todas las manos
    clasificaciones = {}
    for pos in posiciones:
        tipo, val1, val2 = clasificar_pares(manos[pos])
        clasificaciones[pos] = (tipo, val1, val2)
    
    # Encontrar el mejor
    ganador = None
    mejor_tipo, mejor_val1, mejor_val2 = "sin_pares", 0, 0
    
    for pos in posiciones:
        tipo, val1, val2 = clasificaciones[pos]
        
        # Si nadie tiene pares aún, este es el primero
        if mejor_tipo == "sin_pares":
            if tipo != "sin_pares":
                ganador = pos
                mejor_tipo, mejor_val1, mejor_val2 = tipo, val1, val2
        else:
            # Comparar con el actual ganador
            if tipo != "sin_pares":
                resultado = comparar_pares(
                    mejor_tipo, mejor_val1, mejor_val2,
                    tipo, val1, val2,
                    es_mano=True  # En empate, gana la posición menor
                )
                if resultado == -1:  # El retador gana
                    ganador = pos
                    mejor_tipo, mejor_val1, mejor_val2 = tipo, val1, val2
    
    return ganador, mejor_tipo, mejor_val1, mejor_val2


def evaluar_juego(manos, posiciones=[1, 2, 3, 4]):
    """
    Evalúa el lance de Juego o Punto.
    
    Si al menos uno tiene juego (≥31), se juega Juego.
    Si nadie tiene juego, se juega Punto (más cercano a 30).
    
    Args:
        manos: Dict {posicion: mano} con las 4 manos
        posiciones: Lista de posiciones en orden [1, 2, 3, 4]
    
    Returns:
        tuple: (posicion_ganador, es_juego, valor)
               - es_juego: True si hay juego, False si es punto
               - valor: valor de juego (31-40) o punto (4-36)
    """
    # Calcular valores de juego para todos
    valores_juego = {}
    for pos in posiciones:
        valores_juego[pos] = calcular_valor_juego(manos[pos])
    
    # ¿Alguien tiene juego?
    hay_juego = any(v >= 31 for v in valores_juego.values())
    
    if hay_juego:
        # Juego: buscar el mejor valor ≥ 31
        ganador = None
        mejor_valor = 0
        
        for pos in posiciones:
            if valores_juego[pos] >= 31:
                if ganador is None:
                    ganador = pos
                    mejor_valor = valores_juego[pos]
                else:
                    resultado = comparar_juego(mejor_valor, valores_juego[pos], es_mano=True)
                    if resultado == -1:  # El retador gana
                        ganador = pos
                        mejor_valor = valores_juego[pos]
        
        return ganador, True, mejor_valor
    
    else:
        # Punto: buscar el más cercano a 30
        ganador = posiciones[0]
        mejor_punto = calcular_valor_punto(manos[posiciones[0]])
        
        for pos in posiciones[1:]:
            punto_actual = calcular_valor_punto(manos[pos])
            resultado = comparar_punto(mejor_punto, punto_actual, es_mano=True)
            if resultado == -1:  # El retador gana
                ganador = pos
                mejor_punto = punto_actual
        
        return ganador, False, mejor_punto


def calcular_puntos_equipos(resultados_lances, manos):
    """
    Calcula los puntos obtenidos por cada equipo en una ronda completa.
    
    Reglas de puntuación:
    - Grande: 1 punto para el equipo ganador
    - Chica: 1 punto para el equipo ganador
    - Pares: Suma de los valores base de AMBOS miembros del equipo ganador
    - Juego: Suma de los valores base de AMBOS miembros del equipo ganador
    - Punto: 1 punto para el equipo ganador
    
    Args:
        resultados_lances: Dict con resultados de evaluar_*
        manos: Dict {posicion: mano} con las 4 manos
    
    Returns:
        dict: {
            "Equipo_A": int,
            "Equipo_B": int,
            "Diferencial": int (A - B),
            "desglose": {...}
        }
    """
    puntos = {"A": 0, "B": 0}
    desglose = {
        "grande": {"ganador_pos": None, "ganador_equipo": None, "puntos": 0},
        "chica": {"ganador_pos": None, "ganador_equipo": None, "puntos": 0},
        "pares": {"ganador_pos": None, "ganador_equipo": None, "puntos": 0, "tipo": None},
        "juego": {"ganador_pos": None, "ganador_equipo": None, "puntos": 0, "es_juego": False}
    }
    
    # GRANDE
    pos_ganador = resultados_lances["grande"]
    equipo_ganador = obtener_equipo(pos_ganador)
    puntos[equipo_ganador] += PUNTOS_GRANDE
    desglose["grande"] = {
        "ganador_pos": pos_ganador,
        "ganador_equipo": equipo_ganador,
        "puntos": PUNTOS_GRANDE
    }
    
    # CHICA
    pos_ganador = resultados_lances["chica"]
    equipo_ganador = obtener_equipo(pos_ganador)
    puntos[equipo_ganador] += PUNTOS_CHICA
    desglose["chica"] = {
        "ganador_pos": pos_ganador,
        "ganador_equipo": equipo_ganador,
        "puntos": PUNTOS_CHICA
    }
    
    # PARES
    pos_ganador, tipo_pares, val1, val2 = resultados_lances["pares"]
    if pos_ganador is not None:  # Alguien tiene pares
        equipo_ganador = obtener_equipo(pos_ganador)
        companero = obtener_companero(pos_ganador)
        
        # Calcular puntos de AMBOS miembros del equipo
        tipo_ganador, _, _ = clasificar_pares(manos[pos_ganador])
        tipo_companero, _, _ = clasificar_pares(manos[companero])
        
        puntos_ganador = VALORES_PUNTOS_PARES[tipo_ganador]
        puntos_companero = VALORES_PUNTOS_PARES[tipo_companero]
        puntos_totales = puntos_ganador + puntos_companero
        
        puntos[equipo_ganador] += puntos_totales
        desglose["pares"] = {
            "ganador_pos": pos_ganador,
            "ganador_equipo": equipo_ganador,
            "puntos": puntos_totales,
            "tipo": tipo_pares,
            "puntos_ganador": puntos_ganador,
            "puntos_companero": puntos_companero
        }
    
    # JUEGO / PUNTO
    pos_ganador, es_juego, valor = resultados_lances["juego"]
    equipo_ganador = obtener_equipo(pos_ganador)
    companero = obtener_companero(pos_ganador)
    
    if es_juego:
        # Calcular puntos de AMBOS miembros del equipo
        juego_ganador = calcular_valor_juego(manos[pos_ganador])
        juego_companero = calcular_valor_juego(manos[companero])
        
        puntos_ganador = VALORES_PUNTOS_JUEGO.get(juego_ganador, 0)
        puntos_companero = VALORES_PUNTOS_JUEGO.get(juego_companero, 0)
        puntos_totales = puntos_ganador + puntos_companero
        
        puntos[equipo_ganador] += puntos_totales
        desglose["juego"] = {
            "ganador_pos": pos_ganador,
            "ganador_equipo": equipo_ganador,
            "puntos": puntos_totales,
            "es_juego": True,
            "valor": valor,
            "puntos_ganador": puntos_ganador,
            "puntos_companero": puntos_companero
        }
    else:
        # Punto: 1 punto fijo
        puntos[equipo_ganador] += PUNTOS_PUNTO
        desglose["juego"] = {
            "ganador_pos": pos_ganador,
            "ganador_equipo": equipo_ganador,
            "puntos": PUNTOS_PUNTO,
            "es_juego": False,
            "valor": valor
        }
    
    return {
        "Equipo_A": puntos["A"],
        "Equipo_B": puntos["B"],
        "Diferencial": puntos["A"] - puntos["B"],
        "desglose": desglose
    }


def evaluar_ronda_rapida(manos):
    """
    Versión optimizada de evaluar_ronda_completa que solo devuelve el diferencial.
    Evita crear dicts intermedios para máxima velocidad en rollouts.
    
    Args:
        manos: Dict {posicion: mano} con las 4 manos
    
    Returns:
        int: Diferencial Equipo_A - Equipo_B
    """
    posiciones = [1, 2, 3, 4]
    # Mapeo rápido posición->equipo: 1,3 -> A (+1), 2,4 -> B (-1)
    _EQUIPO_SIGNO = {1: 1, 2: -1, 3: 1, 4: -1}
    _COMPANERO = {1: 3, 2: 4, 3: 1, 4: 2}
    
    diferencial = 0
    
    # GRANDE
    ganador = evaluar_grande(manos, posiciones)
    diferencial += _EQUIPO_SIGNO[ganador] * PUNTOS_GRANDE
    
    # CHICA
    ganador = evaluar_chica(manos, posiciones)
    diferencial += _EQUIPO_SIGNO[ganador] * PUNTOS_CHICA
    
    # PARES
    pos_ganador, tipo_pares, val1, val2 = evaluar_pares(manos, posiciones)
    if pos_ganador is not None:
        companero = _COMPANERO[pos_ganador]
        tipo_ganador, _, _ = clasificar_pares(manos[pos_ganador])
        tipo_companero, _, _ = clasificar_pares(manos[companero])
        puntos_totales = VALORES_PUNTOS_PARES[tipo_ganador] + VALORES_PUNTOS_PARES[tipo_companero]
        diferencial += _EQUIPO_SIGNO[pos_ganador] * puntos_totales
    
    # JUEGO / PUNTO
    pos_ganador, es_juego, valor = evaluar_juego(manos, posiciones)
    if es_juego:
        companero = _COMPANERO[pos_ganador]
        juego_ganador = calcular_valor_juego(manos[pos_ganador])
        juego_companero = calcular_valor_juego(manos[companero])
        puntos_g = VALORES_PUNTOS_JUEGO.get(juego_ganador, 0)
        puntos_c = VALORES_PUNTOS_JUEGO.get(juego_companero, 0)
        diferencial += _EQUIPO_SIGNO[pos_ganador] * (puntos_g + puntos_c)
    else:
        diferencial += _EQUIPO_SIGNO[pos_ganador] * PUNTOS_PUNTO
    
    return diferencial


def evaluar_ronda_completa(manos, verbose=False):
    """
    Evalúa una ronda completa con los 4 lances y calcula puntos por equipo.
    
    Args:
        manos: Dict {posicion: mano} donde posicion es 1-4 y mano es lista de 4 cartas
        verbose: Si True, imprime detalles
    
    Returns:
        dict: Resultado completo con puntos y desglose por lance
    
    Ejemplo:
        >>> manos = {
        ...     1: [12, 12, 11, 10],
        ...     2: [7, 7, 6, 5],
        ...     3: [12, 11, 10, 1],
        ...     4: [6, 5, 5, 4]
        ... }
        >>> resultado = evaluar_ronda_completa(manos)
        >>> print(resultado["Equipo_A"], resultado["Equipo_B"])
    """
    posiciones = [1, 2, 3, 4]
    
    # Evaluar los 4 lances
    ganador_grande = evaluar_grande(manos, posiciones)
    ganador_chica = evaluar_chica(manos, posiciones)
    resultado_pares = evaluar_pares(manos, posiciones)
    resultado_juego = evaluar_juego(manos, posiciones)
    
    resultados_lances = {
        "grande": ganador_grande,
        "chica": ganador_chica,
        "pares": resultado_pares,
        "juego": resultado_juego
    }
    
    # Calcular puntos
    puntos = calcular_puntos_equipos(resultados_lances, manos)
    
    if verbose:
        print("=" * 70)
        print("EVALUACIÓN DE RONDA COMPLETA")
        print("=" * 70)
        for pos in posiciones:
            equipo = obtener_equipo(pos)
            print(f"Posición {pos} (Equipo {equipo}): {manos[pos]}")
        
        print("\n📊 RESULTADOS DE LANCES:")
        print(f"  Grande: Posición {ganador_grande} (Equipo {obtener_equipo(ganador_grande)}) +{puntos['desglose']['grande']['puntos']}")
        print(f"  Chica:  Posición {ganador_chica} (Equipo {obtener_equipo(ganador_chica)}) +{puntos['desglose']['chica']['puntos']}")
        
        if resultado_pares[0] is not None:
            print(f"  Pares:  Posición {resultado_pares[0]} ({resultado_pares[1]}) (Equipo {obtener_equipo(resultado_pares[0])}) +{puntos['desglose']['pares']['puntos']}")
        else:
            print(f"  Pares:  Nadie tiene pares")
        
        if resultado_juego[1]:  # es_juego
            print(f"  Juego:  Posición {resultado_juego[0]} (Juego {resultado_juego[2]}) (Equipo {obtener_equipo(resultado_juego[0])}) +{puntos['desglose']['juego']['puntos']}")
        else:
            print(f"  Punto:  Posición {resultado_juego[0]} (Punto {resultado_juego[2]}) (Equipo {obtener_equipo(resultado_juego[0])}) +{puntos['desglose']['juego']['puntos']}")
        
        print("\n🏆 PUNTUACIÓN FINAL:")
        print(f"  Equipo A: {puntos['Equipo_A']} puntos")
        print(f"  Equipo B: {puntos['Equipo_B']} puntos")
        print(f"  Diferencial: {puntos['Diferencial']:+d}")
    
    return puntos


if __name__ == "__main__":
    print("=" * 70)
    print("TEST: Evaluador de Ronda Completa")
    print("=" * 70)
    
    # Caso 1: Equipo A domina
    print("\n🎴 CASO 1: Equipo A con ventaja clara")
    manos_1 = {
        1: [12, 12, 11, 10],  # Duples + Juego 31
        2: [7, 7, 6, 5],      # Pares de 7
        3: [12, 11, 10, 1],   # Juego 31
        4: [6, 5, 5, 4]       # Pares de 5
    }
    resultado_1 = evaluar_ronda_completa(manos_1, verbose=True)
    
    # Caso 2: Lances distribuidos
    print("\n" + "=" * 70)
    print("\n🎴 CASO 2: Lances distribuidos")
    manos_2 = {
        1: [12, 11, 7, 6],    # Sin pares, sin juego
        2: [12, 12, 12, 10],  # Medias de Rey + Juego 31
        3: [11, 10, 7, 6],    # Sin pares, sin juego
        4: [1, 1, 1, 1]       # Duples de As
    }
    resultado_2 = evaluar_ronda_completa(manos_2, verbose=True)
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
