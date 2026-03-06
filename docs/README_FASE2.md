# FASE 2: Simulador de Descarte por Rollout (Puntos Reales)

## 📋 Descripción General

Sistema completo de Q-Learning para determinar políticas óptimas de descarte en el Mus, basado en simulaciones de rollout (partida completa) y medición de puntos reales obtenidos por cada equipo.

**Objetivo:** En lugar de usar estimaciones heurísticas (EV), este sistema simula el final de la ronda completa y mide el diferencial de puntos real (`Puntos_Equipo_A - Puntos_Equipo_B`) para cada decisión de descarte posible.

## 🏗️ Arquitectura del Sistema

### Módulos Implementados

```
calculadora_probabilidades_mus/
├── params.py                      # Configuración centralizada
├── evaluador_ronda.py             # Evaluación de 4 lances + puntuación
├── generar_politicas_rollout.py   # Q-Learning para políticas óptimas
└── simulador_fase2.py             # Simulador con políticas óptimas

utils/
├── mascaras_descarte.py           # Gestión de máscaras de descarte
└── descarte_heuristico.py         # Política baseline (jugador promedio)

Tests/
├── test_mascaras.py               # Tests de máscaras
├── test_evaluador_ronda.py        # Tests de evaluación de ronda
└── test_descarte_heuristico.py    # Tests de heurística
```

## 🎯 Sistema de Puntuación Real

### Reglas Implementadas

| Lance | Puntos | Detalle |
|-------|--------|---------|
| **Grande** | 1 punto | Fijo para el equipo ganador |
| **Chica** | 1 punto | Fijo para el equipo ganador |
| **Pares** | Variable | Suma de valores base de **AMBOS** miembros del equipo ganador |
| **Juego** | Variable | Suma de valores base de **AMBOS** miembros del equipo ganador |
| **Punto** | 1 punto | Cuando nadie tiene juego |

### Valores Base para Pares

```python
sin_pares = 0 puntos
pares     = 1 punto
medias    = 2 puntos
duples    = 3 puntos
```

### Valores Base para Juego

```python
31 (La 31) = 3 puntos
Otros juegos (32-40) = 2 puntos
```

### Ejemplo de Puntuación

**Manos:**
- J1 (Equipo A): Duples de Rey + Juego 31 → Pares: 3, Juego: 3
- J2 (Equipo B): Medias de 7 → Pares: 2, Juego: 0
- J3 (Equipo A): Par de Ases + Juego 31 → Pares: 1, Juego: 3
- J4 (Equipo B): Par de 5 → Pares: 1, Juego: 0

**Resultado:**
- **Grande:** Gana J1 (Equipo A) → +1 punto
- **Chica:** Gana J4 (Equipo B) → +1 punto
- **Pares:** Gana J1 (Duples > Medias) → Equipo A suma 3+1 = **+4 puntos**
- **Juego:** Gana J1 o J3 (ambos 31) → Equipo A suma 3+3 = **+6 puntos**

**Total:** Equipo A: 11 puntos | Equipo B: 1 punto | **Diferencial: +10**

## 🎴 Máscaras de Descarte

### Concepto

Una máscara especifica qué cartas descartar de una mano de 4 cartas. Se representa como tupla de índices.

**Total de máscaras:** 15 (descartar 1, 2, 3 o 4 cartas)

```python
# Ejemplos para mano [12, 12, 11, 10]:
(0,)         # Descartar posición 0 (primer 12)
(0, 1)       # Descartar posiciones 0,1 (ambos 12)
(2, 3)       # Descartar posiciones 2,3 (11 y 10)
(0, 1, 2, 3) # Descartar todas
```

### Distribución

| Cartas descartadas | Cantidad de máscaras |
|-------------------|---------------------|
| 1 carta | 4 |
| 2 cartas | 6 |
| 3 cartas | 4 |
| 4 cartas | 1 |
| **TOTAL** | **15** |

## 🤖 Política Base (Heurística)

Para simular rivales realistas, se implementó una política heurística con reglas conservadoras:

### Reglas de la Heurística

1. **Reyes (12):** Mantener SIEMPRE
2. **Pareja de Ases:** Mantener SOLO en posición 4 (Postre)
3. **As suelto:** Mantener SOLO si hay Rey (buscar 31)
4. **Figuras altas (10, 11):** Mantener SOLO si hay Rey
5. **Basura (4-7):** Descartar SIEMPRE
6. **Figuras sin soporte:** Descartar

### Ejemplos

```python
Mano: [12, 11, 7, 4] (Pos 1)
→ Mantiene: [12, 11]  # Rey + Caballo
→ Descarta: [7, 4]    # Basura

Mano: [1, 1, 5, 6] (Pos 4)
→ Mantiene: [1, 1]    # Pareja de Ases en Postre
→ Descarta: [5, 6]

Mano: [1, 1, 5, 6] (Pos 1)
→ Mantiene: []        # Pareja de Ases NO en Postre sin Rey
→ Descarta: [1, 1, 5, 6]
```

## 🎲 Generador de Políticas (Q-Learning)

### Proceso de Aprendizaje

```
Por cada iteración:
  1. Repartir 4 manos iniciales
  2. Evaluar Fase 1 (¿Todos dan Mus?)
     └─ Si alguien corta → siguiente iteración
  3. Guardar mazo_restante (24 cartas)
  4. Para el Jugador 1:
     a. Iterar sobre las 15 máscaras
     b. Para cada máscara:
        - J1 descarta según máscara y roba
        - J2, J3, J4 descartan con heurística y roban
        - Evaluar ronda completa (4 lances)
        - Calcular Diferencial = Puntos_A - Puntos_B
        - Actualizar Q(mano_J1, pos_J1, máscara) += Diferencial
  5. Siguiente iteración
```

### Q-Table

Estructura: `Q(mano, posicion, mascara) = reward_promedio`

**Formato CSV:**
```csv
mano,posicion,mascara_idx,reward_promedio,n_visitas
"[12, 12, 11, 10]",1,0,2.45,1523
"[12, 12, 11, 10]",1,1,-0.87,1523
...
```

### Ejecución

```bash
cd calculadora_probabilidades_mus
python generar_politicas_rollout.py
```

**Configuración:**
- Iteraciones: 100,000 (configurable en `params.py`)
- Modo: 8 Reyes (configurable)
- Output: `politicas_optimas_fase2.csv`

**Tiempo estimado:** 10-30 minutos (según hardware)

## 📊 Simulador de Fase 2

### Proceso de Simulación

```
Por cada iteración:
  1. Repartir 4 manos iniciales
  2. Evaluar Fase 1 (¿Todos dan Mus?)
     └─ Si alguien corta → siguiente iteración
  3. Para cada jugador (1-4):
     a. Consultar política óptima de su mano
     b. Elegir máscara con Softmax(tau=0.5) sobre rewards
        └─ Introduce variabilidad (jugadores no perfectos)
     c. Descartar y robar en orden (1→2→3→4)
  4. Evaluar ronda completa con 4 manos finales
  5. Registrar victorias por lance para cada mano_final
  6. Siguiente iteración
```

### Softmax Estocástico

Para simular jugadores realistas (no perfectos), se usa softmax sobre los rewards:

```python
P(máscara_i) ∝ exp(reward_i / tau)
```

- **tau = 0.5:** Balance entre explotación (elegir mejor) y exploración (probar subóptimas)
- **tau → 0:** Siempre elige la mejor (determinista)
- **tau → ∞:** Elige al azar (completamente exploratorio)

### Ejecución

```bash
cd calculadora_probabilidades_mus
python simulador_fase2.py
```

**Configuración:**
- Iteraciones: 500,000 (configurable en `params.py`)
- Entrada: `politicas_optimas_fase2.csv`
- Output: `probabilidades_fase2.csv`

**Tiempo estimado:** 20-60 minutos (según hardware)

## 🧪 Tests de Validación

### Test de Máscaras

