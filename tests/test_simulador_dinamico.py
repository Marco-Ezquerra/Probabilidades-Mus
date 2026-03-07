"""
Tests básicos para el simulador dinámico
Valida casos edge y comportamiento esperado
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'calculadora_probabilidades_mus'))

from simular_dinamico import simular_con_companero, validar_manos, formatear_resultado_legible
from calculadoramus import inicializar_baraja


def test_validacion():
    """Tests de validación de manos."""
    print("=" * 70)
    print("TEST 1: VALIDACIÓN DE MANOS")
    print("=" * 70)
    
    baraja = inicializar_baraja(modo_8_reyes=False)
    
    # Caso 1: Manos válidas
    valido, error = validar_manos([1,1,1,1], [12,12,12,12], baraja)
    assert valido == True, "Debería ser válido"
    print("✓ Manos válidas: OK")
    
    # Caso 2: Demasiadas cartas en mano del jugador
    valido, error = validar_manos([1,1,1,1,1], [12,12,12,12], baraja)
    assert valido == False, "No debería ser válido (5 cartas)"
    print("✓ Rechazo de 5 cartas: OK")
    
    # Caso 3: Demasiadas cartas iguales (imposible tener 5 doses cuando solo hay 4)
    valido, error = validar_manos([1,1,1,1], [1,1,1,1,1], baraja)
    assert valido == False, "No debería ser válido (lista con 5 elementos)"
    print("✓ Rechazo de mano con 5 elementos: OK")
    
    # Caso 4: Carta inexistente (el 8 y 9 no existen en ningún modo)
    # Primero verificar con carta que sabemos que no existe
    valido, error = validar_manos([8,8,8,8], [12,12,12,12], baraja)
    assert valido == False, "No debería ser válido (carta 8 no existe)"
    print("✓ Rechazo de carta inexistente: OK")
    
    print("\n✅ Todos los tests de validación pasaron\n")


def test_probabilidades_extremas():
    """Tests de casos extremos con probabilidades esperadas."""
    print("=" * 70)
    print("TEST 2: PROBABILIDADES EXTREMAS")
    print("=" * 70)
    
    baraja = inicializar_baraja(modo_8_reyes=False)
    
    # Caso 1: Mejor mano posible para GRANDE y JUEGO
    print("\nCaso 1: Mano perfecta para GRANDE y JUEGO")
    print("  Tu mano: [12,12,11,10] - Pares de reyes + Juego 40")
    print("  Compañero: [7,6,5,4]")
    
    resultado = simular_con_companero([12,12,11,10], [7,6,5,4], baraja, iteraciones=10000)
    
    assert resultado['probabilidad_grande'] > 0.90, "Debería ganar GRANDE casi siempre"
    assert resultado['probabilidad_juego'] > 0.85, "Debería ganar JUEGO casi siempre (40 es el mejor)"
    print(f"  GRANDE: {resultado['probabilidad_grande']:.2%} ✓")
    print(f"  JUEGO:  {resultado['probabilidad_juego']:.2%} ✓")
    
    # Caso 2: Mano muy baja (debería tener probabilidades muy bajas en GRANDE)
    print("\nCaso 2: Mano baja")
    print("  Tu mano: [4,4,5,5]")
    print("  Compañero: [6,6,7,7]")
    
    resultado = simular_con_companero([4,4,5,5], [6,6,7,7], baraja, iteraciones=10000)
    
    assert resultado['probabilidad_grande'] < 0.10, "No debería ganar GRANDE casi nunca"
    print(f"  GRANDE: {resultado['probabilidad_grande']:.2%} ✓")
    
    # Caso 3: Duples perfectas
    print("\nCaso 3: Duples de reyes")
    print("  Tu mano: [12,12,12,12]")
    print("  Compañero: [1,1,2,3]")
    
    resultado = simular_con_companero([12,12,12,12], [1,1,2,3], baraja, iteraciones=10000)
    
    assert resultado['probabilidad_pares'] > 0.95, "Duples de reyes deberían ganar PARES casi siempre"
    print(f"  PARES:  {resultado['probabilidad_pares']:.2%} ✓")
    
    print("\n✅ Todos los tests de probabilidades extremas pasaron\n")


def test_modo_8_reyes():
    """Test con modo 8 reyes."""
    print("=" * 70)
    print("TEST 3: MODO 8 REYES")
    print("=" * 70)
    
    baraja = inicializar_baraja(modo_8_reyes=True)
    
    print("\nModo 8 reyes: más reyes disponibles")
    print("  Tu mano: [1,1,1,1]")
    print("  Compañero: [12,12,12,12]")
    
    resultado = simular_con_companero([1,1,1,1], [12,12,12,12], baraja, iteraciones=10000)
    
    assert resultado['cartas_disponibles'] == 32, "Deberían quedar 32 cartas disponibles"
    print(f"  Cartas disponibles: {resultado['cartas_disponibles']} ✓")
    print(f"  GRANDE: {resultado['probabilidad_grande']:.2%}")
    print(f"  CHICA:  {resultado['probabilidad_chica']:.2%}")
    print(f"  PARES:  {resultado['probabilidad_pares']:.2%}")
    
    print("\n✅ Test de modo 8 reyes pasado\n")


def test_formateo():
    """Test de formateo de resultados."""
    print("=" * 70)
    print("TEST 4: FORMATEO DE RESULTADOS")
    print("=" * 70)
    
    baraja = inicializar_baraja(modo_8_reyes=False)
    resultado = simular_con_companero([7,7,6,6], [5,4,4,2], baraja, iteraciones=5000)
    
    texto = formatear_resultado_legible([7,7,6,6], [5,4,4,2], resultado)
    
    assert "SIMULACIÓN DINÁMICA" in texto, "Debería tener el título"
    assert "GRANDE" in texto, "Debería mostrar GRANDE"
    assert "CHICA" in texto, "Debería mostrar CHICA"
    assert "PARES" in texto, "Debería mostrar PARES"
    assert "JUEGO" in texto, "Debería mostrar JUEGO"
    assert "5,000" in texto or "5000" in texto, "Debería mostrar iteraciones"
    
    print("✓ Formato contiene todos los elementos necesarios")
    print("\n✅ Test de formateo pasado\n")


def ejecutar_todos_tests():
    """Ejecuta todos los tests."""
    print("\n" + "=" * 70)
    print(" SUITE DE TESTS - SIMULADOR DINÁMICO")
    print("=" * 70 + "\n")
    
    try:
        test_validacion()
        test_probabilidades_extremas()
        test_modo_8_reyes()
        test_formateo()
        
        print("=" * 70)
        print(" ✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)
        print("\nEl simulador dinámico está funcionando correctamente.")
        print("Listo para integración en la interfaz gráfica.\n")
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print(" ❌ ERROR EN LOS TESTS")
        print("=" * 70)
        print(f"\n{e}\n")
        raise


if __name__ == "__main__":
    ejecutar_todos_tests()
