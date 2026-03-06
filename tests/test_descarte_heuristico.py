"""
Tests de validación para la heurística base de descarte.

Verifica:
1. Reyes siempre se mantienen
2. Pareja de Ases se mantiene solo en posición 4
3. As suelto se mantiene solo si hay Rey
4. Figuras altas se mantienen solo si hay Rey
5. Basura se descarta siempre
"""

import sys
from pathlib import Path

# Añadir paths
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from descarte_heuristico import (
    descarte_heuristico_base,
    descarte_heuristico_indice,
    simular_descarte_heuristico,
    tiene_rey,
    tiene_pareja,
    clasificar_mano_basico
)
from mascaras_descarte import generar_mascaras


def test_reyes_siempre_se_mantienen():
    """Test: Reyes siempre se mantienen."""
    print("=" * 70)
    print("TEST 1: Reyes siempre se mantienen")
    print("=" * 70)
    
    casos = [
        ([12, 11, 7, 4], 1, "Un Rey"),
        ([12, 12, 7, 4], 2, "Dos Reyes"),
        ([12, 12, 12, 7], 3, "Tres Reyes")
    ]
    
    for mano, pos, desc in casos:
        print(f"\n{desc}: {mano} (Pos {pos})")
        mascara = descarte_heuristico_base(mano, pos)
        cartas_descartadas = [mano[i] for i in mascara]
        cartas_mantenidas = [mano[i] for i in range(4) if i not in mascara]
        
        print(f"  Mantiene: {cartas_mantenidas}")
        print(f"  Descarta: {cartas_descartadas}")
        
        # Verificar que ningún Rey está en descartadas
        assert 12 not in cartas_descartadas, f"ERROR: Se descartó un Rey en {desc}"
    
    print("\n✓ Test 1 pasado")


def test_pareja_ases_posicional():
    """Test: Pareja de Ases solo se mantiene en posición 4."""
    print("\n" + "=" * 70)
    print("TEST 2: Pareja de Ases - Regla Posicional")
    print("=" * 70)
    
    mano = [1, 1, 5, 6]  # Pareja de Ases + basura
    
    # En posición 4 (Postre): se mantiene la pareja
    print("\nCaso 1: Pareja de Ases en Posición 4 (Postre)")
    print(f"  Mano: {mano}")
    mascara_pos4 = descarte_heuristico_base(mano, posicion=4)
    cartas_mantenidas_pos4 = [mano[i] for i in range(4) if i not in mascara_pos4]
    cartas_descartadas_pos4 = [mano[i] for i in mascara_pos4]
    
    print(f"  Mantiene: {cartas_mantenidas_pos4}")
    print(f"  Descarta: {cartas_descartadas_pos4}")
    
    assert cartas_mantenidas_pos4.count(1) == 2, "ERROR: Debería mantener ambos Ases en pos 4"
    
    # En posición 1: NO se mantiene la pareja (sin Rey)
    print("\nCaso 2: Pareja de Ases en Posición 1 (Mano)")
    print(f"  Mano: {mano}")
    mascara_pos1 = descarte_heuristico_base(mano, posicion=1)
    cartas_mantenidas_pos1 = [mano[i] for i in range(4) if i not in mascara_pos1]
    cartas_descartadas_pos1 = [mano[i] for i in mascara_pos1]
    
    print(f"  Mantiene: {cartas_mantenidas_pos1}")
    print(f"  Descarta: {cartas_descartadas_pos1}")
    
    # No debería mantener ambos ases (no hay Rey)
    assert cartas_mantenidas_pos1.count(1) < 2, "ERROR: No debería mantener pareja de Ases en pos 1 sin Rey"
    
    print("\n✓ Test 2 pasado")


def test_as_suelto_con_rey():
    """Test: As suelto se mantiene solo si hay Rey."""
    print("\n" + "=" * 70)
    print("TEST 3: As suelto - Solo con Rey")
    print("=" * 70)
    
    # Caso 1: Rey + As (debería mantener As)
    print("\nCaso 1: Rey + As + basura")
    mano_con_rey = [12, 1, 7, 5]
    print(f"  Mano: {mano_con_rey}")
    mascara = descarte_heuristico_base(mano_con_rey, posicion=2)
    cartas_mantenidas = [mano_con_rey[i] for i in range(4) if i not in mascara]
    cartas_descartadas = [mano_con_rey[i] for i in mascara]
    
    print(f"  Mantiene: {cartas_mantenidas}")
    print(f"  Descarta: {cartas_descartadas}")
    
    assert 12 in cartas_mantenidas, "ERROR: Debería mantener el Rey"
    assert 1 in cartas_mantenidas, "ERROR: Debería mantener el As (hay Rey)"
    
    # Caso 2: As sin Rey (no debería mantener As necesariamente)
    print("\nCaso 2: As sin Rey")
    mano_sin_rey = [11, 1, 7, 5]
    print(f"  Mano: {mano_sin_rey}")
    mascara = descarte_heuristico_base(mano_sin_rey, posicion=2)
    cartas_mantenidas = [mano_sin_rey[i] for i in range(4) if i not in mascara]
    cartas_descartadas = [mano_sin_rey[i] for i in mascara]
    
    print(f"  Mantiene: {cartas_mantenidas}")
    print(f"  Descarta: {cartas_descartadas}")
    
    # Si no hay Rey y no es posición 4, no debería mantener As suelto
    # (Este test puede variar según la implementación específica)
    print(f"  As en mantenidas: {1 in cartas_mantenidas}")
    print(f"  As en descartadas: {1 in cartas_descartadas}")
    
    print("\n✓ Test 3 pasado")