```bash
python test_mascaras.py
```

**Verifica:**
- ✓ Se generan exactamente 15 máscaras
- ✓ Distribución correcta (4+6+4+1)
- ✓ Aplicación de máscaras funciona
- ✓ Robar cartas reduce baraja correctamente
- ✓ Completar mano funciona
- ✓ Conversión máscara ↔ índice

### Test de Evaluador de Ronda

```bash
python test_evaluador_ronda.py
```

**Verifica:**
- ✓ Grande: Gana la mano más alta
- ✓ Chica: Gana la mano más baja
- ✓ Pares: Jerarquía correcta (Duples > Medias > Pares)
- ✓ Juego/Punto: Lógica correcta
- ✓ Puntuación por equipo: Suma de ambos miembros
- ✓ Desempates por posición (1 > 2 > 3 > 4)

### Test de Heurística de Descarte

```bash
python test_descarte_heuristico.py
```

**Verifica:**
- ✓ Reyes siempre se mantienen
- ✓ Pareja de Ases: Regla posicional (solo pos. 4)
- ✓ As suelto: Solo con Rey
- ✓ Figuras altas: Solo con Rey
- ✓ Basura siempre se descarta
- ✓ Conversión a índice de máscara

## ⚙️ Configuración (params.py)

### Parámetros Principales

```python
# Simulación
TAU = 0.5                           # Temperatura Softmax
N_ITERACIONES_ROLLOUT = 100_000     # Generador de políticas
N_ITERACIONES_SIMULADOR_FASE2 = 500_000  # Simulador

# Puntuación
VALORES_PUNTOS_PARES = {
    "sin_pares": 0,
    "pares": 1,
    "medias": 2,
    "duples": 3
}

VALORES_PUNTOS_JUEGO = {
    31: 3,  # La 31
    32: 2, 33: 2, 34: 2, 35: 2,
    36: 2, 37: 2, 40: 2
}

PUNTOS_GRANDE = 1
PUNTOS_CHICA = 1
PUNTOS_PUNTO = 1

# Equipos
EQUIPOS = {1: "A", 2: "B", 3: "A", 4: "B"}

# Archivos
ARCHIVO_POLITICAS_FASE2 = "politicas_optimas_fase2.csv"
ARCHIVO_PROBABILIDADES_FASE2 = "probabilidades_fase2.csv"

# Modo
MODO_8_REYES = True
```

## 📈 Análisis de Resultados

### Comparación Fase 1 vs Fase 2

**Fase 1 (Sin descarte):**
- Archivo: `resultados_8reyes.csv`
- Probabilidades con manos iniciales
- No considera descarte óptimo

**Fase 2 (Con descarte óptimo):**
- Archivo: `probabilidades_fase2.csv`
- Probabilidades con manos finales tras descarte
- Refleja estrategia óptima de descarte

**Análisis esperado:**
- ↗️ Aumento en `prob_pares` (mejora de manos)
- ↗️ Aumento en `prob_juego` (búsqueda de 31)
- Manos débiles mejoran más que manos fuertes

### Ejemplo de Análisis

```python
import pandas as pd

fase1 = pd.read_csv("resultados_8reyes.csv")
fase2 = pd.read_csv("probabilidades_fase2.csv")

# Merge por mano
comparacion = fase1.merge(fase2, on="mano", suffixes=("_fase1", "_fase2"))

# Calcular mejoras
comparacion["mejora_pares"] = comparacion["prob_pares_fase2"] - comparacion["prob_pares_fase1"]
comparacion["mejora_juego"] = comparacion["prob_juego_fase2"] - comparacion["prob_juego_fase1"]

# Top 10 mejoras
print(comparacion.nlargest(10, "mejora_pares")[["mano", "mejora_pares", "mejora_juego"]])
```

## 🚀 Flujo de Trabajo Completo

### 1. Generación de Políticas Óptimas

```bash
cd calculadora_probabilidades_mus
python generar_politicas_rollout.py
```

**Output:** `politicas_optimas_fase2.csv` (~10-15MB)

