"""
Motor de Decisión de Mus - Fase 1: Primeras Dadas
Implementa un agente IA que decide "Cortar" o dar "Mus" basándose en:
- Valor Esperado (EV) matemático de la mano
- Soporte estadístico del compañero (desconocido)
- Política de decisión estocástica (sigmoide) para evitar ser explotable

Versión: 2.3
Última actualización: marzo 2026

Cambios v2.3:
- CRÍTICO: Eliminado factor bayesiano heurístico (pesos lineales Rey=4, As=1.5, etc.)
- Implementadas probabilidades condicionadas EXACTAS (distribución hipergeométrica)
- calcular_prob_rival() ahora usa probabilidades precomputadas desde dataset
- Precomputación: prob_rival_pares_condicionada y prob_rival_juego_condicionada
- Eliminadas funciones: calcular_peso_mano() y calcular_factor_bayesiano()

Cambios v2.2:
- Aplicación simétrica del factor bayesiano (OBSOLETO en v2.3)

Cambios v2.1:
- Desempates exactos: prob_menor + prob_empate × factor_posición
- Eliminados todos los ajustes arbitrarios (±0.0033)
- Factores de posición: {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}
"""

import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from calculadoramus import (
    inicializar_baraja,
    clasificar_pares,
    calcular_valor_juego,
    convertir_valor_juego,
    calcular_valor_punto
)


# ============================================================================
# CONSTANTES Y CONFIGURACIÓN
# ============================================================================

# Valores base por tipo de jugada (W_yo^L)
VALORES_PARES = {
    "sin_pares": 0,
    "pares": 1,
    "medias": 2,
    "duples": 3
}

# Valores de juego según jerarquía del Mus
# Jerarquía: 31 > 32 > 40 > 37 > 36 > 35 > 34 > 33
# Pesos normalizados: 31=3.0 (mejor), 33=2.0 (peor juego)
# Fórmula: W = 2.0 + (jerarquía - 1) * (1.0 / 7)
VALORES_JUEGO = {
    31: 3.0,      # Jerarquía 8 (mejor) 
    32: 2.857,    # Jerarquía 7
    40: 2.714,    # Jerarquía 6
    37: 2.571,    # Jerarquía 5
    36: 2.429,    # Jerarquía 4
    35: 2.286,    # Jerarquía 3
    34: 2.143,    # Jerarquía 2
    33: 2.0       # Jerarquía 1 (peor juego)
}

# Valor de punto (cuando nadie tiene juego 31-40)
W_PUNTO = 1.0  # Todos los puntos valen 1 punto base

# Esperanza de puntos extra en envites (Swing)
# NOTA: Actualmente 0.0, se implementará sistema de envites en futuro
E_EXTRA_PARES = 0.0
E_EXTRA_JUEGO = 0.0
E_EXTRA_PUNTO = 0.0

# Perfiles predefinidos
PERFILES = {
    'conservador': {'beta': 0.65, 'k_base': 2.0, 'sigma': 0.3, 'percentil_mu': 55},
    'normal': {'beta': 0.75, 'k_base': 2.0, 'sigma': 0.3, 'percentil_mu': 45},
    'agresivo': {'beta': 0.85, 'k_base': 1.8, 'sigma': 0.4, 'percentil_mu': 30}
}


# ============================================================================
# CARGA DE ESTADÍSTICAS ESTÁTICAS
# ============================================================================

