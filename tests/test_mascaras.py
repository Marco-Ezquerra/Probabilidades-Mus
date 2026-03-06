"""
Tests de validación para el módulo de máscaras de descarte.

Verifica:
1. Se generan exactamente 15 máscaras
2. Las máscaras cubren todos los casos (1, 2, 3, 4 cartas)
3. La aplicación de máscaras funciona correctamente
4. Robar cartas reduce la baraja apropiadamente
"""

import sys
from pathlib import Path

# Añadir paths
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from mascaras_descarte import (
    generar_mascaras,
    aplicar_mascara,
    robar_cartas,
    completar_mano,
    encontrar_mascara,
    mascara_a_indice,
    indice_a_mascara
)


def test_generar_15_mascaras():
    """Test: Se generan exactamente 15 máscaras."""
    print("=" * 70)
    print("TEST 1: Generación de 15 máscaras")
    print("=" * 70)
    
    mascaras = generar_mascaras()
    
    print(f"Máscaras generadas: {len(mascaras)}")
    assert len(mascaras) == 15, f"ERROR: Se esperaban 15 máscaras, se generaron {len(mascaras)}"
    
    # Verificar distribución por tamaño
    por_tamano = {1: 0, 2: 0, 3: 0, 4: 0}
    for m in mascaras:
        por_tamano[len(m)] += 1
    
    print(f"Distribución por tamaño:")
    print(f"  - 1 carta: {por_tamano[1]} (esperado: 4)")
    print(f"  - 2 cartas: {por_tamano[2]} (esperado: 6)")
    print(f"  - 3 cartas: {por_tamano[3]} (esperado: 4)")
    print(f"  - 4 cartas: {por_tamano[4]} (esperado: 1)")
    
    assert por_tamano[1] == 4, "ERROR: Debería haber 4 máscaras de 1 carta"
    assert por_tamano[2] == 6, "ERROR: Debería haber 6 máscaras de 2 cartas"
    assert por_tamano[3] == 4, "ERROR: Debería haber 4 máscaras de 3 cartas"
    assert por_tamano[4] == 1, "ERROR: Debería haber 1 máscara de 4 cartas"
    
    print("✓ Test 1 pasado")


def test_aplicar_mascara():
    """Test: Aplicar máscaras funciona correctamente."""
    print("\n" + "=" * 70)
    print("TEST 2: Aplicación de máscaras")
    print("=" * 70)
    
    mano = [12, 12, 11, 10]
    
    # Caso 1: Descartar primera carta
    print("\nCaso 1: Descartar posición 0")
    restante, descartadas = aplicar_mascara(mano, (0,))
    print(f"  Mano: {mano}")
    print(f"  Quedan: {restante}, Descartadas: {descartadas}")
    assert restante == [12, 11, 10], f"ERROR: Esperado [12, 11, 10], obtenido {restante}"
    assert descartadas == [12], f"ERROR: Esperado [12], obtenido {descartadas}"
    
    # Caso 2: Descartar dos cartas
    print("\nCaso 2: Descartar posiciones 0, 1")
    restante, descartadas = aplicar_mascara(mano, (0, 1))
    print(f"  Mano: {mano}")
    print(f"  Quedan: {restante}, Descartadas: {descartadas}")
    assert restante == [11, 10], f"ERROR: Esperado [11, 10], obtenido {restante}"
    assert descartadas == [12, 12], f"ERROR: Esperado [12, 12], obtenido {descartadas}"
    
    # Caso 3: Descartar toda la mano
    print("\nCaso 3: Descartar todas (0, 1, 2, 3)")
    restante, descartadas = aplicar_mascara(mano, (0, 1, 2, 3))
    print(f"  Mano: {mano}")
    print(f"  Quedan: {restante}, Descartadas: {descartadas}")
    assert restante == [], f"ERROR: Esperado [], obtenido {restante}"
    assert descartadas == [12, 12, 11, 10], f"ERROR: Esperado [12, 12, 11, 10], obtenido {descartadas}"
    
    print("\n✓ Test 2 pasado")


