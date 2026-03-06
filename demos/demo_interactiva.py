#!/usr/bin/env python3
"""
Demo Interactiva del Sistema de Análisis de Mus
Muestra todas las funcionalidades del sistema de forma visual.
"""

import sys
sys.path.insert(0, '/workspaces/Probabilidades-Mus/calculadora_probabilidades_mus')

import random
from calculadoramus import (
    inicializar_baraja, 
    clasificar_pares, 
    comparar_grande_chica,
    calcular_valor_juego
)
from simular_dinamico import simular_con_companero, formatear_resultado_legible
from motor_decision import MotorDecisionMus


def imprimir_separador(titulo="", ancho=70):
    """Imprime un separador con título opcional."""
    if titulo:
        padding = (ancho - len(titulo) - 2) // 2
        print("=" * padding + f" {titulo} " + "=" * padding)
    else:
        print("=" * ancho)


def formatear_mano(mano):
    """Convierte lista de cartas en string legible."""
    return " ".join([f"[{c:2d}]" for c in mano])


def demo_estatica():
    """Demo de probabilidades estáticas."""
    imprimir_separador("DEMO 1: ANÁLISIS ESTÁTICO")
    
    print("\nSe reparte una mano aleatoria y se consultan sus probabilidades")
    print("precalculadas (basadas en 100,000 simulaciones).\n")
    
    # Generar mano aleatoria
    baraja = inicializar_baraja(modo_8_reyes=True)
    mano = sorted(random.sample(baraja, 4), reverse=True)
    
    print(f"Tu mano: {formatear_mano(mano)}")
    
    # Analizar características
    tipo_pares, _ = clasificar_pares(mano)
    es_grande = comparar_grande_chica(mano, [10, 7, 6, 5], es_grande=True)
    es_chica = comparar_grande_chica(mano, [10, 7, 6, 5], es_grande=False)
    valor_juego = calcular_valor_juego(mano)
    
    print("\nCaracterísticas:")
    print(f"  Pares: {tipo_pares if tipo_pares != 'sin_pares' else '❌ No'}")
    if valor_juego >= 31:
        print(f"  Juego: ✓ Sí (valor: {valor_juego})")
    else:
        print(f"  Juego: ❌ No (punto: {valor_juego})")
    
    # Cargar probabilidades desde CSV
    import pandas as pd
    try:
        df = pd.read_csv('/workspaces/Probabilidades-Mus/calculadora_probabilidades_mus/resultados_8reyes.csv')
        mano_str = str(mano)
        fila = df[df['mano'] == mano_str]
        
        if not fila.empty:
            print("\nProbabilidades de victoria (estadísticas precalculadas):")
            print(f"  GRANDE: {fila['probabilidad_grande'].values[0]:.1%}")
            print(f"  CHICA:  {fila['probabilidad_chica'].values[0]:.1%}")
            print(f"  PARES:  {fila['probabilidad_pares'].values[0]:.1%}")
            print(f"  JUEGO:  {fila['probabilidad_juego'].values[0]:.1%}")
        else:
            print("\n⚠️  Mano no encontrada en estadísticas (mano muy rara)")
    except Exception as e:
        print(f"\n⚠️  Error cargando estadísticas: {e}")
    
    print("\n" + "→" * 35)
    input("Presiona ENTER para continuar...")


def demo_dinamica():
    """Demo de simulación dinámica con compañero."""
    imprimir_separador("DEMO 2: SIMULACIÓN DINÁMICA")
    
    print("\nTu compañero te muestra su mano. Ahora podemos calcular")
    print("probabilidades CONDICIONADAS conociendo 8 de las 40 cartas.\n")
    
    baraja = inicializar_baraja(modo_8_reyes=True)
    
    # Repartir manos
    baraja_mezclada = random.sample(baraja, len(baraja))
    tu_mano = sorted(baraja_mezclada[:4], reverse=True)
    mano_companero = sorted(baraja_mezclada[4:8], reverse=True)
    
    print(f"Tu mano:         {formatear_mano(tu_mano)}")
    print(f"Mano compañero:  {formatear_mano(mano_companero)}")
    
    print("\n⏳ Simulando 50,000 partidas (quedan 32 cartas para 2 rivales)...\n")
    
    # Simular
    resultado = simular_con_companero(tu_mano, mano_companero, baraja, iteraciones=50000)
    
    # Mostrar resultados formateados
    print(formatear_resultado_legible(tu_mano, mano_companero, resultado))
    
    print("\n💡 Estas probabilidades son más precisas que las estáticas porque")
    print("   conocemos información adicional (mano del compañero).")
    
    print("\n" + "→" * 35)
    input("Presiona ENTER para continuar...")


