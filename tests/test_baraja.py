#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de la baraja
"""

import sys
sys.path.insert(0, '/workspaces/Probabilidades-Mus/calculadora_probabilidades_mus')

from calculadoramus import inicializar_baraja

def verificar_baraja(modo_8_reyes):
    modo_nombre = "8 REYES" if modo_8_reyes else "4 REYES"
    print(f"\n{'='*60}")
    print(f"Verificando modo: {modo_nombre}")
    print(f"{'='*60}")
    
    baraja = inicializar_baraja(modo_8_reyes)
    
    print(f"\nTotal de cartas: {len(baraja)}")
    
    # Contar frecuencias
    from collections import Counter
    conteo = Counter(baraja)
    
    print("\nDistribución de cartas:")
    for carta in sorted(conteo.keys()):
        print(f"  Carta {carta:2d}: {conteo[carta]} cartas")
    
    # Verificar total
    if len(baraja) == 40:
        print("\n✓ Baraja correcta: 40 cartas")
    else:
        print(f"\n✗ ERROR: La baraja tiene {len(baraja)} cartas (debería tener 40)")
    
    # Identificar reyes
    reyes = [carta for carta, count in conteo.items() if count == 8]
    print(f"\nReyes identificados: {reyes}")
    

if __name__ == "__main__":
    verificar_baraja(modo_8_reyes=False)
    verificar_baraja(modo_8_reyes=True)
    print(f"\n{'='*60}\n")