def test_robar_cartas():
    """Test: Robar cartas funciona correctamente."""
    print("\n" + "=" * 70)
    print("TEST 3: Robar cartas de la baraja")
    print("=" * 70)
    
    baraja = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    baraja_copia = baraja.copy()
    
    print(f"Baraja inicial: {baraja_copia} ({len(baraja_copia)} cartas)")
    
    # Robar 3 cartas
    robadas = robar_cartas(baraja_copia, 3)
    print(f"Cartas robadas: {robadas} ({len(robadas)} cartas)")
    print(f"Baraja restante: {baraja_copia} ({len(baraja_copia)} cartas)")
    
    assert len(robadas) == 3, f"ERROR: Se esperaban 3 cartas robadas, se obtuvieron {len(robadas)}"
    assert len(baraja_copia) == 7, f"ERROR: Debería quedar 7 cartas, quedan {len(baraja_copia)}"
    
    # Verificar que las robadas están en la baraja original
    for carta in robadas:
        assert carta in baraja, f"ERROR: Carta {carta} no estaba en la baraja original"
    
    # Verificar que no hay duplicados en las robadas
    assert len(robadas) == len(set(robadas)), "ERROR: Hay cartas duplicadas en las robadas"
    
    print("✓ Test 3 pasado")


def test_completar_mano():
    """Test: Completar mano funciona correctamente."""
    print("\n" + "=" * 70)
    print("TEST 4: Completar mano tras descarte")
    print("=" * 70)
    
    mano_parcial = [12, 11]
    baraja = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    baraja_copia = baraja.copy()
    
    print(f"Mano parcial: {mano_parcial} ({len(mano_parcial)} cartas)")
    print(f"Baraja disponible: {len(baraja_copia)} cartas")
    
    mano_completa = completar_mano(mano_parcial, baraja_copia)
    
    print(f"Mano completada: {mano_completa} ({len(mano_completa)} cartas)")
    print(f"Baraja restante: {len(baraja_copia)} cartas")
    
    assert len(mano_completa) == 4, f"ERROR: La mano debería tener 4 cartas, tiene {len(mano_completa)}"
    assert len(baraja_copia) == 8, f"ERROR: Debería quedar 8 cartas en baraja, quedan {len(baraja_copia)}"
    
    # Verificar que las originales están
    assert 12 in mano_completa, "ERROR: Falta el 12 original"
    assert 11 in mano_completa, "ERROR: Falta el 11 original"
    
    # Verificar que está ordenada descendente
    assert mano_completa == sorted(mano_completa, reverse=True), "ERROR: Mano no está ordenada descendente"
    
    print("✓ Test 4 pasado")


def test_conversion_mascaras():
    """Test: Conversión entre máscaras e índices."""
    print("\n" + "=" * 70)
    print("TEST 5: Conversión máscaras <-> índices")
    print("=" * 70)
    
    mascaras = generar_mascaras()
    
    # Test ida y vuelta
    for idx, mascara in enumerate(mascaras):
        idx_calculado = mascara_a_indice(mascara, mascaras)
        assert idx_calculado == idx, f"ERROR: mascara_a_indice falló para {mascara}"
        
        mascara_calculada = indice_a_mascara(idx, mascaras)
        assert mascara_calculada == mascara, f"ERROR: indice_a_mascara falló para índice {idx}"
    
    print(f"✓ Todas las conversiones (15 máscaras) funcionan correctamente")
    print("✓ Test 5 pasado")


def test_encontrar_mascara():
    """Test: Encontrar máscara desde cartas a descartar."""
    print("\n" + "=" * 70)
    print("TEST 6: Encontrar máscara desde cartas")
    print("=" * 70)
    
    mano = [12, 12, 11, 10]
    
    # Caso 1: Descartar primer 12
    mascara = encontrar_mascara([12], mano)
    print(f"Descartar [12] de {mano} -> Máscara: {mascara}")
    assert mascara[0] == 0, f"ERROR: Esperado índice 0, obtenido {mascara}"
    
    # Caso 2: Descartar ambos 12
    mascara = encontrar_mascara([12, 12], mano)
    print(f"Descartar [12, 12] de {mano} -> Máscara: {mascara}")
    assert mascara == (0, 1), f"ERROR: Esperado (0, 1), obtenido {mascara}"
    
    # Caso 3: Descartar todo menos un 12
    mascara = encontrar_mascara([12, 11, 10], mano)
    print(f"Descartar [12, 11, 10] de {mano} -> Máscara: {mascara}")
    assert len(mascara) == 3, f"ERROR: Esperado 3 índices, obtenido {len(mascara)}"
    
    print("✓ Test 6 pasado")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("🚀 INICIANDO TESTS DE MÁSCARAS DE DESCARTE")
    print("=" * 70)
    
    test_generar_15_mascaras()
    test_aplicar_mascara()
    test_robar_cartas()
    test_completar_mano()
    test_conversion_mascaras()
    test_encontrar_mascara()
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
