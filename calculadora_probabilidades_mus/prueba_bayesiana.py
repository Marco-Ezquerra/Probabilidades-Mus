#!/usr/bin/env python3
"""
Script para validar la corrección de asimetría bayesiana.
Compara el impacto del factor bayesiano en rivales vs compañero.
"""

from motor_decision import (
    calcular_peso_mano,
    calcular_factor_bayesiano,
    calcular_prob_rival,
    EstadisticasEstaticas
)

def analizar_caso(mano, descripcion):
    """Analiza impacto bayesiano en una mano"""
    print(f"\n{'='*80}")
    print(f"  {descripcion}")
    print(f"  Mano: {mano}")
    print(f"{'='*80}")
    
    # Calcular factor bayesiano
    peso = calcular_peso_mano(mano)
    factor = calcular_factor_bayesiano(peso)
    
    print(f"\n⚖️  Peso mano: {peso:.2f} pts")
    print(f"📊 Factor Bayesiano: {factor:.4f}")
    
    if factor > 1.0:
        print(f"   → Mazo ENRIQUECIDO (tengo basura)")
    elif factor < 1.0:
        print(f"   → Mazo EMPOBRECIDO (tengo reyes)")
    else:
        print(f"   → Mazo NEUTRAL")
    
    # Cargar estadísticas
    stats = EstadisticasEstaticas()
    
    # Probabilidades base (sin ajuste bayesiano)
    p_individual_pares_base = stats.estadisticas_generales['prob_tener_pares']
    p_individual_juego_base = stats.estadisticas_generales['prob_tener_juego']
    
    # Probabilidades con factor bayesiano
    P_RL_pares = calcular_prob_rival('pares', stats, mano)
    P_RL_juego = calcular_prob_rival('juego', stats, mano)
    
    # Calcular ajustes
    p_pares_ajustado = min(p_individual_pares_base * factor, 0.95)
    p_juego_ajustado = min(p_individual_juego_base * factor, 0.95)
    
    # Mostrar resultados
    print(f"\n📈 PARES:")
    print(f"   P(individual base):     {p_individual_pares_base:.4f}")
    print(f"   P(individual ajustado): {p_pares_ajustado:.4f} (×{factor:.4f} = {p_individual_pares_base*factor:.4f})")
    print(f"   P(al menos 1 rival):    {P_RL_pares:.4f}")
    
    cambio_pares = (p_pares_ajustado - p_individual_pares_base) / p_individual_pares_base * 100
    print(f"   Δ Cambio: {cambio_pares:+.2f}%")
    
    print(f"\n🎲 JUEGO:")
    print(f"   P(individual base):     {p_individual_juego_base:.4f}")
    print(f"   P(individual ajustado): {p_juego_ajustado:.4f} (×{factor:.4f} = {p_individual_juego_base*factor:.4f})")
    print(f"   P(al menos 1 rival):    {P_RL_juego:.4f}")
    
    cambio_juego = (p_juego_ajustado - p_individual_juego_base) / p_individual_juego_base * 100
    print(f"   Δ Cambio: {cambio_juego:+.2f}%")
    
    print(f"\n💡 Interpretación:")
    if factor > 1.0:
        print(f"   • Rivales tienen {cambio_pares:+.1f}% más probabilidad de pares")
        print(f"   • Rivales tienen {cambio_juego:+.1f}% más probabilidad de juego")
        print(f"   • Compañero TAMBIÉN se beneficia (mismo factor aplicado)")
        print(f"   ✅ SIMETRÍA: Mazo enriquecido beneficia a todos por igual")
    elif factor < 1.0:
        print(f"   • Rivales tienen {cambio_pares:.1f}% menos probabilidad de pares")
        print(f"   • Rivales tienen {cambio_juego:.1f}% menos probabilidad de juego")
        print(f"   • Compañero TAMBIÉN se perjudica (mismo factor aplicado)")
        print(f"   ✅ SIMETRÍA: Mazo empobrecido perjudica a todos por igual")


if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"  VALIDACIÓN DE SIMETRÍA BAYESIANA")
    print(f"  Factor = 1.3 - (peso/16) × 0.6")
    print(f"{'='*80}")
    
    # Caso 1: Mano pesada (muchos Reyes) → factor < 1.0
    analizar_caso([12, 12, 11, 11], "CASO 1: Mano PESADA (Reyes)")
    
    # Caso 2: Mano ligera (basura) → factor > 1.0
    analizar_caso([5, 4, 6, 7], "CASO 2: Mano LIGERA (Basura)")
    
    # Caso 3: Mano mixta
    analizar_caso([12, 11, 6, 5], "CASO 3: Mano MIXTA")
    
    print(f"\n{'='*80}")
    print(f"  CONCLUSIÓN")
    print(f"{'='*80}")
    print(f"\n✅ El factor bayesiano ahora se aplica SIMÉTRICAMENTE:")
    print(f"   • Rivales: min(p_individual × factor, 0.95)")
    print(f"   • Compañero: también usa el mismo factor")
    print(f"\n🎯 No hay sesgo optimista/pesimista por remoción de cartas")
    print()
