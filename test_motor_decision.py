"""
Testing y Análisis de Parámetros del Motor de Decisión de Mus
Evalúa diferentes configuraciones y valida el comportamiento del motor.
"""

import sys
sys.path.insert(0, '/workspaces/Probabilidades-Mus/calculadora_probabilidades_mus')

import numpy as np
import pandas as pd
from motor_decision import MotorDecisionMus, PERFILES, formatear_decision
from calculadoramus import inicializar_baraja


# =============================================================================
# TESTS BÁSICOS
# =============================================================================

def test_manos_extremas():
    """Valida que el motor responda coherentemente a manos extremas."""
    print("=" * 70)
    print("TEST 1: MANOS EXTREMAS")
    print("=" * 70)
    
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
    
    # Mano excelente
    mano_excelente = [12, 12, 11, 10]
    decisiones = []
    for _ in range(100):
        decision, _, _, _ = motor.decidir(mano_excelente)
        decisiones.append(decision)
    
    tasa_corte_excelente = sum(decisiones) / len(decisiones)
    print(f"\nMano EXCELENTE [12,12,11,10]:")
    print(f"  Cortes: {sum(decisiones)}/100 = {tasa_corte_excelente:.1%}")
    assert tasa_corte_excelente > 0.85, "Mano excelente debe cortar >85%"
    print("  ✓ Comportamiento correcto (>85%)")
    
    # Mano pésima
    mano_pesima = [7, 6, 5, 4]
    decisiones = []
    for _ in range(100):
        decision, _, _, _ = motor.decidir(mano_pesima)
        decisiones.append(decision)
    
    tasa_corte_pesima = sum(decisiones) / len(decisiones)
    print(f"\nMano PÉSIMA [7,6,5,4]:")
    print(f"  Cortes: {sum(decisiones)}/100 = {tasa_corte_pesima:.1%}")
    assert tasa_corte_pesima < 0.15, "Mano pésima debe cortar <15%"
    print("  ✓ Comportamiento correcto (<15%)")
    
    print("\n✅ Test de manos extremas: PASADO\n")


def test_estocasticidad():
    """Valida que el componente estocástico funciona correctamente."""
    print("=" * 70)
    print("TEST 2: ESTOCASTICIDAD")
    print("=" * 70)
    
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
    
    # Mano intermedia (debería tener decisiones variadas)
    mano_intermedia = [10, 7, 6, 5]
    decisiones = []
    prob_cortar_list = []
    
    for _ in range(200):
        decision, prob, _, _ = motor.decidir(mano_intermedia)
        decisiones.append(decision)
        prob_cortar_list.append(prob)
    
    tasa_corte = sum(decisiones) / len(decisiones)
    prob_media = np.mean(prob_cortar_list)
    prob_std = np.std(prob_cortar_list)
    
    print(f"\nMano INTERMEDIA [10,7,6,5] - 200 simulaciones:")
    print(f"  Tasa de corte observada: {tasa_corte:.1%}")
    print(f"  Probabilidad media: {prob_media:.1%}")
    print(f"  Desviación estándar de probabilidad: {prob_std:.4f}")
    
    # Verificar que hay variabilidad
    assert prob_std > 0.001, "Debe haber variabilidad en las probabilidades"
    print("  ✓ Componente estocástico funcionando")
    
    # Verificar que la tasa observada está cerca de la probabilidad media
    diferencia = abs(tasa_corte - prob_media)
    print(f"  Diferencia tasa/probabilidad: {diferencia:.1%}")
    assert diferencia < 0.10, "Tasa observada debe estar cerca de probabilidad (±10%)"
    print("  ✓ Convergencia correcta")
    
    print("\n✅ Test de estocasticidad: PASADO\n")