### 2. Simulación con Políticas

```bash
python simulador_fase2.py
```

**Output:** `probabilidades_fase2.csv`

### 3. Análisis de Resultados

```bash
# Comparar con Fase 1
python -c "
import pandas as pd
fase1 = pd.read_csv('resultados_8reyes.csv')
fase2 = pd.read_csv('probabilidades_fase2.csv')
print('Fase 1 - Manos:', len(fase1))
print('Fase 2 - Manos:', len(fase2))
print('\\nPromedio prob_pares:')
print('  Fase 1:', fase1['probabilidad_pares'].mean())
print('  Fase 2:', fase2['prob_pares'].mean())
"
```

## 🔧 Extensiones Futuras

### Posibles Mejoras

1. **Multi-posición:** Actualmente solo aprende J1. Extender a las 4 posiciones.
2. **Información del compañero:** Integrar conocimiento de la mano del compañero (señas).
3. **Modelo de oponentes:** Asumir que rivales también optimizan.
4. **Deep Q-Learning:** Usar redes neuronales en lugar de Q-Table.
5. **Envites:** Incorporar sistema de apuestas (paso/quiero/órdago).
6. **Partida completa:** Simular hasta 40 puntos, no solo una ronda.

### Arquitectura para Multi-Posición

```python
# Modificar generar_politicas_rollout.py
for posicion_sujeto in [1, 2, 3, 4]:  # Extender a todas las posiciones
    mano_sujeto = manos_iniciales[posicion_sujeto]
    
    for mascara_idx in range(15):
        # Simular rollout desde la perspectiva de posicion_sujeto
        reward = simular_rollout_mascara(
            mano_sujeto, posicion_sujeto, mascara_idx, ...
        )
        q_table.actualizar(mano_sujeto, posicion_sujeto, mascara_idx, reward)
```

## 📚 Referencias

### Documentación Relacionada

- **FUNDAMENTOS_MATEMATICOS.md:** Matemáticas de Fase 1
- **DESEMPATES_MATEMATICOS.md:** Sistema de desempates
- **TABLA_MAESTRA_EV.md:** Expected Values (Fase 1)
- **CHANGELOG_v2.3.md:** Evolución del proyecto

### Papers y Recursos

- **Monte Carlo Tree Search (MCTS):** Técnica de búsqueda usada en Go/Chess
- **Q-Learning:** Sutton & Barto, "Reinforcement Learning: An Introduction"
- **Rollout Algorithms:** Bertsekas, "Dynamic Programming and Optimal Control"

## 👥 Equipos y Posiciones

```
┌─────────────────────────────────┐
│          MESA DE MUS            │
│                                 │
│         Posición 1              │
│           (Mano)                │
│         Equipo A                │
│                                 │
│  Pos 4        +        Pos 2    │
│ (Postre)               Equipo B │
│ Equipo B                        │
│                                 │
│         Posición 3              │
│         Equipo A                │
│                                 │
└─────────────────────────────────┘

Parejas:
- Equipo A: Posiciones 1 y 3
- Equipo B: Posiciones 2 y 4

Desempates: 1 > 2 > 3 > 4
```

## ✅ Validación del Sistema

### Checklist de Verificación

- [x] Máscaras de descarte generadas correctamente (15 máscaras)
- [x] Heurística base funcional (reglas posicionales)
- [x] Evaluador de ronda calcula puntos correctamente
- [x] Sistema de puntuación por equipo implementado
- [x] Q-Learning con rollouts funcional
- [x] Softmax estocástico para variabilidad
- [x] Simulador Fase 2 con políticas óptimas
- [x] Tests de validación (100% pasados)
- [x] Documentación completa

### Tests Ejecutados