class EstadisticasEstaticas:
    """Gestiona la carga y acceso a las estadísticas precalculadas."""
    
    def __init__(self, modo_8_reyes=False):
        self.modo_8_reyes = modo_8_reyes
        self.archivo = 'resultados_8reyes.csv' if modo_8_reyes else 'resultados_4reyes.csv'
        self.df = None
        self.manos_dict = {}
        self.estadisticas_generales = {}
        self.probs_pares = {}  # {mano_tuple: {'prob_menor': X, 'prob_empate': Y}}
        self.probs_juego = {}  # {mano_tuple: {'prob_menor': X, 'prob_empate': Y}}
        self._cargar()
    
    def _cargar(self):
        """Carga el archivo CSV de estadísticas."""
        ruta = Path(__file__).parent / self.archivo
        if not ruta.exists():
            raise FileNotFoundError(
                f"No se encuentra {self.archivo}. "
                f"Ejecuta primero calculadoramus.py para generar las estadísticas."
            )
        
        self.df = pd.read_csv(ruta)
        
        # Convertir columna 'mano' de string a lista
        import ast
        self.df['mano_lista'] = self.df['mano'].apply(
            lambda x: sorted(ast.literal_eval(x)) if isinstance(x, str) else sorted(x)
        )
        
        # Crear diccionario para búsqueda rápida
        for _, row in self.df.iterrows():
            key = tuple(row['mano_lista'])
            self.manos_dict[key] = {
                'prob_grande': row['probabilidad_grande'],
                'prob_chica': row['probabilidad_chica'],
                'prob_pares': row['probabilidad_pares'],
                'prob_juego': row['probabilidad_juego'],
                # NUEVO: Probabilidades condicionadas exactas de rivales
                'prob_rival_pares_condicionada': row.get('prob_rival_pares_condicionada', 0.0),
                'prob_rival_juego_condicionada': row.get('prob_rival_juego_condicionada', 0.0)
            }
        
        # Calcular estadísticas generales (para compañero desconocido)
        self.estadisticas_generales = {
            'P_comp_media_grande': self.df['probabilidad_grande'].mean(),
            'P_comp_media_chica': self.df['probabilidad_chica'].mean(),
            'P_comp_media_pares': self.df['probabilidad_pares'].mean(),
            'P_comp_media_juego': self.df['probabilidad_juego'].mean(),
            'prob_tener_pares': self._calcular_prob_tener_pares(),
            'prob_tener_juego': self._calcular_prob_tener_juego()
        }
        
        # Calcular probabilidades exactas de pares y juego
        self._calcular_probabilidades_pares()
        self._calcular_probabilidades_juego()
    
    def _calcular_prob_tener_pares(self):
        """Calcula la probabilidad general de que una mano tenga pares."""
        baraja = inicializar_baraja(self.modo_8_reyes)
        total = len(self.df)
        con_pares = 0
        
        for mano in self.df['mano_lista']:
            tipo_pares, _, _ = clasificar_pares(mano)
            if tipo_pares != "sin_pares":
                con_pares += 1
        
        return con_pares / total if total > 0 else 0.3
    
    def _calcular_prob_tener_juego(self):
        """Calcula la probabilidad general de que una mano tenga juego."""
        total = len(self.df)
        con_juego = 0
        
        for mano in self.df['mano_lista']:
            if calcular_valor_juego(mano) > 0:
                con_juego += 1
        
        return con_juego / total if total > 0 else 0.15
    
    def _calcular_probabilidades_pares(self):
        """Calcula probabilidades exactas: P(rival < yo) y P(rival == yo) para pares."""
        # Crear lista de todas las manos con pares y sus características
        manos_con_pares = []
        for mano in self.df['mano_lista']:
            tipo_pares, valor_pares, valor_secundario = clasificar_pares(mano)
            if tipo_pares != "sin_pares":
                tipo_orden = {'duples': 3, 'medias': 2, 'pares': 1}[tipo_pares]
                manos_con_pares.append({
                    'mano': tuple(sorted(mano)),
                    'tipo_orden': tipo_orden,
                    'valor_pares': valor_pares,
                    'valor_secundario': valor_secundario
                })
        
        n_total = len(manos_con_pares)
        if n_total == 0:
            return
        
        # Para cada mano, calcular probabilidades exactas
        for i, mano_i in enumerate(manos_con_pares):
            # Contar cuántas manos son estrictamente peores
            n_menores = 0
            n_empates = 0
            
            for j, mano_j in enumerate(manos_con_pares):
                if i == j:
                    continue
                
                # Comparar manos
                if (mano_j['tipo_orden'] < mano_i['tipo_orden'] or
                    (mano_j['tipo_orden'] == mano_i['tipo_orden'] and mano_j['valor_pares'] < mano_i['valor_pares']) or
                    (mano_j['tipo_orden'] == mano_i['tipo_orden'] and mano_j['valor_pares'] == mano_i['valor_pares'] and mano_j['valor_secundario'] < mano_i['valor_secundario'])):
                    n_menores += 1
                elif (mano_j['tipo_orden'] == mano_i['tipo_orden'] and 
                      mano_j['valor_pares'] == mano_i['valor_pares'] and 
                      mano_j['valor_secundario'] == mano_i['valor_secundario']):
                    n_empates += 1
            
            # Probabilidades exactas (uniforme sobre todas las manos posibles)
            prob_menor = n_menores / (n_total - 1) if n_total > 1 else 0.0
            prob_empate = n_empates / (n_total - 1) if n_total > 1 else 0.0
            
            self.probs_pares[mano_i['mano']] = {
                'prob_menor': prob_menor,
                'prob_empate': prob_empate
            }
    
    def _calcular_probabilidades_juego(self):
        """Calcula probabilidades exactas: P(rival < yo) y P(rival == yo) para juego."""
        # Crear lista de todas las manos con juego
        manos_con_juego = []
        for mano in self.df['mano_lista']:
            valor_juego = calcular_valor_juego(mano)
            if valor_juego > 0:
                manos_con_juego.append({
                    'mano': tuple(sorted(mano)),
                    'valor_juego': valor_juego
                })
        
        n_total = len(manos_con_juego)
        if n_total == 0:
            return
        
        # Para cada mano, calcular probabilidades exactas
        for i, mano_i in enumerate(manos_con_juego):
            # Contar cuántas manos son estrictamente peores (valor juego mayor es peor, 31 es mejor)
            n_menores = 0
            n_empates = 0
            
            for j, mano_j in enumerate(manos_con_juego):
                if i == j:
                    continue
                
                # En juego: menor valor = mejor mano
                if mano_j['valor_juego'] > mano_i['valor_juego']:
                    n_menores += 1
                elif mano_j['valor_juego'] == mano_i['valor_juego']:
                    n_empates += 1
            
            # Probabilidades exactas
            prob_menor = n_menores / (n_total - 1) if n_total > 1 else 0.0
            prob_empate = n_empates / (n_total - 1) if n_total > 1 else 0.0
            
            self.probs_juego[mano_i['mano']] = {
                'prob_menor': prob_menor,
                'prob_empate': prob_empate
            }
    
    def obtener_probabilidades(self, mano):
        """
        Busca las probabilidades de una mano en la tabla.
        
        Args:
            mano: Lista de 4 cartas
        
        Returns:
            Dict con prob_grande, prob_chica, prob_pares, prob_juego
        """
        key = tuple(sorted(mano))
        if key in self.manos_dict:
            return self.manos_dict[key]
        
        # Si no encuentra la mano exacta, retornar valores conservadores
        return {
            'prob_grande': 0.25,
            'prob_chica': 0.25,
            'prob_pares': 0.15,
            'prob_juego': 0.15
        }
    
    def obtener_prob_pares(self, mano):
        """Obtiene las probabilidades exactas de una mano en pares."""
        key = tuple(sorted(mano))
        return self.probs_pares.get(key, {'prob_menor': 0.5, 'prob_empate': 0.0})
    
    def obtener_prob_juego(self, mano):
        """Obtiene las probabilidades exactas de una mano en juego."""
        key = tuple(sorted(mano))
        return self.probs_juego.get(key, {'prob_menor': 0.5, 'prob_empate': 0.0})