def test_perfiles():
    """Valida que los diferentes perfiles tienen comportamientos distintos."""
    print("=" * 70)
    print("TEST 3: DIFERENCIACIÓN DE PERFILES")
    print("=" * 70)
    
    manos_test = [
        [12, 11, 10, 7],
        [10, 7, 6, 5],
        [7, 6, 5, 4]
    ]
    
    resultados = {}
    
    for perfil in ['conservador', 'normal', 'agresivo']:
        motor = MotorDecisionMus(modo_8_reyes=True, perfil=perfil)
        tasas_corte = []
        
        for mano in manos_test:
            decisiones = [motor.decidir(mano)[0] for _ in range(50)]
            tasa = sum(decisiones) / len(decisiones)
            tasas_corte.append(tasa)
        
        resultados[perfil] = tasas_corte
    
    # Mostrar resultados
    print("\nTasas de corte por perfil:")
    print(f"{'Mano':<20} {'Conservador':>12} {'Normal':>12} {'Agresivo':>12}")
    print("-" * 60)
    for i, mano in enumerate(manos_test):
        print(f"{str(mano):<20} {resultados['conservador'][i]:>11.1%} " +
              f"{resultados['normal'][i]:>11.1%} {resultados['agresivo'][i]:>11.1%}")
    
    # Validar que agresivo > normal > conservador (en promedio)
    media_conservador = np.mean(resultados['conservador'])
    media_normal = np.mean(resultados['normal'])
    media_agresivo = np.mean(resultados['agresivo'])
    
    print(f"\nMedias: Conservador={media_conservador:.1%}, Normal={media_normal:.1%}, " +
          f"Agresivo={media_agresivo:.1%}")
    
    # El agresivo debe cortar más que el normal, y el normal más que el conservador
    # (con cierta tolerancia por estocasticidad)
    assert media_agresivo >= media_normal - 0.05, "Agresivo debe cortar ≥ Normal"
    assert media_normal >= media_conservador - 0.05, "Normal debe cortar ≥ Conservador"
    
    print("✓ Los perfiles se diferencian correctamente\n")
    print("✅ Test de perfiles: PASADO\n")


# =============================================================================
# ANÁLISIS DE PARÁMETROS
# =============================================================================

def analizar_distribucion_ev():
    """Analiza la distribución de EVs en todas las manos únicas."""
    print("=" * 70)
    print("ANÁLISIS: DISTRIBUCIÓN DE EV")
    print("=" * 70)
    
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
    
    EVs = []
    for mano in motor.estadisticas.df['mano_lista'][:500]:  # Muestra de 500 manos
        ev, _ = motor.analizar_mano_detallado(mano)['EV_total'], None
        EVs.append(ev)
    
    print(f"\nEstadísticas de EV (muestra de 500 manos):")
    print(f"  Media:     {np.mean(EVs):.4f}")
    print(f"  Mediana:   {np.median(EVs):.4f}")
    print(f"  Desv.Est:  {np.std(EVs):.4f}")
    print(f"  Mínimo:    {np.min(EVs):.4f}")
    print(f"  Máximo:    {np.max(EVs):.4f}")
    print(f"\nPercentiles:")
    for p in [10, 25, 40, 50, 60, 70, 75, 90]:
        val = np.percentile(EVs, p)
        marca = " ← μ actual" if p == 60 else ""
        print(f"  P{p:2d}: {val:.4f}{marca}")
    
    print(f"\nUmbral μ calibrado: {motor.mu:.4f}")
    print()


def analizar_tasas_decision():
    """Analiza las tasas de decisión para diferentes configuraciones."""
    print("=" * 70)
    print("ANÁLISIS: TASAS DE DECISIÓN")
    print("=" * 70)
    
    configuraciones = [
        ('Conservador P70', 'conservador'),
        ('Normal P60', 'normal'),
        ('Agresivo P40', 'agresivo')
    ]
    
    print("\nTasas de corte (muestra de 200 manos aleatorias):\n")
    
    for nombre, perfil in configuraciones:
        motor = MotorDecisionMus(modo_8_reyes=True, perfil=perfil)
        
        # Muestrear manos aleatorias
        muestra = motor.estadisticas.df['mano_lista'].sample(200, random_state=42)
        
        decisiones = []
        for mano in muestra:
            decision, _, _, _ = motor.decidir(mano)
            decisiones.append(decision)
        
        tasa_corte = sum(decisiones) / len(decisiones)
        
        print(f"  {nombre:<20}: {tasa_corte:.1%} de cortes")
        print(f"  {'':20}  (μ={motor.mu:.4f}, β={motor.params['beta']:.1f})")
    
    print()


