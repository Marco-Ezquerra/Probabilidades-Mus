"""
Tests de validación para el evaluador de ronda completa.

Verifica:
1. Evaluación correcta de Grande
2. Evaluación correcta de Chica
3. Evaluación correcta de Pares
4. Evaluación correcta de Juego/Punto
5. Cálculo correcto de puntos por equipo
6. Reglas de puntuación (Grande/Chica: 1, Pares/Juego: suma de ambos miembros)
"""

import sys
from pathlib import Path

# Añadir paths
sys.path.insert(0, str(Path(__file__).parent.parent / "calculadora_probabilidades_mus"))

from evaluador_ronda import (
    evaluar_grande,
    evaluar_chica,
    evaluar_pares,
    evaluar_juego,
    evaluar_ronda_completa
)
from params import obtener_equipo


def test_evaluar_grande():
    """Test: Evaluación de Grande."""
    print("=" * 70)
    print("TEST 1: Evaluación de Grande")
    print("=" * 70)
    
    # Caso 1: Grande clara
    print("\nCaso 1: Grande clara")
    manos = {
        1: [12, 12, 11, 10],  # Grande más alta
        2: [7, 7, 6, 5],
        3: [11, 10, 7, 6],
        4: [6, 5, 5, 4]
    }
    ganador = evaluar_grande(manos)
    print(f"  Ganador: Posición {ganador}")
    assert ganador == 1, f"ERROR: Esperado posición 1, obtenido {ganador}"
    
    # Caso 2: Empate (gana por posición)
    print("\nCaso 2: Empate - gana la mano (posición 1)")
    manos = {
        1: [12, 11, 10, 7],
        2: [12, 11, 10, 7],  # Misma grande
        3: [11, 10, 7, 6],
        4: [10, 7, 6, 5]
    }
    ganador = evaluar_grande(manos)
    print(f"  Ganador: Posición {ganador}")
    assert ganador == 1, f"ERROR: En empate debe ganar posición 1, obtenido {ganador}"
    
    print("\n✓ Test 1 pasado")


def test_evaluar_chica():
    """Test: Evaluación de Chica."""
    print("\n" + "=" * 70)
    print("TEST 2: Evaluación de Chica")
    print("=" * 70)
    
    # Caso 1: Chica clara
    print("\nCaso 1: Chica clara (carta más baja)")
    manos = {
        1: [12, 12, 11, 10],
        2: [7, 7, 6, 5],
        3: [11, 10, 7, 6],
        4: [6, 5, 4, 4]  # Tiene 4 (más bajo)
    }
    ganador = evaluar_chica(manos)
    print(f"  Ganador: Posición {ganador}")
    assert ganador == 4, f"ERROR: Esperado posición 4, obtenido {ganador}"
    
    # Caso 2: Todas iguales (gana posición 1)
    print("\nCaso 2: Empate en chica")
    manos = {
        1: [12, 11, 10, 7],
        2: [12, 11, 10, 7],
        3: [12, 11, 10, 7],
        4: [12, 11, 10, 7]
    }
    ganador = evaluar_chica(manos)
    print(f"  Ganador: Posición {ganador}")
    assert ganador == 1, f"ERROR: En empate debe ganar posición 1, obtenido {ganador}"
    
    print("\n✓ Test 2 pasado")


def test_evaluar_pares():
    """Test: Evaluación de Pares."""
    print("\n" + "=" * 70)
    print("TEST 3: Evaluación de Pares")
    print("=" * 70)
    
    # Caso 1: Duples gana
    print("\nCaso 1: Duples vs Medias")
    manos = {
        1: [12, 12, 5, 5],  # Duples
        2: [7, 7, 7, 6],    # Medias
        3: [11, 10, 7, 6],
        4: [6, 6, 5, 4]     # Pares
    }
    ganador, tipo, val1, val2 = evaluar_pares(manos)
    print(f"  Ganador: Posición {ganador}, Tipo: {tipo}")
    assert ganador == 1, f"ERROR: Duples debería ganar"
    assert tipo == "duples", f"ERROR: Tipo debería ser duples, obtenido {tipo}"
    
    # Caso 2: Nadie tiene pares
    print("\nCaso 2: Nadie tiene pares")
    manos = {
        1: [12, 11, 10, 7],
        2: [12, 11, 7, 6],
        3: [11, 10, 7, 6],
        4: [10, 7, 6, 5]
    }
    ganador, tipo, val1, val2 = evaluar_pares(manos)
    print(f"  Ganador: {ganador}, Tipo: {tipo}")
    assert ganador is None, f"ERROR: No debería haber ganador"
    assert tipo == "sin_pares", f"ERROR: Tipo debería ser sin_pares"
    
    print("\n✓ Test 3 pasado")