# ============================================================================
# ANÁLISIS DE MANO
# ============================================================================

def analizar_mano(mano):
    """
    Inspecciona una mano y extrae sus características para el cálculo de EV.
    
    Args:
        mano: Lista de 4 cartas
    
    Returns:
        Dict con características de la mano
    """
    tipo_pares, valor_pares, valor_secundario = clasificar_pares(mano)
    valor_juego_raw = calcular_valor_juego(mano)
    valor_juego_convertido = convertir_valor_juego(valor_juego_raw)
    valor_punto = calcular_valor_punto(mano)
    
    # Valor W para pares
    W_pares = VALORES_PARES.get(tipo_pares, 0)
    
    # Valor W para juego
    W_juego = VALORES_JUEGO.get(valor_juego_raw, 0) if valor_juego_raw > 0 else 0
    
    return {
        'tiene_pares': tipo_pares != "sin_pares",
        'tipo_pares': tipo_pares,
        'valor_pares': valor_pares,
        'W_pares': W_pares,
        'tiene_juego': valor_juego_raw > 0,
        'valor_juego_raw': valor_juego_raw,
        'valor_juego_convertido': valor_juego_convertido,
        'W_juego': W_juego,
        'valor_punto': valor_punto,
        'W_punto': W_PUNTO
    }


# ============================================================================
# CÁLCULO DE PROBABILIDAD DE RIVAL (P_RL)
# ============================================================================