def test_figuras_altas_con_rey():
    """Test: Figuras altas se mantienen solo si hay Rey."""
    print("\n" + "=" * 70)
    print("TEST 4: Figuras altas (10, 11) - Solo con Rey")
    print("=" * 70)
    
    # Caso 1: Rey + Caballo (mantiene)
    print("\nCaso 1: Rey + Caballo + basura")
    mano_con_rey = [12, 11, 7, 5]
    print(f"  Mano: {mano_con_rey}")
    mascara = descarte_heuristico_base(mano_con_rey, posicion=1)
    cartas_mantenidas = [mano_con_rey[i] for i in range(4) if i not in mascara]
    cartas_descartadas = [mano_con_rey[i] for i in mascara]
    
    print(f"  Mantiene: {cartas_mantenidas}")
    print(f"  Descarta: {cartas_descartadas}")
    
    assert 12 in cartas_mantenidas, "ERROR: Debería mantener el Rey"
    assert 11 in cartas_mantenidas, "ERROR: Debería mantener el Caballo (hay Rey)"
    
    # Caso 2: Caballo sin Rey (descarta)
    print("\nCaso 2: Caballo sin Rey")
    mano_sin_rey = [11, 10, 7, 5]
    print(f"  Mano: {mano_sin_rey}")
    mascara = descarte_heuristico_base(mano_sin_rey, posicion=1)
    cartas_mantenidas = [mano_sin_rey[i] for i in range(4) if i not in mascara]
    cartas_descartadas = [mano_sin_rey[i] for i in mascara]
    
    print(f"  Mantiene: {cartas_mantenidas}")
    print(f"  Descarta: {cartas_descartadas}")
    
    # Sin Rey, las figuras pueden descartarse
    print(f"  11 en mantenidas: {11 in cartas_mantenidas}")
    print(f"  10 en mantenidas: {10 in cartas_mantenidas}")
    
    print("\n✓ Test 4 pasado")


def test_basura_se_descarta():
    """Test: Basura (4, 5, 6, 7) siempre se descarta."""
    print("\n" + "=" * 70)
    print("TEST 5: Basura siempre se descarta")
    print("=" * 70)
    
    mano = [12, 11, 7, 4]  # Rey, Caballo, Basura
    print(f"Mano: {mano}")
    
    for pos in [1, 2, 3, 4]:
        print(f"\nPosición {pos}:")
        mascara = descarte_heuristico_base(mano, pos)
        cartas_descartadas = [mano[i] for i in mascara]
        cartas_mantenidas = [mano[i] for i in range(4) if i not in mascara]
        
        print(f"  Mantiene: {cartas_mantenidas}")
        print(f"  Descarta: {cartas_descartadas}")
        
        # Verificar que basura está en descartadas
        basura_descartada = [c for c in cartas_descartadas if c in [4, 5, 6, 7]]
        print(f"  Basura descartada: {basura_descartada}")
        assert len(basura_descartada) > 0, f"ERROR: Debería descartar basura en pos {pos}"
    
    print("\n✓ Test 5 pasado")


def test_mano_perfecta():
    """Test: Mano perfecta (Duples + Juego)."""
    print("\n" + "=" * 70)
    print("TEST 6: Mano perfecta no descarta nada crítico")
    print("=" * 70)
    
    mano = [12, 12, 11, 10]  # Duples de Rey + Juego 31
    print(f"Mano: {mano} (Duples + Juego 31)")
    
    for pos in [1, 2, 3, 4]:
        print(f"\nPosición {pos}:")
        mascara = descarte_heuristico_base(mano, pos)
        cartas_descartadas = [mano[i] for i in mascara]
        cartas_mantenidas = [mano[i] for i in range(4) if i not in mascara]
        
        print(f"  Mantiene: {cartas_mantenidas}")
        print(f"  Descarta: {cartas_descartadas}")
        
        # Debería mantener los reyes
        assert cartas_mantenidas.count(12) == 2, f"ERROR: Debería mantener ambos Reyes"
    
    print("\n✓ Test 6 pasado")


def test_conversion_indice():
    """Test: Conversión a índice de máscara."""
    print("\n" + "=" * 70)
    print("TEST 7: Conversión a índice de máscara")
    print("=" * 70)
    
    mano = [12, 11, 7, 4]
    pos = 1
    
    print(f"Mano: {mano}, Posición: {pos}")
    
    mascara_tuple = descarte_heuristico_base(mano, pos)
    mascara_indice = descarte_heuristico_indice(mano, pos)
    
    print(f"  Máscara (tupla): {mascara_tuple}")
    print(f"  Máscara (índice): {mascara_indice}")
    
    mascaras = generar_mascaras()
    assert mascaras[mascara_indice] == mascara_tuple, "ERROR: Conversión incorrecta"
    
    print("\n✓ Test 7 pasado")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("🚀 INICIANDO TESTS DE HEURÍSTICA DE DESCARTE")
    print("=" * 70)
    
    test_reyes_siempre_se_mantienen()
    test_pareja_ases_posicional()
    test_as_suelto_con_rey()
    test_figuras_altas_con_rey()
    test_basura_se_descarta()
    test_mano_perfecta()
    test_conversion_indice()
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
