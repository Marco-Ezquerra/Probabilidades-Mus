"""
Demo interactiva de la Fase 2: Sistema de Rollout con Puntos Reales.

Muestra ejemplos de:
1. Generación de máscaras
2. Heurística de descarte
3. Evaluación de ronda completa
4. Simulación de rollout para una mano
"""

import sys
from pathlib import Path
import random

# Añadir paths
sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "calculadora_probabilidades_mus"))

from mascaras_descarte import generar_mascaras, aplicar_mascara, completar_mano
from descarte_heuristico import descarte_heuristico_base, simular_descarte_heuristico
from evaluador_ronda import evaluar_ronda_completa
from calculadoramus import inicializar_baraja


def demo_mascaras():
    """Demo de máscaras de descarte."""
    print("=" * 70)
    print("DEMO 1: MÁSCARAS DE DESCARTE")
    print("=" * 70)
    
    mascaras = generar_mascaras()
    print(f"\n✓ Generadas {len(mascaras)} máscaras posibles")
    
    # Mostrar algunas máscaras representativas
    print("\nEjemplos de máscaras:")
    ejemplos = [0, 4, 9, 14]  # Primera, quinta, décima, última
    for idx in ejemplos:
        mascara = mascaras[idx]
        print(f"  [{idx:2d}] {mascara} - Descartar {len(mascara)} carta(s)")
    
    # Aplicar una máscara a una mano ejemplo
    print("\n" + "-" * 70)
    mano_ejemplo = [12, 12, 11, 10]
    print(f"Mano ejemplo: {mano_ejemplo} (Duples de Rey + Juego)")
    
    mascara = (2, 3)  # Descartar 11 y 10
    mano_restante, descartadas = aplicar_mascara(mano_ejemplo, mascara)
    print(f"Aplicar máscara {mascara}:")
    print(f"  → Mantiene: {mano_restante}")
    print(f"  → Descarta: {descartadas}")


def demo_heuristica():
    """Demo de heurística de descarte."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: HEURÍSTICA DE DESCARTE")
    print("=" * 70)
    
    casos = [
        ([12, 12, 11, 10], 1, "Duples + Juego (Pos 1)"),
        ([1, 1, 5, 6], 4, "Pareja de Ases (Pos 4 - Postre)"),
        ([1, 1, 5, 6], 1, "Pareja de Ases (Pos 1 - Mano)"),
        ([12, 1, 7, 5], 2, "Rey + As + Basura"),
        ([11, 10, 7, 5], 3, "Solo figuras sin Rey"),
    ]
    
    print("\nEvaluando diferentes manos con heurística:")
    print("-" * 70)
    
    for mano, pos, desc in casos:
        print(f"\n{desc}")
        resultado = simular_descarte_heuristico(mano, pos, verbose=True)


def demo_evaluacion_ronda():
    """Demo de evaluación de ronda completa."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: EVALUACIÓN DE RONDA COMPLETA")
    print("=" * 70)
    
    print("\nEscenario: Equipo A domina claramente")
    manos = {
        1: [12, 12, 11, 10],  # Duples + Juego 31
        2: [7, 7, 6, 5],      # Pares de 7
        3: [12, 11, 10, 1],   # Juego 31
        4: [6, 5, 5, 4]       # Pares de 5
    }
    
    resultado = evaluar_ronda_completa(manos, verbose=True)
    
    print("\n" + "=" * 70)
    print("ANÁLISIS DEL RESULTADO")
    print("=" * 70)
    print(f"Diferencial: {resultado['Diferencial']:+d} puntos")
    print(f"Ganador: Equipo {'A' if resultado['Diferencial'] > 0 else 'B'}")


def demo_rollout_simple():
    """Demo simplificado de un rollout."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: SIMULACIÓN DE ROLLOUT (Simplificado)")
    print("=" * 70)
    
    print("\nSimulando descarte + reparto + evaluación...")
    print("-" * 70)
    
    # Inicializar baraja
    baraja = inicializar_baraja(modo_8_reyes=True)
    random.shuffle(baraja)
    
    # Repartir 4 manos
    print("\n1. MANOS INICIALES:")
    manos_iniciales = {}
    mazo_temp = baraja.copy()
    for pos in [1, 2, 3, 4]:
        mano = mazo_temp[:4]
        manos_iniciales[pos] = sorted(mano, reverse=True)
        mazo_temp = mazo_temp[4:]
        print(f"   Pos {pos}: {manos_iniciales[pos]}")
    
    mazo_restante = mazo_temp
    
    # Descartar según heurística
    print("\n2. DESCARTES (según heurística):")
    manos_finales = {}
    for pos in [1, 2, 3, 4]:
        mascara = descarte_heuristico_base(manos_iniciales[pos], pos)
        mano_restante, descartadas = aplicar_mascara(manos_iniciales[pos], mascara)
        mano_final = completar_mano(mano_restante, mazo_restante)
        manos_finales[pos] = mano_final
        print(f"   Pos {pos}: Descarta {descartadas} → Nueva mano: {mano_final}")
    
    # Evaluar resultado
    print("\n3. EVALUACIÓN DE LA RONDA:")
    print("-" * 70)
    resultado = evaluar_ronda_completa(manos_finales, verbose=True)
    
    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: Diferencial = {resultado['Diferencial']:+d} puntos")
    print("=" * 70)


def main():
    """Ejecuta todas las demos."""
    print("\n" * 2)
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║          DEMO INTERACTIVA - FASE 2: ROLLOUT CON PUNTOS REALES       ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    try:
        demo_mascaras()
        input("\n[Presiona Enter para continuar...]")
        
        demo_heuristica()
        input("\n[Presiona Enter para continuar...]")
        
        demo_evaluacion_ronda()
        input("\n[Presiona Enter para continuar...]")
        
        demo_rollout_simple()
        
        print("\n\n" + "=" * 70)
        print("✅ DEMO COMPLETADA")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("  1. Generar políticas: python calculadora_probabilidades_mus/generar_politicas_rollout.py")
        print("  2. Simular Fase 2:    python calculadora_probabilidades_mus/simulador_fase2.py")
        print("  3. Ver README:        cat calculadora_probabilidades_mus/README_FASE2.md")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