def demo_motor_ia():
    """Demo del motor de decisión IA."""
    imprimir_separador("DEMO 3: MOTOR DE DECISIÓN IA")
    
    print("\nEl motor IA analiza la mano y decide si CORTAR o pedir MUS")
    print("usando Valor Esperado (EV) y una política estocástica.\n")
    
    # Probar con 3 perfiles
    baraja = inicializar_baraja(modo_8_reyes=True)
    mano = sorted(random.sample(baraja, 4), reverse=True)
    
    print(f"Tu mano: {formatear_mano(mano)}\n")
    
    for perfil in ['conservador', 'normal', 'agresivo']:
        motor = MotorDecisionMus(modo_8_reyes=True, perfil=perfil, silent=True)
        
        # Hacer 20 decisiones para ver tasa
        decisiones = []
        evs = []
        probs = []
        
        for _ in range(20):
            decision, prob, ev, _ = motor.decidir(mano)
            decisiones.append(decision)
            probs.append(prob)
            evs.append(ev)
        
        tasa_corte = sum(decisiones) / len(decisiones)
        prob_media = sum(probs) / len(probs)
        ev_medio = sum(evs) / len(evs)
        
        print(f"Perfil {perfil.upper()}:")
        print(f"  EV:               {ev_medio:.4f}")
        print(f"  P(Cortar) media:  {prob_media:.1%}")
        print(f"  Tasa de corte:    {tasa_corte:.0%} (20 simulaciones)")
        print(f"  Umbral μ:         {motor.mu:.4f}")
        print()
    
    print("💡 El perfil conservador exige EVs más altos para cortar.")
    print("   El agresivo corta con EVs más bajos (más arriesgado).")
    
    print("\n" + "→" * 35)
    input("Presiona ENTER para continuar...")


def demo_decision_detallada():
    """Demo con análisis detallado de una decisión."""
    imprimir_separador("DEMO 4: ANÁLISIS DETALLADO DE DECISIÓN")
    
    print("\nVeamos el razonamiento completo del motor IA para una mano.\n")
    
    # Crear mano interesante
    mano = [12, 12, 11, 10]  # Duples + juego alto
    
    print(f"Tu mano: {formatear_mano(mano)}")
    print("         (Pares de reyes + Juego de 40)\n")
    
    # Crear motor
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal', silent=True)
    
    # Análisis completo
    analisis = motor.analizar_mano_detallado(mano)
    
    print("CARACTERÍSTICAS:")
    carac = analisis['caracteristicas']
    print(f"  Tipo de pares: {carac['tipo_pares']}")
    print(f"  Valor W pares: {carac['W_pares']:.1f}")
    print(f"  Tiene juego:   {'✓ Sí' if carac['tiene_juego'] else '❌ No'}")
    if carac['tiene_juego']:
        print(f"  Valor juego:   {analisis['valor_juego']}")
    
    print("\nPROBABILIDADES DE VICTORIA:")
    probs = analisis['probabilidades']
    print(f"  GRANDE: {probs['prob_grande']:.2%}")
    print(f"  CHICA:  {probs['prob_chica']:.2%}")
    print(f"  PARES:  {probs['prob_pares']:.2%}")
    print(f"  JUEGO:  {probs['prob_juego']:.2%}")
    
    print("\nDESGLOSE DE VALOR ESPERADO (EV):")
    desglose = analisis['desglose']
    ev_total = 0
    
    for lance in ['grande', 'chica', 'pares', 'juego']:
        d = desglose[lance]
        ev_lance = d['propio'] + d['soporte']
        ev_total += ev_lance
        print(f"  {lance.upper():6s}: {ev_lance:.4f} = {d['propio']:.4f} (propio) + " +
              f"{d['soporte']:.4f} (soporte)")
    
    print(f"\n  TOTAL EV: {analisis['EV_total']:.4f}")
    print(f"  Umbral μ: {motor.mu:.4f}")
    print(f"  Diferencia: {analisis['EV_total'] - motor.mu:.4f}")
    
    # Tomar decisión
    decision, prob, _, _ = motor.decidir(mano)
    
    print(f"\nDECISIÓN:")
    print(f"  {'🛑 CORTAR' if decision else '🔄 MUS'}")
    print(f"  Probabilidad: {prob:.1%}")
    
    print("\n💡 Como EV > μ, la probabilidad de cortar es alta (>50%).")
    print("   El componente estocástico añade variabilidad natural.")
    
    print("\n" + "→" * 35)
    input("Presiona ENTER para continuar...")