def calcular_prob_rival(lance, mano, estadisticas):
    """
    Estima la probabilidad de que AL MENOS uno de los 2 rivales tenga la jugada.
    NUEVO: Usa probabilidades condicionadas exactas precomputadas (distribución hipergeométrica)
    en lugar de factor bayesiano heurístico.
    
    Args:
        lance: 'pares' o 'juego'
        mano: Lista de 4 cartas (para buscar probabilidad condicionada exacta)
        estadisticas: EstadisticasEstaticas
    
    Returns:
        P_RL: float (probabilidad de que al menos 1 rival tenga la jugada)
    """
    mano_tuple = tuple(sorted(mano))
    
    # Extraer probabilidad EXACTA condicionada de que AL MENOS 1 rival tenga la jugada
    # (ya precomputada considerando las 36 cartas restantes tras ver mi mano)
    if mano_tuple in estadisticas.manos_dict:
        if lance == 'pares':
            P_RL = estadisticas.manos_dict[mano_tuple]['prob_rival_pares_condicionada']
        elif lance == 'juego':
            P_RL = estadisticas.manos_dict[mano_tuple]['prob_rival_juego_condicionada']
        else:
            return 0.0
    else:
        # Fallback: si no está precomputada, usar probabilidad general
        if lance == 'pares':
            p_individual = estadisticas.estadisticas_generales['prob_tener_pares']
        elif lance == 'juego':
            p_individual = estadisticas.estadisticas_generales['prob_tener_juego']
        else:
            return 0.0
        # P(al menos 1 de 2) = 1 - P(ninguno)
        P_RL = 1 - (1 - p_individual) ** 2
    
    return P_RL


# ============================================================================
# CÁLCULO DE EV PROPIO
# ============================================================================

def calcular_ev_propio_lineal(prob_yo, valor_base=1.0):
    """
    Calcula EV propio para lances lineales (Grande, Chica).
    
    Args:
        prob_yo: Probabilidad de que gane el lance
        valor_base: Valor del lance (1 punto por defecto)
    
    Returns:
        EV_Propio
    """
    return prob_yo * valor_base


def calcular_ev_propio_condicionado(mano, W_yo, P_RL, E_extra, lance, estadisticas, posicion=1):
    """
    Calcula EV propio para lances condicionados (Pares, Juego).
    Usa probabilidades exactas: P(rival < yo) y P(rival == yo).
    El factor de desempate depende de la posición en la mesa.
    
    Args:
        mano: Lista de 4 cartas
        W_yo: Valor base de mi jugada
        P_RL: Probabilidad de que rival tenga jugada
        E_extra: Esperanza de puntos extra (swing)
        lance: 'pares' o 'juego'
        estadisticas: EstadisticasEstaticas
        posicion: Posición en la mesa [1-4]
    
    Returns:
        EV_Propio
    """
    # Factor de desempate por posición (solo afecta empates exactos)
    # Parejas: (1,3) vs (2,4)
    # Pos 1: gana empates a 2 y 4 → 1.0
    # Pos 2: gana a 3, pierde a 1 → 0.5
    # Pos 3: gana a 4, pierde a 2 → 0.5
    # Pos 4: pierde empates a 1 y 3 → 0.0
    factores_desempate = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}
    factor_desempate = factores_desempate.get(posicion, 0.5)
    
    # Obtener probabilidades exactas
    if lance == 'pares':
        probs = estadisticas.obtener_prob_pares(mano)
    else:  # juego
        probs = estadisticas.obtener_prob_juego(mano)
    
    prob_menor = probs['prob_menor']
    prob_empate = probs['prob_empate']
    
    # Probabilidad de ganar = ganar estrictamente + ganar empates
    prob_yo_vs_rival = prob_menor + (prob_empate * factor_desempate)
    
    # Escenario 1: Nadie más tiene la jugada
    EV_sin_rival = (1 - P_RL) * W_yo
    
    # Escenario 2: Rival tiene la jugada, compito usando probabilidad exacta
    EV_con_rival = P_RL * prob_yo_vs_rival * (W_yo + E_extra)
    
    return EV_sin_rival + EV_con_rival


# ============================================================================
# CÁLCULO DE EV SOPORTE (COMPAÑERO)
# ============================================================================