def test_evaluar_juego():
    """Test: Evaluación de Juego/Punto."""
    print("\n" + "=" * 70)
    print("TEST 4: Evaluación de Juego/Punto")
    print("=" * 70)
    
    # Caso 1: Hay juego (31)
    print("\nCaso 1: Juego de 31")
    manos = {
        1: [12, 11, 10, 1],  # 31
        2: [7, 7, 7, 7],     # 28 (no juego)
        3: [12, 12, 11, 1],  # 31
        4: [10, 7, 7, 7]     # 31
    }
    ganador, es_juego, valor = evaluar_juego(manos)
    print(f"  Ganador: Posición {ganador}, Es juego: {es_juego}, Valor: {valor}")
    assert es_juego == True, f"ERROR: Debería ser juego"
    assert valor == 31, f"ERROR: Valor debería ser 31"
    assert ganador in [1, 3, 4], f"ERROR: Ganador debería tener 31"
    
    # Caso 2: Punto (nadie tiene juego)
    print("\nCaso 2: Punto (nadie llega a 31)")
    manos = {
        1: [7, 7, 7, 6],   # 27
        2: [7, 7, 6, 6],   # 26
        3: [7, 6, 6, 6],   # 25
        4: [7, 7, 7, 7]    # 28 (más cercano a 30)
    }
    ganador, es_juego, valor = evaluar_juego(manos)
    print(f"  Ganador: Posición {ganador}, Es juego: {es_juego}, Valor: {valor}")
    assert es_juego == False, f"ERROR: Debería ser punto"
    assert ganador == 4, f"ERROR: Posición 4 tiene punto más cercano a 30"
    
    print("\n✓ Test 4 pasado")


def test_puntuacion_equipos():
    """Test: Cálculo de puntos por equipo."""
    print("\n" + "=" * 70)
    print("TEST 5: Cálculo de puntos por equipo")
    print("=" * 70)
    
    # Caso 1: Equipo A gana Pares con Duples + Par
    print("\nCaso 1: Equipo A gana Pares (Duples + Par = 3+1=4 puntos)")
    manos = {
        1: [12, 12, 5, 5],  # Duples (3 puntos)
        2: [7, 7, 7, 6],    # Medias (2 puntos)
        3: [11, 11, 10, 7], # Pares (1 punto)
        4: [6, 5, 5, 4]     # Pares (1 punto)
    }
    resultado = evaluar_ronda_completa(manos, verbose=False)
    
    puntos_pares = resultado["desglose"]["pares"]["puntos"]
    equipo_ganador = resultado["desglose"]["pares"]["ganador_equipo"]
    
    print(f"  Equipo ganador: {equipo_ganador}")
    print(f"  Puntos por Pares: {puntos_pares}")
    print(f"  J1 (Duples): 3 puntos + J3 (Pares): 1 punto = 4 puntos")
    
    assert equipo_ganador == "A", f"ERROR: Equipo A debería ganar (Duples > Medias)"
    assert puntos_pares == 4, f"ERROR: Debería sumar 3+1=4 puntos, obtenido {puntos_pares}"
    
    # Caso 2: Grande y Chica suman 1 punto cada una
    print("\nCaso 2: Grande y Chica valen 1 punto fijo")
    puntos_grande = resultado["desglose"]["grande"]["puntos"]
    puntos_chica = resultado["desglose"]["chica"]["puntos"]
    
    print(f"  Grande: {puntos_grande} punto")
    print(f"  Chica: {puntos_chica} punto")
    
    assert puntos_grande == 1, f"ERROR: Grande debería valer 1 punto"
    assert puntos_chica == 1, f"ERROR: Chica debería valer 1 punto"
    
    print("\n✓ Test 5 pasado")


def test_caso_completo():
    """Test: Caso completo con verificación de diferencial."""
    print("\n" + "=" * 70)
    print("TEST 6: Caso completo con diferencial")
    print("=" * 70)
    
    print("\nEscenario: Equipo A domina")
    manos = {
        1: [12, 12, 11, 10],  # Duples + Juego 31
        2: [7, 7, 6, 5],      # Pares
        3: [12, 11, 10, 1],   # Juego 31
        4: [6, 5, 5, 4]       # Pares
    }
    
    resultado = evaluar_ronda_completa(manos, verbose=True)
    
    print(f"\n📊 Resumen:")
    print(f"  Equipo A: {resultado['Equipo_A']} puntos")
    print(f"  Equipo B: {resultado['Equipo_B']} puntos")
    print(f"  Diferencial: {resultado['Diferencial']:+d}")
    
    # Verificar que Equipo A gana
    assert resultado["Diferencial"] > 0, "ERROR: Equipo A debería tener diferencial positivo"
    
    print("\n✓ Test 6 pasado")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("🚀 INICIANDO TESTS DEL EVALUADOR DE RONDA")
    print("=" * 70)
    
    test_evaluar_grande()
    test_evaluar_chica()
    test_evaluar_pares()
    test_evaluar_juego()
    test_puntuacion_equipos()
    test_caso_completo()
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