```bash
✓ test_mascaras.py: 6/6 tests pasados
✓ test_evaluador_ronda.py: 6/6 tests pasados
✓ test_descarte_heuristico.py: 7/7 tests pasados

Total: 19/19 tests pasados (100%)
```

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **CSV vs JSON para Q-Table:** CSV elegido por facilidad de análisis con pandas
2. **Softmax en simulador:** Añade realismo (jugadores no perfectos)
3. **Heurística conservadora:** Baseline sólido para aprendizaje
4. **Solo J1 en Q-Learning:** Simplifica primera versión, extensible a 4 posiciones
5. **Desempates estrictos:** Posición 1 > 2 > 3 > 4 (sin probabilidades)

### Limitaciones Conocidas

- **Solo aprende J1:** Las políticas se generan solo para posición 1
- **Sin información del compañero:** No considera señas ni información parcial
- **Oponentes con heurística fija:** No se adaptan ni optimizan
- **Sin envites:** Sistema simplificado sin apuestas
- **Una ronda aislada:** No considera contexto de partida completa

## 🎛️ Sistema de Mus Configurable (v2.4)

### Tasa de Mus Objetivo

La tasa de mus (porcentaje de repartos donde los 4 jugadores dan mus) es configurable:

```python
# En params.py
TASA_MUS_OBJETIVO = 0.20  # 20% objetivo (modificable)
```

Para alcanzarla automáticamente, usar auto-calibración al crear el motor:

```python
motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal', auto_calibrar_tasa=True)
```

Esto ejecuta búsqueda binaria sobre `percentil_mu` hasta encontrar el valor que produce la tasa objetivo.

### Parámetros Position-Aware (FACTOR_K_POS)

Las posiciones 1 y 3 (equipo Mano) dan mus con más frecuencia porque se benefician de los descartes sucesivos. Esto se modela con un factor multiplicativo sobre k:

```python
# En params.py
FACTOR_K_POS = {
    1: 0.75,  # Mano: 25% más agresivo pidiendo mus
    2: 1.0,   # Normal
    3: 0.75,  # Pareja de Mano: 25% más agresivo pidiendo mus
    4: 1.0    # Postre: normal
}
```

- Factor < 1.0 → k más bajo → sigmoide más plana → más probabilidad de dar mus
- Factor = 1.0 → sin ajuste

### Temperatura Adaptativa (Softmax)

En lugar de un TAU fijo para el softmax de selección de máscaras, se adapta según la claridad de la decisión:

```python
# En params.py
TAU_ADAPTATIVO = True      # Activar/desactivar
TAU_MIN = 0.4              # Explotar cuando hay clara ventaja  
TAU_MAX = 1.5              # Explorar cuando opciones similares
UMBRAL_DIFERENCIA_ALTO = 0.5   # Diferencia de reward para TAU mínimo
UMBRAL_DIFERENCIA_BAJO = 0.05  # Diferencia de reward para TAU máximo
```

**Criterio:** Diferencia entre el mejor y el segundo mejor reward:
- Diferencia ≥ 0.5 → TAU = 0.4 (explotar, decisión clara)
- Diferencia ≤ 0.05 → TAU = 1.5 (explorar, opciones similares)
- Entre ambos → interpolación lineal

### Script de Diagnóstico

```bash
# Diagnóstico básico (50K iteraciones)
python diagnostico_mus.py --iteraciones 50000

# Con auto-calibración
python diagnostico_mus.py --iteraciones 50000 --calibrar

# Con perfil específico
python diagnostico_mus.py --perfil agresivo --iteraciones 100000
```

Reporta: tasa de mus global y por posición, distribución de K efectivo, validación position-aware.

### Perfiles Actualizados

| Perfil | k_base | sigma | percentil_mu | beta | Tasa Mus aprox. |
|--------|--------|-------|-------------|------|-----------------|
| conservador | 1.2 | 0.3 | 80 | 0.65 | ~15% |
| normal | 1.0 | 0.4 | 74 | 0.75 | ~20% |
| agresivo | 0.8 | 0.5 | 65 | 0.85 | ~30% |

---

**Autor:** Sistema de Fase 2 - Rollout con Puntos Reales  
**Fecha:** Febrero 2026  
**Versión:** 2.4.0  
**Estado:** ✅ Implementación Completa y Validada