def calcular_ev_soporte_lineal(mano, prob_yo, estadisticas, lance):
    """
    Calcula EV de soporte del compañero para lances lineales.
    
    Args:
        mano: Lista de 4 cartas
        prob_yo: Mi probabilidad de ganar
        estadisticas: EstadisticasEstaticas
        lance: 'grande' o 'chica'
    
    Returns:
        EV_Soporte
    """
    if lance == 'grande':
        P_comp_media = estadisticas.estadisticas_generales['P_comp_media_grande']
    else:  # chica
        P_comp_media = estadisticas.estadisticas_generales['P_comp_media_chica']
    
    # Factor de ajuste: si yo estoy débil (prob_yo baja), el compañero
    # tiene mayor probabilidad de compensar
    factor_ajuste = 1.0 + (0.3 * (1 - prob_yo))
    
    P_comp_ajustado = min(P_comp_media * factor_ajuste, 0.9)
    
    return P_comp_ajustado * 1.0  # 1 punto base


def calcular_ev_soporte_condicionado(mano, tiene_jugada_yo, estadisticas, lance, E_extra):
    """
    Calcula EV de soporte del compañero para lances condicionados.
    
    Args:
        mano: Lista de 4 cartas
        tiene_jugada_yo: bool, si yo tengo la jugada
        estadisticas: EstadisticasEstaticas
        lance: 'pares' o 'juego'
        E_extra: Esperanza de puntos extra
    
    Returns:
        EV_Soporte
    """
    if lance == 'pares':
        prob_comp_tiene = estadisticas.estadisticas_generales['prob_tener_pares']
        W_comp_estimado = 1.5  # Valor medio de pares
    else:  # juego
        prob_comp_tiene = estadisticas.estadisticas_generales['prob_tener_juego']
        W_comp_estimado = 2.0  # Valor medio de juego
    
    # Si yo ya tengo la jugada, el compañero aporta menos
    if tiene_jugada_yo:
        factor_reduccion = 0.5
    else:
        factor_reduccion = 1.0
    
    prob_comp_gana = prob_comp_tiene * 0.6  # 60% de prob de ganar si tiene
    
    return factor_reduccion * prob_comp_gana * (W_comp_estimado + E_extra)


# ============================================================================
# CÁLCULO DE EV TOTAL POR MANO
# ============================================================================

