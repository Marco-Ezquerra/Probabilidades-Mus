"""
Script de Análisis Detallado de Mano
Muestra paso a paso cómo se calcula el EV de cualquier mano en el Motor de Decisión.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from motor_decision import (
    MotorDecisionMus, EstadisticasEstaticas,
    analizar_mano, calcular_prob_rival,
    E_EXTRA_PARES, E_EXTRA_JUEGO, VALORES_PARES, VALORES_JUEGO
)
from calculadoramus import calcular_valor_juego, clasificar_pares


def imprimir_seccion(titulo):
    """Imprime un separador de sección."""
    print("\n" + "=" * 80)
    print(f"  {titulo}")
    print("=" * 80)


def imprimir_subseccion(titulo):
    """Imprime un separador de subsección."""
    print("\n" + "-" * 80)
    print(f"  {titulo}")
    print("-" * 80)


def analizar_mano_completo(mano, posicion=1, modo_8_reyes=True, perfil='normal', beta=None):
    """
    Analiza una mano de forma exhaustiva, mostrando todos los cálculos paso a paso.
    
    Args:
        mano: Lista de 4 cartas
        posicion: Posición en la mesa [1-4]
        modo_8_reyes: bool, modo de juego
        perfil: Perfil del motor
        beta: Factor de confianza en compañero [0.0-1.0]. Si None, usa el del perfil
    """
    # Inicializar motor
    motor = MotorDecisionMus(modo_8_reyes=modo_8_reyes, perfil=perfil, silent=True)
    stats = motor.estadisticas
    
    # Usar beta personalizado si se proporciona
    if beta is not None:
        beta = float(beta)
        beta = max(0.0, min(1.0, beta))  # Limitar entre 0 y 1
    else:
        beta = motor.params['beta']
    
    imprimir_seccion("ANÁLISIS COMPLETO DE MANO")
    
    print(f"\nMano: {sorted(mano, reverse=True)}")
    print(f"Posición: {posicion} {'(Mano - gana empates)' if posicion == 1 else '(Postre - pierde empates)' if posicion == 4 else ''}")
    print(f"Perfil: {perfil}")
    print(f"β (confianza en compañero): {beta:.2f} {'(personalizado)' if beta != motor.params['beta'] else '(del perfil)'}")
    print(f"   β = 0.0 → No confías en el compañero (solo tu mano)")
    print(f"   β = 1.0 → Confías 100% en el compañero")
    print(f"Modo: {'8 reyes' if modo_8_reyes else '4 reyes'}")
    
    # ============================================================================
    # 1. ANÁLISIS BÁSICO DE LA MANO
    # ============================================================================
    imprimir_subseccion("1. ANÁLISIS BÁSICO")
    
    analisis = analizar_mano(mano)
    
    print(f"\n🎴 PARES:")
    print(f"   Tipo: {analisis['tipo_pares']}")
    print(f"   Valor: {analisis['valor_pares']}")
    print(f"   W (valor base): {analisis['W_pares']}")
    
    print(f"\n🎲 JUEGO:")
    valor_juego = calcular_valor_juego(mano)
    print(f"   Cálculo: {' + '.join([f'min({c}, 10)' for c in mano])} = {valor_juego}")
    print(f"   Tiene juego: {'Sí' if valor_juego >= 31 else 'No'}")
    if valor_juego >= 31:
        print(f"   Valor: {valor_juego}")
        print(f"   W (valor base): {analisis['W_juego']}")
    
    # ============================================================================
    # 2. PROBABILIDADES DE LA MANO
    # ============================================================================
    imprimir_subseccion("2. PROBABILIDADES (desde dataset precalculado)")
    
    probs = stats.obtener_probabilidades(mano)
    
    print(f"\n📊 Probabilidades generales:")
    print(f"   P(Grande): {probs['prob_grande']:.4f} ({probs['prob_grande']:.2%})")
    print(f"   P(Chica):  {probs['prob_chica']:.4f} ({probs['prob_chica']:.2%})")
    print(f"   P(Pares):  {probs['prob_pares']:.4f} ({probs['prob_pares']:.2%})")
    print(f"   P(Juego):  {probs['prob_juego']:.4f} ({probs['prob_juego']:.2%})")
    
    # Probabilidades exactas para desempates
    if analisis['tiene_pares']:
        probs_pares = stats.obtener_prob_pares(mano)
        print(f"\n🔍 Probabilidades específicas PARES (para desempates):")
        print(f"   P(rival < yo): {probs_pares['prob_menor']:.4f} - Rivales estrictamente peores")
        print(f"   P(empate):     {probs_pares['prob_empate']:.4f} - Rivales con mano idéntica")
        print(f"   Total:         {probs_pares['prob_menor'] + probs_pares['prob_empate']:.4f}")
    
    if analisis['tiene_juego']:
        probs_juego = stats.obtener_prob_juego(mano)
        print(f"\n🔍 Probabilidades específicas JUEGO (para desempates):")
        print(f"   P(rival < yo): {probs_juego['prob_menor']:.4f} - Rivales estrictamente peores")
        print(f"   P(empate):     {probs_juego['prob_empate']:.4f} - Rivales con mano idéntica")
        print(f"   Total:         {probs_juego['prob_menor'] + probs_juego['prob_empate']:.4f}")
    
    # ============================================================================
    # 3. PROBABILIDADES CONDICIONADAS DE RIVALES
    # ============================================================================
    imprimir_subseccion("3. PROBABILIDADES CONDICIONADAS EXACTAS")
    
    mano_tuple = tuple(sorted(mano))
    prob_rival_pares_cond = probs.get('prob_rival_pares_condicionada', 0.0)
    prob_rival_juego_cond = probs.get('prob_rival_juego_condicionada', 0.0)
    
    print(f"\n🎯 Probabilidades de rivales (distribución hipergeométrica):")
    print(f"   Dadas mis 4 cartas, quedan 36 cartas en el mazo.")
    print(f"   Estas son las probabilidades EXACTAS de que AL MENOS 1 rival tenga la jugada:")
    print(f"\n   P(rival tiene pares): {prob_rival_pares_cond:.4f} ({prob_rival_pares_cond:.2%})")
    print(f"   P(rival tiene juego): {prob_rival_juego_cond:.4f} ({prob_rival_juego_cond:.2%})")
    print(f"\n   ✅ Estas probabilidades consideran:")
    print(f"      • Las 4 cartas que YO tengo (removidas del mazo)")
    print(f"      • Las 36 cartas restantes disponibles")
    print(f"      • Combinatoria exacta de manos posibles")
    
    # ============================================================================
    # 4. CÁLCULO DE EV - GRANDE (Lineal)
    # ============================================================================
    imprimir_subseccion("4. EV GRANDE (Lance Lineal)")
    
    print(f"\n📐 EV Propio:")
    print(f"   🏆 P(yo gano Grande): {probs['prob_grande']:.4f} ({probs['prob_grande']:.2%})")
    print(f"   Fórmula: P(yo gano) × 1.0 punto")
    ev_propio_g = probs['prob_grande'] * 1.0
    print(f"   EV = {probs['prob_grande']:.4f} × 1.0 = {ev_propio_g:.4f}")
    
    print(f"\n👥 EV Soporte (Compañero):")
    P_comp_media_g = stats.estadisticas_generales['P_comp_media_grande']
    factor_ajuste_g = 1.0 + (0.3 * (1 - probs['prob_grande']))
    P_comp_ajustado_g = min(P_comp_media_g * factor_ajuste_g, 0.9)
    ev_soporte_g = P_comp_ajustado_g * 1.0
    
    print(f"   🏆 P(compañero gana Grande): {P_comp_ajustado_g:.4f} ({P_comp_ajustado_g:.2%})")
    print(f"      P(comp media base): {P_comp_media_g:.4f}")
    print(f"      Factor ajuste (por mi debilidad): {factor_ajuste_g:.4f}")
    print(f"   EV soporte = {P_comp_ajustado_g:.4f} × 1.0 = {ev_soporte_g:.4f}")
    
    ev_decision_g = ev_propio_g + (beta * ev_soporte_g)
    print(f"\n✅ EV Decisión Grande:")
    print(f"   Fórmula: EV_propio + (β × EV_soporte)")
    print(f"   {ev_propio_g:.4f} + ({beta:.2f} × {ev_soporte_g:.4f}) = {ev_decision_g:.4f}")
    print(f"   💡 Con β={beta:.2f}, el compañero aporta {beta * ev_soporte_g:.4f} al EV total")
    
    # ============================================================================
    # 5. CÁLCULO DE EV - CHICA (Lineal)
    # ============================================================================
    imprimir_subseccion("5. EV CHICA (Lance Lineal)")
    
    print(f"\n📐 EV Propio:")
    print(f"   🏆 P(yo gano Chica): {probs['prob_chica']:.4f} ({probs['prob_chica']:.2%})")
    ev_propio_c = probs['prob_chica'] * 1.0
    print(f"   EV = {probs['prob_chica']:.4f} × 1.0 = {ev_propio_c:.4f}")
    
    print(f"\n👥 EV Soporte (Compañero):")
    P_comp_media_c = stats.estadisticas_generales['P_comp_media_chica']
    factor_ajuste_c = 1.0 + (0.3 * (1 - probs['prob_chica']))
    P_comp_ajustado_c = min(P_comp_media_c * factor_ajuste_c, 0.9)
    ev_soporte_c = P_comp_ajustado_c * 1.0
    
    print(f"   🏆 P(compañero gana Chica): {P_comp_ajustado_c:.4f} ({P_comp_ajustado_c:.2%})")
    print(f"      P(comp media base): {P_comp_media_c:.4f}")
    print(f"      Factor ajuste: {factor_ajuste_c:.4f}")
    print(f"   EV soporte = {P_comp_ajustado_c:.4f} × 1.0 = {ev_soporte_c:.4f}")
    
    ev_decision_c = ev_propio_c + (beta * ev_soporte_c)
    print(f"\n✅ EV Decisión Chica:")
    print(f"   {ev_propio_c:.4f} + ({beta:.2f} × {ev_soporte_c:.4f}) = {ev_decision_c:.4f}")
    print(f"   💡 Con β={beta:.2f}, el compañero aporta {beta * ev_soporte_c:.4f} al EV total")
    
    # ============================================================================
    # 6. CÁLCULO DE EV - PARES (Condicionado)
    # ============================================================================
    imprimir_subseccion("6. EV PARES (Lance Condicionado)")
    
    P_RL_pares = calcular_prob_rival('pares', mano, stats)
    print(f"\n🎯 Probabilidad condicionada exacta de que AL MENOS un rival tenga pares:")
    print(f"   P(al menos 1 rival tiene pares | mis 4 cartas): {P_RL_pares:.4f} ({P_RL_pares:.2%})")
    print(f"   ✅ Valor precomputado usando distribución hipergeométrica")
    print(f"      (36 cartas disponibles, considerando mis cartas removidas)")
    
    if analisis['tiene_pares']:
        print(f"\n📐 EV Propio (YO TENGO PARES):")
        probs_pares = stats.obtener_prob_pares(mano)
        
        # Factor de desempate
        factores_desempate = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}
        factor_desemp = factores_desempate[posicion]
        prob_yo_vs_rival = probs_pares['prob_menor'] + (probs_pares['prob_empate'] * factor_desemp)
        
        print(f"   W (valor base): {analisis['W_pares']}")
        print(f"   E_extra (swing): {E_EXTRA_PARES}")
        print(f"\n   🏆 P(yo gano Pares vs rival CON pares): {prob_yo_vs_rival:.4f} ({prob_yo_vs_rival:.2%})")
        print(f"      P(rival < yo):     {probs_pares['prob_menor']:.4f}")
        print(f"      P(empate) × factor: {probs_pares['prob_empate']:.4f} × {factor_desemp} = {probs_pares['prob_empate'] * factor_desemp:.4f}")
        
        ev_sin_rival = (1 - P_RL_pares) * analisis['W_pares']
        ev_con_rival = P_RL_pares * prob_yo_vs_rival * (analisis['W_pares'] + E_EXTRA_PARES)
        ev_propio_p = ev_sin_rival + ev_con_rival
        
        print(f"\n   Escenario 1 (rival SIN pares):")
        print(f"      P: {1 - P_RL_pares:.4f}")
        print(f"      EV: {1 - P_RL_pares:.4f} × {analisis['W_pares']} = {ev_sin_rival:.4f}")
        
        print(f"\n   Escenario 2 (rival CON pares, yo compito):")
        print(f"      P: {P_RL_pares:.4f}")
        print(f"      EV: {P_RL_pares:.4f} × {prob_yo_vs_rival:.4f} × ({analisis['W_pares']} + {E_EXTRA_PARES}) = {ev_con_rival:.4f}")
        
        print(f"\n   EV Propio Total: {ev_sin_rival:.4f} + {ev_con_rival:.4f} = {ev_propio_p:.4f}")
    else:
        print(f"\n❌ NO TENGO PARES")
        ev_propio_p = 0.0
        print(f"   EV Propio: {ev_propio_p:.4f}")
    
    print(f"\n👥 EV Soporte (Compañero):")
    W_comp_pares = 1.5
    prob_comp_tiene_pares = stats.estadisticas_generales['prob_tener_pares']
    factor_reduccion = 0.5 if analisis['tiene_pares'] else 1.0
    prob_comp_gana_pares = prob_comp_tiene_pares * 0.6
    ev_soporte_p = factor_reduccion * prob_comp_gana_pares * (W_comp_pares + E_EXTRA_PARES)
    
    print(f"   🏆 P(compañero gana Pares): {prob_comp_gana_pares:.4f} ({prob_comp_gana_pares:.2%})")
    print(f"      P(comp tiene pares): {prob_comp_tiene_pares:.4f}")
    print(f"      Factor reducción: {factor_reduccion} {'(ya tengo pares)' if analisis['tiene_pares'] else ''}")
    print(f"   EV soporte = {factor_reduccion} × {prob_comp_gana_pares:.4f} × {W_comp_pares + E_EXTRA_PARES} = {ev_soporte_p:.4f}")
    
    ev_decision_p = ev_propio_p + (beta * ev_soporte_p)
    print(f"\n✅ EV Decisión Pares:")
    print(f"   {ev_propio_p:.4f} + ({beta:.2f} × {ev_soporte_p:.4f}) = {ev_decision_p:.4f}")
    print(f"   💡 Con β={beta:.2f}, el compañero aporta {beta * ev_soporte_p:.4f} al EV total")
    
    # ============================================================================
    # 7. CÁLCULO DE EV - JUEGO (Condicionado)
    # ============================================================================
    imprimir_subseccion("7. EV JUEGO (Lance Condicionado)")
    
    P_RL_juego = calcular_prob_rival('juego', mano, stats)
    print(f"\n🎯 Probabilidad condicionada exacta de que AL MENOS un rival tenga juego:")
    print(f"   P(al menos 1 rival tiene juego | mis 4 cartas): {P_RL_juego:.4f} ({P_RL_juego:.2%})")
    print(f"   ✅ Valor precomputado usando distribución hipergeométrica")
    print(f"      (36 cartas disponibles, considerando mis cartas removidas)")
    
    if analisis['tiene_juego']:
        print(f"\n📐 EV Propio (YO TENGO JUEGO):")
        probs_juego = stats.obtener_prob_juego(mano)
        
        # Factor de desempate
        factores_desempate = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}
        factor_desemp = factores_desempate[posicion]
        prob_yo_vs_rival = probs_juego['prob_menor'] + (probs_juego['prob_empate'] * factor_desemp)
        
        print(f"   W (valor base): {analisis['W_juego']}")
        print(f"   E_extra (swing): {E_EXTRA_JUEGO}")
        print(f"\n   🏆 P(yo gano Juego vs rival CON juego): {prob_yo_vs_rival:.4f} ({prob_yo_vs_rival:.2%})")
        print(f"      P(rival < yo):     {probs_juego['prob_menor']:.4f}")
        print(f"      P(empate) × factor: {probs_juego['prob_empate']:.4f} × {factor_desemp} = {probs_juego['prob_empate'] * factor_desemp:.4f}")
        
        ev_sin_rival = (1 - P_RL_juego) * analisis['W_juego']
        ev_con_rival = P_RL_juego * prob_yo_vs_rival * (analisis['W_juego'] + E_EXTRA_JUEGO)
        ev_propio_j = ev_sin_rival + ev_con_rival
        
        print(f"\n   Escenario 1 (rival SIN juego):")
        print(f"      P: {1 - P_RL_juego:.4f}")
        print(f"      EV: {1 - P_RL_juego:.4f} × {analisis['W_juego']} = {ev_sin_rival:.4f}")
        
        print(f"\n   Escenario 2 (rival CON juego, yo compito):")
        print(f"      P: {P_RL_juego:.4f}")
        print(f"      EV: {P_RL_juego:.4f} × {prob_yo_vs_rival:.4f} × ({analisis['W_juego']} + {E_EXTRA_JUEGO}) = {ev_con_rival:.4f}")
        
        print(f"\n   EV Propio Total: {ev_sin_rival:.4f} + {ev_con_rival:.4f} = {ev_propio_j:.4f}")
    else:
        print(f"\n❌ NO TENGO JUEGO")
        ev_propio_j = 0.0
        print(f"   EV Propio: {ev_propio_j:.4f}")
    
    print(f"\n👥 EV Soporte (Compañero):")
    W_comp_juego = 2.0
    prob_comp_tiene_juego = stats.estadisticas_generales['prob_tener_juego']
    factor_reduccion_j = 0.5 if analisis['tiene_juego'] else 1.0
    prob_comp_gana_juego = prob_comp_tiene_juego * 0.6
    ev_soporte_j = factor_reduccion_j * prob_comp_gana_juego * (W_comp_juego + E_EXTRA_JUEGO)
    
    print(f"   🏆 P(compañero gana Juego): {prob_comp_gana_juego:.4f} ({prob_comp_gana_juego:.2%})")
    print(f"      P(comp tiene juego): {prob_comp_tiene_juego:.4f}")
    print(f"      Factor reducción: {factor_reduccion_j} {'(ya tengo juego)' if analisis['tiene_juego'] else ''}")
    print(f"   EV soporte = {factor_reduccion_j} × {prob_comp_gana_juego:.4f} × {W_comp_juego + E_EXTRA_JUEGO} = {ev_soporte_j:.4f}")
    
    ev_decision_j = ev_propio_j + (beta * ev_soporte_j)
    print(f"\n✅ EV Decisión Juego:")
    print(f"   {ev_propio_j:.4f} + ({beta:.2f} × {ev_soporte_j:.4f}) = {ev_decision_j:.4f}")
    print(f"   💡 Con β={beta:.2f}, el compañero aporta {beta * ev_soporte_j:.4f} al EV total")
    
    # ============================================================================
    # 8. EV TOTAL Y DECISIÓN
    # ============================================================================
    imprimir_subseccion("8. EV TOTAL Y DECISIÓN")
    
    ev_total = ev_decision_g + ev_decision_c + ev_decision_p + ev_decision_j
    
    print(f"\n📊 RESUMEN DE EVs POR LANCE:")
    print(f"   {'Lance':<10} {'Propio':<12} {'Soporte':<12} {'Decisión':<12}")
    print(f"   {'-' * 50}")
    print(f"   {'Grande':<10} {ev_propio_g:<12.4f} {ev_soporte_g:<12.4f} {ev_decision_g:<12.4f}")
    print(f"   {'Chica':<10} {ev_propio_c:<12.4f} {ev_soporte_c:<12.4f} {ev_decision_c:<12.4f}")
    print(f"   {'Pares':<10} {ev_propio_p:<12.4f} {ev_soporte_p:<12.4f} {ev_decision_p:<12.4f}")
    print(f"   {'Juego':<10} {ev_propio_j:<12.4f} {ev_soporte_j:<12.4f} {ev_decision_j:<12.4f}")
    print(f"   {'-' * 50}")
    print(f"   {'TOTAL':<10} {'':<12} {'':<12} {ev_total:<12.4f}")
    
    # Decisión
    decision, P_cortar, ev_total_calculado, _ = motor.decidir(mano, posicion=posicion)
    
    print(f"\n🎲 FUNCIÓN SIGMOIDE (Decisión estocástica):")
    print(f"   μ (umbral calibrado): {motor.mu:.4f}")
    print(f"   K (agresividad base): {motor.params['k_base']}")
    print(f"   σ (ruido gaussiano): {motor.params['sigma']}")
    print(f"   P(Cortar) = 1 / (1 + e^(-K × (EV - μ)))")
    print(f"   P(Cortar) en último cálculo: {P_cortar:.1%}")
    
    print(f"\n{'🛑 CORTAR' if decision else '🔄 MUS'}")
    print(f"   Decisión tomada: {'Cortar' if decision else 'Dar Mus'}")
    print(f"   Probabilidad base de cortar: ~{P_cortar:.1%}")
    
    # Nota sobre estocasticidad
    print(f"\n💡 NOTA SOBRE ESTOCASTICIDAD:")
    print(f"   - El EV de la mano es FIJO: {ev_total:.4f}")
    print(f"   - La DECISIÓN (Cortar/Mus) es ESTOCÁSTICA (aleatorio con sesgo)")
    print(f"   - Si repites el análisis, el EV será el mismo pero la decisión puede cambiar")
    print(f"   - Desviación estándar EV = 0 es CORRECTO (el EV no varía)")
    
    imprimir_seccion("FIN DEL ANÁLISIS")


def main():
    """Punto de entrada principal."""
    print("\n" + "=" * 80)
    print("  ANALIZADOR DETALLADO DE MANO - MOTOR DE DECISIÓN MUS")
    print("=" * 80)
    
    # Solicitar modo
    print("\n¿Qué modo de juego?")
    print("  1. 8 Reyes (por defecto)")
    print("  2. 4 Reyes")
    modo_input = input("\nSelecciona (1/2) [1]: ").strip() or "1"
    modo_8_reyes = modo_input == "1"
    
    # Solicitar mano
    print(f"\nIntroduce una mano de 4 cartas (separadas por espacios o comas)")
    if modo_8_reyes:
        print("  Valores válidos: 1, 4, 5, 6, 7, 10, 11, 12")
        print("  Ejemplo: 12 11 10 1  (significa 31)")
    else:
        print("  Valores válidos: 1, 2, 3, 4, 5, 6, 7, 10, 11, 12")
        print("  Ejemplo: 12 11 10 1")
    
    mano_input = input("\nMano: ").strip()
    
    # Parsear mano
    try:
        mano = [int(x) for x in mano_input.replace(',', ' ').split()]
        if len(mano) != 4:
            print(f"❌ Error: Debes introducir exactamente 4 cartas. Tienes {len(mano)}.")
            return
        
        # Validar valores según modo
        valores_validos = {1, 4, 5, 6, 7, 10, 11, 12} if modo_8_reyes else {1, 2, 3, 4, 5, 6, 7, 10, 11, 12}
        valores_invalidos = set(mano) - valores_validos
        if valores_invalidos:
            print(f"❌ Error: Valores inválidos: {valores_invalidos}")
            print(f"   Valores permitidos en {'8' if modo_8_reyes else '4'} reyes: {sorted(valores_validos)}")
            return
            
    except ValueError:
        print("❌ Error: Introduce solo números separados por espacios.")
        return
    
    # Solicitar posición
    print(f"\n¿En qué posición estás en la mesa?")
    print("  1. Posición 1 (Mano - ganas empates)")
    print("  2. Posición 2")
    print("  3. Posición 3")
    print("  4. Posición 4 (Postre - pierdes empates)")
    posicion_input = input("\nPosición (1/2/3/4) [1]: ").strip() or "1"
    
    try:
        posicion = int(posicion_input)
        if posicion not in [1, 2, 3, 4]:
            print("❌ Error: Posición debe ser 1, 2, 3 o 4.")
            return
    except ValueError:
        print("❌ Error: Posición debe ser un número.")
        return
    
    # Solicitar perfil
    print(f"\n¿Qué perfil de juego?")
    print("  1. Normal (β=0.75)")
    print("  2. Conservador (β=0.65)")
    print("  3. Agresivo (β=0.85)")
    print("  4. Personalizado")
    perfil_input = input("\nPerfil (1/2/3/4) [1]: ").strip() or "1"
    perfiles = {"1": "normal", "2": "conservador", "3": "agresivo"}
    perfil = perfiles.get(perfil_input, "normal")
    
    # Solicitar beta personalizado
    beta_custom = None
    if perfil_input == "4":
        perfil = "normal"  # Usar normal como base
        print(f"\n¿Cuánto confías en tu compañero?")
        print("  β = 0.0 → No confías nada (solo tu mano cuenta)")
        print("  β = 0.5 → Confianza media")
        print("  β = 1.0 → Confianza total")
        beta_input = input("\nβ (0.0 - 1.0) [0.75]: ").strip() or "0.75"
        try:
            beta_custom = float(beta_input)
            if beta_custom < 0 or beta_custom > 1:
                print("⚠️  β fuera de rango, usando 0.75")
                beta_custom = 0.75
        except ValueError:
            print("⚠️  Valor inválido, usando 0.75")
            beta_custom = 0.75
    
    # Ejecutar análisis
    print("\n")
    analizar_mano_completo(mano, posicion, modo_8_reyes, perfil, beta=beta_custom)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Análisis interrumpido por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