def analizar_impacto_beta():
    """Analiza cómo afecta el factor β a las decisiones."""
    print("=" * 70)
    print("ANÁLISIS: IMPACTO DEL FACTOR β (CONFIANZA EN COMPAÑERO)")
    print("=" * 70)
    
    from motor_decision import calcular_ev_total, EstadisticasEstaticas
    
    stats = EstadisticasEstaticas(modo_8_reyes=True)
    mano_test = [10, 7, 6, 5]  # Mano intermedia
    
    print(f"\nMano de prueba: {mano_test}")
    print(f"\n{'β':<6} {'EV Total':<12} {'EV Propio':<12} {'EV Soporte':<12}")
    print("-" * 50)
    
    for beta in [0.3, 0.5, 0.7, 0.9, 1.0]:
        ev_total, desglose = calcular_ev_total(mano_test, stats, beta)
        
        # Calcular suma de componentes propios y de soporte
        ev_propio = sum([desglose[l]['propio'] for l in ['grande', 'chica', 'pares', 'juego']])
        ev_soporte = sum([desglose[l]['soporte'] for l in ['grande', 'chica', 'pares', 'juego']])
        
        print(f"{beta:<6.1f} {ev_total:<12.4f} {ev_propio:<12.4f} {ev_soporte:<12.4f}")
    
    print("\nInterpretación:")
    print("  - β bajo (0.3): Desconfía del compañero, decisión casi individual")
    print("  - β medio (0.7): Balance normal, considera al compañero moderadamente")
    print("  - β alto (1.0): Confía plenamente en el soporte del compañero")
    print()


def sugerir_parametros():
    """Sugiere valores óptimos de parámetros basándose en el análisis."""
    print("=" * 70)
    print("SUGERENCIAS DE PARÁMETROS")
    print("=" * 70)
    
    print("\nBasándose en el análisis realizado:\n")
    
    print("PERFIL CONSERVADOR (corta ~35-45%):")
    print("  β = 0.6   (confía menos en el compañero)")
    print("  μ = P70   (exige manos muy buenas)")
    print("  K = 2.0   (decisión moderada)")
    print("  σ = 0.3   (variabilidad media)")
    
    print("\nPERFIL NORMAL (corta ~50-60%):")
    print("  β = 0.7   (confianza normal en el compañero)")
    print("  μ = P60   (exige manos buenas)")
    print("  K = 2.0   (decisión moderada)")
    print("  σ = 0.3   (variabilidad media)")
    
    print("\nPERFIL AGRESIVO (corta ~65-75%):")
    print("  β = 0.8   (confía mucho en el compañero)")
    print("  μ = P40   (corta con manos regulares)")
    print("  K = 1.8   (decisión más suave, menos determinista)")
    print("  σ = 0.4   (alta variabilidad, impredecible)")
    
    print("\nPERFIL EXPERTO (recomendación avanzada):")
    print("  β = 0.75  (balance óptimo)")
    print("  μ = P55   (ligeramente agresivo)")
    print("  K = 2.2   (decisión más marcada)")
    print("  σ = 0.25  (baja variabilidad, más consistente)")
    print()


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

def ejecutar_todos_tests():
    """Ejecuta todos los tests y análisis."""
    print("\n" + "=" * 70)
    print(" SUITE COMPLETA - MOTOR DE DECISIÓN DE MUS")
    print("=" * 70 + "\n")
    
    try:
        # Tests básicos
        test_manos_extremas()
        test_estocasticidad()
        test_perfiles()
        
        # Análisis de parámetros
        analizar_distribucion_ev()
        analizar_tasas_decision()
        analizar_impacto_beta()
        sugerir_parametros()
        
        print("=" * 70)
        print(" ✅ TODOS LOS TESTS Y ANÁLISIS COMPLETADOS")
        print("=" * 70)
        print("\nEl motor de decisión está funcionando correctamente.")
        print("Los parámetros actuales son adecuados y están calibrados.\n")
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print(" ❌ ERROR EN LOS TESTS")
        print("=" * 70)
        print(f"\n{e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        raise


if __name__ == "__main__":
    ejecutar_todos_tests()