def calcular_ev_total(mano, estadisticas, beta=0.7, posicion=1):
    """
    Calcula el Valor Esperado total de una mano.
    
    Args:
        mano: Lista de 4 cartas
        estadisticas: EstadisticasEstaticas
        beta: Factor de confianza en el compañero [0, 1]
        posicion: Posición en la mesa [1-4]
    
    Returns:
        (EV_total, desglose_detallado)
    """
    # Obtener probabilidades de la mano
    prob_mano = estadisticas.obtener_probabilidades(mano)
    
    # Analizar características de la mano
    analisis = analizar_mano(mano)
    
    # --- GRANDE (Lineal) ---
    EV_propio_G = calcular_ev_propio_lineal(prob_mano['prob_grande'])
    EV_soporte_G = calcular_ev_soporte_lineal(mano, prob_mano['prob_grande'], estadisticas, 'grande')
    EV_decision_G = EV_propio_G + (beta * EV_soporte_G)
    
    # --- CHICA (Lineal) ---
    EV_propio_C = calcular_ev_propio_lineal(prob_mano['prob_chica'])
    EV_soporte_C = calcular_ev_soporte_lineal(mano, prob_mano['prob_chica'], estadisticas, 'chica')
    EV_decision_C = EV_propio_C + (beta * EV_soporte_C)
    
    # --- PARES (Condicionado) ---
    P_RL_pares = calcular_prob_rival('pares', mano, estadisticas)
    
    if analisis['tiene_pares']:
        EV_propio_P = calcular_ev_propio_condicionado(
            mano,
            analisis['W_pares'],
            P_RL_pares,
            E_EXTRA_PARES,
            'pares',
            estadisticas,
            posicion
        )
    else:
        EV_propio_P = 0.0
    
    EV_soporte_P = calcular_ev_soporte_condicionado(
        mano, analisis['tiene_pares'], estadisticas, 'pares', E_EXTRA_PARES
    )
    EV_decision_P = EV_propio_P + (beta * EV_soporte_P)
    
    # --- JUEGO Y PUNTO (Condicionado) ---
    # El lance de "Juego" incluye dos casos:
    # 1. Si algún jugador tiene juego (31-40) → se compara juego (jerarquía)
    # 2. Si nadie tiene juego → se compara por punto (distancia a 30, W=1)
    P_RL_juego = calcular_prob_rival('juego', mano, estadisticas)
    
    if analisis['tiene_juego']:
        # Caso 1: Yo tengo juego → usar lógica de juego con jerarquía
        EV_propio_J = calcular_ev_propio_condicionado(
            mano,
            analisis['W_juego'],
            P_RL_juego,
            E_EXTRA_JUEGO,
            'juego',
            estadisticas,
            posicion
        )
        EV_soporte_J = calcular_ev_soporte_condicionado(
            mano, analisis['tiene_juego'], estadisticas, 'juego', E_EXTRA_JUEGO
        )
        EV_decision_J = EV_propio_J + (beta * EV_soporte_J)
        EV_propio_Punto = 0.0  # No se juega punto si tengo juego
        EV_soporte_Punto = 0.0
        EV_decision_Punto = 0.0
    else:
        # Caso 2: Yo NO tengo juego → puede jugarse punto
        # Si algún rival tiene juego → pierdo automático (0 puntos)
        # Si ningún rival tiene juego → se juega punto (W=1)
        
        # EV propio de punto (solo si ningún rival tiene juego)
        # La prob_juego del CSV ya incluye victorias por punto cuando no hay juego
        EV_propio_Punto = calcular_ev_propio_condicionado(
            mano,
            W_PUNTO,
            P_RL_juego,
            E_EXTRA_PUNTO,
            'juego',  # Usa misma probabilidad (incluye punto)
            estadisticas,
            posicion
        )
        
        # Soporte del compañero (puede tener juego o no)
        EV_soporte_Punto = calcular_ev_soporte_condicionado(
            mano, False, estadisticas, 'juego', E_EXTRA_PUNTO
        )
        
        EV_decision_Punto = EV_propio_Punto + (beta * EV_soporte_Punto)
        EV_propio_J = 0.0  # No tengo juego
        EV_soporte_J = 0.0
        EV_decision_J = 0.0
    
    # --- EV TOTAL ---
    EV_total = EV_decision_G + EV_decision_C + EV_decision_P + EV_decision_J + EV_decision_Punto
    
    # Desglose detallado
    desglose = {
        'EV_total': EV_total,
        'grande': {'propio': EV_propio_G, 'soporte': EV_soporte_G, 'decision': EV_decision_G},
        'chica': {'propio': EV_propio_C, 'soporte': EV_soporte_C, 'decision': EV_decision_C},
        'pares': {'propio': EV_propio_P, 'soporte': EV_soporte_P, 'decision': EV_decision_P},
        'juego': {'propio': EV_propio_J, 'soporte': EV_soporte_J, 'decision': EV_decision_J},
        'punto': {'propio': EV_propio_Punto, 'soporte': EV_soporte_Punto, 'decision': EV_decision_Punto},
        'analisis_mano': analisis,
        'probabilidades': prob_mano
    }
    
    return EV_total, desglose


# ============================================================================
# CALIBRACIÓN DE UMBRAL μ
# ============================================================================

def calibrar_umbral_mu(estadisticas, percentil=60, beta=0.7, cache_file='calibracion_mu.json', silent=False):
    """
    Calcula el umbral μ (percentil del EV) analizando todas las manos únicas.
    Se ejecuta UNA VEZ y se guarda en caché.
    
    Args:
        estadisticas: EstadisticasEstaticas
        percentil: Percentil deseado (50=mediana, 70=conservador, 40=agresivo)
        beta: Factor de confianza en el compañero
        cache_file: Archivo para guardar resultado
        silent: bool, True para suprimir mensajes
    
    Returns:
        mu: float (umbral calibrado)
    """
    cache_path = Path(__file__).parent / cache_file
    
    # Intentar cargar desde caché
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
                key = f"mu_{percentil}_beta_{beta}_modo_{'8' if estadisticas.modo_8_reyes else '4'}"
                if key in cache:
                    return cache[key]
        except:
            pass
    
    # Calcular μ
    if not silent:
        print(f"\nCalibrando umbral μ (percentil {percentil})...")
    EVs = []
    
    for mano in estadisticas.df['mano_lista']:
        ev_total, _ = calcular_ev_total(mano, estadisticas, beta)
        EVs.append(ev_total)
    
    mu = np.percentile(EVs, percentil)
    
    # Guardar en caché
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except:
            pass
    
    key = f"mu_{percentil}_beta_{beta}_modo_{'8' if estadisticas.modo_8_reyes else '4'}"
    cache[key] = float(mu)
    
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)
    
    if not silent:
        print(f"✓ Umbral μ calibrado: {mu:.4f}")
    return mu


