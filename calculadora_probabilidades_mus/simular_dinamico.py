"""
Simulador Dinámico de Probabilidades de Mus
Calcula probabilidades condicionadas cuando conoces tu mano y la de tu compañero.
"""

import random
from calculadoramus import (
    inicializar_baraja,
    clasificar_pares,
    comparar_pares,
    comparar_grande_chica,
    calcular_valor_juego,
    convertir_valor_juego,
    comparar_juego,
    calcular_valor_punto,
    comparar_punto
)


# ============================================================================
# VALIDACIÓN
# ============================================================================

def validar_manos(mano_jugador, mano_companero, baraja):
    """
    Valida que las manos del jugador y compañero sean correctas.
    
    Args:
        mano_jugador: Lista de 4 cartas
        mano_companero: Lista de 4 cartas
        baraja: Baraja completa para validar disponibilidad
    
    Returns:
        (True, None) si es válido
        (False, mensaje_error) si hay algún problema
    """
    # Verificar que son listas de 4 cartas
    if not isinstance(mano_jugador, list) or len(mano_jugador) != 4:
        return False, "La mano del jugador debe tener exactamente 4 cartas"
    
    if not isinstance(mano_companero, list) or len(mano_companero) != 4:
        return False, "La mano del compañero debe tener exactamente 4 cartas"
    
    # Combinar todas las cartas seleccionadas
    todas_cartas = mano_jugador + mano_companero
    
    # Contar ocurrencias en las manos seleccionadas
    conteo_seleccionadas = {}
    for carta in todas_cartas:
        conteo_seleccionadas[carta] = conteo_seleccionadas.get(carta, 0) + 1
    
    # Contar disponibilidad en la baraja
    conteo_baraja = {}
    for carta in baraja:
        conteo_baraja[carta] = conteo_baraja.get(carta, 0) + 1
    
    # Verificar que cada carta seleccionada existe en la baraja en cantidad suficiente
    for carta, cantidad in conteo_seleccionadas.items():
        if carta not in conteo_baraja:
            return False, f"La carta {carta} no existe en esta baraja"
        if cantidad > conteo_baraja[carta]:
            return False, f"No hay suficientes cartas {carta} (necesitas {cantidad}, hay {conteo_baraja[carta]})"
    
    return True, None


# ============================================================================
# SIMULACIÓN CON COMPAÑERO
# ============================================================================

def simular_con_companero(mano_jugador, mano_companero, baraja, iteraciones=50000):
    """
    Simula probabilidades de victoria conociendo tu mano y la de tu compañero.
    
    Args:
        mano_jugador: Lista de 4 cartas del jugador
        mano_companero: Lista de 4 cartas del compañero
        baraja: Baraja completa (40 cartas)
        iteraciones: Número de simulaciones (default: 50,000)
    
    Returns:
        Diccionario con:
        - probabilidad_grande
        - probabilidad_chica
        - probabilidad_pares
        - probabilidad_juego
        - iteraciones_realizadas
        - cartas_disponibles (para info)
    """
    # Validar manos
    valido, mensaje = validar_manos(mano_jugador, mano_companero, baraja)
    if not valido:
        raise ValueError(f"Error de validación: {mensaje}")
    
    # Preparar baraja sin las 8 cartas conocidas
    baraja_disponible = baraja.copy()
    for carta in mano_jugador:
        baraja_disponible.remove(carta)
    for carta in mano_companero:
        baraja_disponible.remove(carta)
    
    # Contadores de victorias
    victorias = {"grande": 0, "chica": 0, "pares": 0, "juego": 0}
    es_mano = True
    
    for _ in range(iteraciones):
        # Repartir dos manos aleatorias a los oponentes
        baraja_temp = baraja_disponible.copy()
        mano1 = random.sample(baraja_temp, 4)
        for carta in mano1:
            baraja_temp.remove(carta)
        mano2 = random.sample(baraja_temp, 4)
        
        # GRANDE: comparar con mayor a menor
        mano_grande = sorted(mano_jugador, reverse=True)
        mano1_grande = sorted(mano1, reverse=True)
        mano2_grande = sorted(mano2, reverse=True)
        
        if (comparar_grande_chica(mano_grande, mano1_grande, es_mano) > 0 and
            comparar_grande_chica(mano_grande, mano2_grande, es_mano) > 0):
            victorias["grande"] += 1
        
        # CHICA: comparar con menor a mayor
        mano_chica = sorted(mano_jugador)
        mano1_chica = sorted(mano1)
        mano2_chica = sorted(mano2)
        
        if (comparar_grande_chica(mano_chica, mano1_chica, es_mano) < 0 and
            comparar_grande_chica(mano_chica, mano2_chica, es_mano) < 0):
            victorias["chica"] += 1
        
        # PARES
        tipo_mano, val1, val2 = clasificar_pares(mano_jugador)
        tipo_mano1, val1_m1, val2_m1 = clasificar_pares(mano1)
        tipo_mano2, val1_m2, val2_m2 = clasificar_pares(mano2)
        
        if (comparar_pares(tipo_mano, val1, val2, tipo_mano1, val1_m1, val2_m1, es_mano) > 0 and
            comparar_pares(tipo_mano, val1, val2, tipo_mano2, val1_m2, val2_m2, es_mano) > 0):
            victorias["pares"] += 1
        
        # JUEGO o PUNTO
        valor_juego = convertir_valor_juego(calcular_valor_juego(mano_jugador))
        valor_juego1 = convertir_valor_juego(calcular_valor_juego(mano1))
        valor_juego2 = convertir_valor_juego(calcular_valor_juego(mano2))
        
        if valor_juego > 0 or valor_juego1 > 0 or valor_juego2 > 0:
            # Hay juego
            if (comparar_juego(valor_juego, valor_juego1, es_mano) > 0 and
                comparar_juego(valor_juego, valor_juego2, es_mano) > 0):
                victorias["juego"] += 1
        else:
            # Se compara por punto
            punto = calcular_valor_punto(mano_jugador)
            punto1 = calcular_valor_punto(mano1)
            punto2 = calcular_valor_punto(mano2)
            
            if (comparar_punto(punto, punto1, es_mano) > 0 and
                comparar_punto(punto, punto2, es_mano) > 0):
                victorias["juego"] += 1
    
    # Calcular probabilidades
    return {
        "probabilidad_grande": victorias["grande"] / iteraciones,
        "probabilidad_chica": victorias["chica"] / iteraciones,
        "probabilidad_pares": victorias["pares"] / iteraciones,
        "probabilidad_juego": victorias["juego"] / iteraciones,
        "iteraciones_realizadas": iteraciones,
        "cartas_disponibles": len(baraja_disponible)
    }