def demo_comparacion():
    """Demo comparando una mano en los 3 componentes."""
    imprimir_separador("DEMO 5: COMPARACIÓN COMPLETA")
    
    print("\nComparemos cómo los 3 componentes analizan la misma mano:\n")
    
    baraja = inicializar_baraja(modo_8_reyes=True)
    mano = sorted(random.sample(baraja, 4), reverse=True)
    
    print(f"Mano de prueba: {formatear_mano(mano)}\n")
    
    # 1. Estadísticas estáticas
    print("1️⃣  ESTADÍSTICAS ESTÁTICAS (precalculadas):")
    import pandas as pd
    try:
        df = pd.read_csv('/workspaces/Probabilidades-Mus/calculadora_probabilidades_mus/resultados_8reyes.csv')
        mano_str = str(mano)
        fila = df[df['mano'] == mano_str]
        
        if not fila.empty:
            print(f"    GRANDE: {fila['probabilidad_grande'].values[0]:.2%}")
            print(f"    PARES:  {fila['probabilidad_pares'].values[0]:.2%}")
        else:
            print("    (Mano no encontrada en CSV)")
    except:
        print("    (Error cargando CSV)")
    
    # 2. Simulación dinámica
    print("\n2️⃣  SIMULACIÓN DINÁMICA (con compañero aleatorio):")
    mano_companero = sorted(random.sample([c for c in baraja if c not in mano], 4), reverse=True)
    print(f"    Compañero: {formatear_mano(mano_companero)}")
    
    resultado = simular_con_companero(mano, mano_companero, baraja, iteraciones=10000)
    print(f"    GRANDE: {resultado['probabilidad_grande']:.2%} (condicionado)")
    print(f"    PARES:  {resultado['probabilidad_pares']:.2%} (condicionado)")
    
    # 3. Motor de decisión
    print("\n3️⃣  MOTOR DE DECISIÓN IA:")
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal', silent=True)
    decision, prob, ev, _ = motor.decidir(mano)
    
    print(f"    Valor Esperado (EV): {ev:.4f}")
    print(f"    Decisión: {'CORTAR' if decision else 'MUS'} ({prob:.1%})")
    
    print("\n📊 INTERPRETACIÓN:")
    print("   • Estáticas: Probabilidades a priori (sin info adicional)")
    print("   • Dinámicas: Probabilidades a posteriori (con compañero)")
    print("   • Motor IA:  Decisión basada en EV total y umbral μ")
    
    print("\n" + "=" * 70)


def menu_principal():
    """Muestra el menú principal y gestiona las opciones."""
    
    print("\n")
    imprimir_separador("DEMO INTERACTIVA - SISTEMA DE ANÁLISIS DE MUS")
    print("\nEste programa demuestra las 3 funcionalidades principales:\n")
    print("  1. Análisis Estático (probabilidades precalculadas)")
    print("  2. Simulación Dinámica (con mano del compañero)")
    print("  3. Motor de Decisión IA (decide CORTAR/MUS con EV)")
    print("  4. Análisis Detallado (razonamiento completo del motor)")
    print("  5. Comparación Completa (los 3 sistemas sobre 1 mano)")
    print("\n  0. Salir")
    
    while True:
        print("\n")
        opcion = input("Elige una demo [0-5]: ").strip()
        
        if opcion == '0':
            print("\n¡Hasta luego! 👋\n")
            break
        elif opcion == '1':
            demo_estatica()
        elif opcion == '2':
            demo_dinamica()
        elif opcion == '3':
            demo_motor_ia()
        elif opcion == '4':
            demo_decision_detallada()
        elif opcion == '5':
            demo_comparacion()
        else:
            print("❌ Opción inválida. Elige 0-5.")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario. ¡Hasta luego! 👋\n")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        raise