# ============================================================================
# POLÍTICA DE DECISIÓN ESTOCÁSTICA
# ============================================================================

def decidir_cortar(mano, estadisticas, mu, k_base=2.0, sigma=0.3, beta=0.7, posicion=1):
    """
    Decide si cortar o dar mus usando función sigmoide estocástica.
    
    Args:
        mano: Lista de 4 cartas
        estadisticas: EstadisticasEstaticas
        mu: Umbral calibrado (percentil)
        k_base: Agresividad base de la sigmoide
        sigma: Desviación estándar del ruido gaussiano
        beta: Factor de confianza en el compañero
        posicion: Posición en la mesa [1-4]
    
    Returns:
        decision: bool (True = Cortar, False = Mus)
        P_cortar: float (probabilidad usada)
        EV_total: float (valor esperado de la mano)
        desglose: dict (componentes detallados del EV)
    """
    # Calcular EV de la mano
    EV_total, desglose = calcular_ev_total(mano, estadisticas, beta, posicion)
    
    # Agresividad estocástica (ruido gaussiano)
    K = np.random.normal(k_base, sigma)
    K = max(K, 0.5)  # Evitar valores negativos o muy pequeños
    
    # Probabilidad de cortar (función sigmoide)
    exponente = -K * (EV_total - mu)
    # Limitar exponente para evitar overflow
    exponente = np.clip(exponente, -500, 500)
    P_cortar = 1 / (1 + np.exp(exponente))
    
    # Decisión estocástica
    decision = np.random.random() < P_cortar
    
    return decision, P_cortar, EV_total, desglose


# ============================================================================
# CLASE PRINCIPAL: MOTOR DE DECISIÓN
# ============================================================================

class MotorDecisionMus:
    """
    Motor de Decisión de Mus - Interfaz principal.
    Gestiona la carga de estadísticas, calibración y toma de decisiones.
    """
    
    def __init__(self, modo_8_reyes=False, perfil='normal', silent=False):
        """
        Inicializa el motor de decisión.
        
        Args:
            modo_8_reyes: bool, True para 8 reyes, False para 4 reyes
            perfil: 'conservador', 'normal', 'agresivo'
            silent: bool, True para suprimir mensajes de inicialización
        """
        if perfil not in PERFILES:
            raise ValueError(f"Perfil '{perfil}' no válido. Usa: {list(PERFILES.keys())}")
        
        self.modo_8_reyes = modo_8_reyes
        self.perfil = perfil
        self.params = PERFILES[perfil].copy()
        self.silent = silent
        
        # Cargar estadísticas
        if not silent:
            print(f"Cargando estadísticas ({4 if not modo_8_reyes else 8} reyes, perfil: {perfil})...")
        self.estadisticas = EstadisticasEstaticas(modo_8_reyes)
        
        # Calibrar umbral μ
        self.mu = calibrar_umbral_mu(
            self.estadisticas,
            percentil=self.params['percentil_mu'],
            beta=self.params['beta'],
            silent=silent
        )
        
        if not silent:
            print(f"✓ Motor de decisión listo\n")
    
    def decidir(self, mano, posicion=1):
        """
        Toma la decisión de cortar o dar mus para una mano.
        
        Args:
            mano: Lista de 4 cartas
            posicion: Posición en la mesa [1-4]
        
        Returns:
            decision: bool (True = Cortar, False = Mus)
            P_cortar: float (probabilidad de cortar)
            EV_total: float (valor esperado)
            desglose: dict (análisis detallado)
        """
        return decidir_cortar(
            mano,
            self.estadisticas,
            self.mu,
            k_base=self.params['k_base'],
            sigma=self.params['sigma'],
            beta=self.params['beta'],
            posicion=posicion
        )
    
    def analizar_mano_detallado(self, mano, posicion=1):
        """
        Analiza una mano sin tomar decisión (solo muestra EV y componentes).
        
        Args:
            mano: Lista de 4 cartas
            posicion: Posición en la mesa [1-4]
        
        Returns:
            dict con análisis completo
        """
        EV_total, desglose = calcular_ev_total(mano, self.estadisticas, self.params['beta'], posicion)
        
        # Calcular probabilidad de cortar sin ruido (K fijo)
        exponente = -self.params['k_base'] * (EV_total - self.mu)
        exponente = np.clip(exponente, -500, 500)
        P_cortar_base = 1 / (1 + np.exp(exponente))
        
        return {
            'EV_total': EV_total,
            'P_cortar_base': P_cortar_base,
            'mu': self.mu,
            'desglose': desglose,
            'caracteristicas': desglose['analisis_mano'],
            'probabilidades': desglose['probabilidades'],
            'valor_juego': calcular_valor_juego(mano)
        }