# ============================================================================
# FORMATEO DE RESULTADOS
# ============================================================================

def formatear_resultado_legible(mano_jugador, mano_companero, probabilidades):
    """
    Formatea los resultados de la simulación de forma legible.
    
    Args:
        mano_jugador: Lista de 4 cartas
        mano_companero: Lista de 4 cartas
        probabilidades: Diccionario retornado por simular_con_companero()
    
    Returns:
        String formateado con los resultados
    """
    tipo_pares, _, _ = clasificar_pares(mano_jugador)
    valor_juego_raw = calcular_valor_juego(mano_jugador)
    valor_juego = convertir_valor_juego(valor_juego_raw)
    valor_punto = calcular_valor_punto(mano_jugador)
    
    resultado = []
    resultado.append("=" * 70)
    resultado.append(" SIMULACIÓN DINÁMICA - PROBABILIDADES CON COMPAÑERO")
    resultado.append("=" * 70)
    resultado.append("")
    resultado.append(f"Tu mano:          {sorted(mano_jugador, reverse=True)}")
    resultado.append(f"Mano compañero:   {sorted(mano_companero, reverse=True)}")
    resultado.append(f"Cartas conocidas: 8 / 40")
    resultado.append(f"Cartas disponibles para oponentes: {probabilidades['cartas_disponibles']}")
    resultado.append("")
    resultado.append("-" * 70)
    resultado.append(" ANÁLISIS DE TU MANO")
    resultado.append("-" * 70)
    resultado.append(f"  Pares:  {tipo_pares}")
    resultado.append(f"  Juego:  {'Sí' if valor_juego > 0 else 'No'} (valor: {valor_juego_raw})")
    resultado.append(f"  Punto:  {valor_punto}")
    resultado.append("")
    resultado.append("-" * 70)
    resultado.append(" PROBABILIDADES DE VICTORIA (vs 2 oponentes)")
    resultado.append("-" * 70)
    resultado.append(f"  GRANDE:  {probabilidades['probabilidad_grande']:.2%}")
    resultado.append(f"  CHICA:   {probabilidades['probabilidad_chica']:.2%}")
    resultado.append(f"  PARES:   {probabilidades['probabilidad_pares']:.2%}")
    resultado.append(f"  JUEGO:   {probabilidades['probabilidad_juego']:.2%}")
    resultado.append("")
    resultado.append(f"Iteraciones: {probabilidades['iteraciones_realizadas']:,}")
    resultado.append("=" * 70)
    resultado.append("")
    resultado.append("Nota: Estas son probabilidades CONDICIONADAS (a posteriori)")
    resultado.append("      dado que conoces 8 cartas. Son distintas a las")
    resultado.append("      estadísticas estáticas precalculadas (a priori).")
    resultado.append("")
    
    return "\n".join(resultado)


# ============================================================================
# FUNCIÓN DE EJEMPLO/TESTING
# ============================================================================

def ejemplo_uso():
    """
    Función de ejemplo que muestra cómo usar el simulador dinámico.
    Esta función se usará para testing y documentación.
    """
    print("\n" + "=" * 70)
    print(" EJEMPLO DE USO - SIMULADOR DINÁMICO")
    print("=" * 70)
    print("\nEste módulo será integrado en la futura interfaz gráfica.")
    print("Por ahora, puedes usarlo importándolo desde Python:\n")
    
    # Ejemplo 1: Caso muy favorable
    print("-" * 70)
    print("EJEMPLO 1: Caso muy favorable")
    print("-" * 70)
    baraja = inicializar_baraja(modo_8_reyes=False)
    mano_jugador = [12, 12, 11, 10]
    mano_companero = [1, 1, 1, 1]
    
    print(f"Tu mano:        {mano_jugador}")
    print(f"Compañero:      {mano_companero}")
    print("\nSimulando...")
    
    resultado = simular_con_companero(mano_jugador, mano_companero, baraja, iteraciones=50000)
    print(formatear_resultado_legible(mano_jugador, mano_companero, resultado))
    
    # Ejemplo 2: Caso intermedio
    print("\n" + "-" * 70)
    print("EJEMPLO 2: Caso intermedio")
    print("-" * 70)
    mano_jugador = [7, 7, 6, 6]
    mano_companero = [5, 4, 4, 2]
    
    print(f"Tu mano:        {mano_jugador}")
    print(f"Compañero:      {mano_companero}")
    print("\nSimulando...")
    
    resultado = simular_con_companero(mano_jugador, mano_companero, baraja, iteraciones=50000)
    print(formatear_resultado_legible(mano_jugador, mano_companero, resultado))


if __name__ == "__main__":
    # Ejecutar ejemplos de uso
    ejemplo_uso()