# ============================================================================
# UTILIDADES Y FORMATO
# ============================================================================

def formatear_decision(mano, decision, P_cortar, EV_total, desglose):
    """Formatea la decisión para presentación al usuario."""
    resultado = []
    resultado.append("=" * 70)
    resultado.append(" MOTOR DE DECISIÓN DE MUS")
    resultado.append("=" * 70)
    resultado.append(f"\nMano: {sorted(mano, reverse=True)}")
    resultado.append(f"\nDECISIÓN: {'🛑 CORTAR' if decision else '🔄 MUS'}")
    resultado.append(f"Probabilidad de cortar: {P_cortar:.1%}")
    resultado.append(f"Valor Esperado (EV): {EV_total:.4f}")
    resultado.append("\n" + "-" * 70)
    resultado.append(" ANÁLISIS DE LA MANO")
    resultado.append("-" * 70)
    
    analisis = desglose['analisis_mano']
    resultado.append(f"  Pares:  {analisis['tipo_pares']} (W={analisis['W_pares']:.1f})")
    resultado.append(f"  Juego:  {'Sí' if analisis['tiene_juego'] else 'No'} " +
                    f"(valor={analisis['valor_juego_raw']}, W={analisis['W_juego']:.1f})")
    
    resultado.append("\n" + "-" * 70)
    resultado.append(" PROBABILIDADES")
    resultado.append("-" * 70)
    prob = desglose['probabilidades']
    resultado.append(f"  Grande: {prob['prob_grande']:.2%}")
    resultado.append(f"  Chica:  {prob['prob_chica']:.2%}")
    resultado.append(f"  Pares:  {prob['prob_pares']:.2%}")
    resultado.append(f"  Juego:  {prob['prob_juego']:.2%}")
    
    resultado.append("\n" + "-" * 70)
    resultado.append(" DESGLOSE DE EV")
    resultado.append("-" * 70)
    for lance in ['grande', 'chica', 'pares', 'juego']:
        ev_lance = desglose[lance]
        resultado.append(f"  {lance.upper():7s}: Propio={ev_lance['propio']:.3f}, " +
                        f"Soporte={ev_lance['soporte']:.3f}, " +
                        f"Decisión={ev_lance['decision']:.3f}")
    
    resultado.append("\n" + "=" * 70)
    return "\n".join(resultado)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" EJEMPLO DE USO - MOTOR DE DECISIÓN")
    print("=" * 70)
    
    # Crear motor con perfil normal (usar 8 reyes ya que tenemos esos datos)
    motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
    
    # Ejemplos de manos (válidas a 8 reyes: sin 2 ni 3)
    ejemplos = [
        [12, 11, 10, 1],   # 31 (mejor juego)
        [12, 12, 5, 4],    # Duples Rey, sin juego
        [7, 7, 6, 6],      # Medias 7-6, sin juego
        [1, 1, 1, 1]       # Cuatro ases, juego 34
    ]
    
    for mano in ejemplos:
        print("\n")
        decision, P_cortar, EV_total, desglose = motor.decidir(mano)
        print(formatear_decision(mano, decision, P_cortar, EV_total, desglose))
        
        # Probar estocasticidad (misma mano, múltiples decisiones)
        print(f"\n  Estocasticidad (misma mano, 10 intentos):")
        decisiones = []
        for _ in range(10):
            dec, _, _, _ = motor.decidir(mano)
            decisiones.append("Cortar" if dec else "Mus")
        print(f"  Decisiones: {decisiones}")
