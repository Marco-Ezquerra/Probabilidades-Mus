# Módulo de Decisión de Corte — Estado Actual y Trabajo Futuro

> **Versión actual**: 2.6 (marzo 2026)  
> **Ficheros relevantes**: `calculadora_probabilidades_mus/motor_decision.py` · `calculadora_probabilidades_mus/params.py`

---

## 1. Qué hace este módulo

Cuando un jugador recibe su mano en el Mus debe decidir: **cortar** (quedarse con esas cartas) o **dar mus** (pedir descarte). Esta decisión, repetida cuatro veces en cada mano, determina si hay reparto o no.

El módulo implementa esa decisión mediante una **función sigmoide estocástica** sobre el Valor Esperado de la mano:

$$
P(\text{cortar}) = \sigma\!\left(K_{\text{pos}} \cdot \bigl(EV_{\text{efectivo}} - \mu\bigr)\right)
$$

Donde:

| Símbolo | Significado |
|---------|-------------|
| $K_{\text{pos}} = k_{\text{base}} \times \texttt{FACTOR\_K\_POS}[\text{pos}]$ | Pendiente de la sigmoide, ajustada por posición |
| $EV_{\text{efectivo}} = EV_{\text{total}} + \texttt{EV\_CORTE\_BONUS}[\text{pos}]$ | EV real de la mano más el valor implícito de quitar mano |
| $\mu$ | Umbral calibrado como percentil de la distribución de EVs |
| $k_{\text{base}}$ | Agresividad base del perfil elegido por el usuario |

La decisión final es **estocástica**: se añade ruido gaussiano sobre $K$ con desviación `sigma`, lo que genera variabilidad natural entre partidas.

---

## 2. Parámetros actuales calibrados

### 2.1 Perfiles de agresividad

Calibrados empíricamente para que el perfil **normal** logre una tasa de mus del 20%:

| Perfil | `percentil_mu` | `k_base` | `sigma` | `beta` | P(cortar) pos1 | tasa mus |
|--------|---------------|----------|---------|--------|----------------|----------|
| conservador | 84 | 1.4 | 0.30 | 0.65 | ~26% | ~30% |
| **normal** | **77** | **1.2** | **0.35** | **0.75** | **~33%** | **~20%** |
| agresivo | 60 | 1.0 | 0.40 | 0.85 | ~49% | ~7% |

### 2.2 Factor de posición sobre k

Las posiciones del equipo **Mano** (1 y 3) se benefician del orden de descarte y en la práctica piden más mus:

```python
FACTOR_K_POS = {1: 0.75, 2: 1.0, 3: 0.75, 4: 1.0}
```

### 2.3 Bonus de corte por posición

**Postre** (pos 4) y su pareja (pos 2) pierden todos o la mitad de los desempates. Cortar les quita la mano a los rivales, lo que vale 2-3 puntos reales en partidas con apuestas. Este valor *no está capturado* por el EV de la mano propia, por lo que se añade como bonus antes de la sigmoide:

```python
EV_CORTE_BONUS = {1: 0.0, 2: 0.15, 3: 0.0, 4: 0.30}
```

Calibrado por búsqueda exhaustiva (sweeping $b_4 \in [0, 1.5]$ con ratio 2:1) para mantener tasa de mus del 20%:

| Pos | bonus | P(cortar) | P(mus) |
|-----|-------|-----------|--------|
| 1 (Mano)       | 0.00 | 33.3% | 66.7% |
| 2 (Int. izda.) | 0.15 | 31.9% | 68.1% |
| 3 (Int. dcha.) | 0.00 | 32.6% | 67.4% |
| 4 (Postre)     | 0.30 | 33.8% | 66.2% |
| **Tasa de mus global** | | | **20.25%** |

---

## 3. Limitaciones conocidas

### 3.1 Calibración a ciegas

Todos los parámetros actuales (`percentil_mu`, `k_base`, `sigma`, `beta`, `EV_CORTE_BONUS`) han sido elegidos de forma **computacional**, sin validación contra datos reales de partidas de Mus. La tasa de mus del 20% es un objetivo razonable pero no está respaldado por estadísticas de juego real.

### 3.2 El bonus de postre es una aproximación gruesa

El valor de «quitar mano» depende de:
- El nivel de apuestas en juego en ese momento.
- Si hay órdago previo o piedras declaradas.
- El historial de señas entre los compañeros de equipo.

Con la implementación actual el bonus es **constante e igual para todas las manos**, lo cual es claramente incorrecto: no vale lo mismo quitar mano con cuatro reyes que con una mano sin pares.

### 3.3 La decisión ignora información táctica

La sigmoide solo usa el EV propio ajustado. No tiene en cuenta:
- Las señas del compañero.
- El número de cartas que ya han descartado los rivales en rondas previas.
- El marcador (si se va ganando o perdiendo).
- La fase de la ronda (primera o segunda vuelta de mus en el mismo reparto).

### 3.4 Beta fijo

El parámetro `beta` modela la confianza en el compañero con un escalar fijo. En la realidad esta confianza depende de las señas jugadas y debería actualizarse dinamicámente a lo largo de la mano.

---

## 4. Trabajo futuro

### 4.1 ← Módulo «Mus Avanzado»: calibración con maestros

Esta es la extensión más importante y la que mayor impacto tendría sobre la calidad de las decisiones. Requiere dos tipos de aportación:

**A) Datos de partidas reales**

- Registrar decisiones de corte/mus de jugadores expertos (mínimo 2.000-5.000 manos documentadas).
- Variables a registrar: mano, posición, decisión, contexto de apuestas, señas del compañero, resultado del lance.
- Con esos datos es posible ajustar `percentil_mu` y `k_base` mediante **máxima verosimilitud** o regresión logística, en lugar de la búsqueda basada en tasa de mus.

**B) Juicio experto sobre casos particulares**

Existen situaciones donde la decisión óptima se desvía sistemáticamente del comportamiento medio. Los maestros del Mus son capaces de articular estas reglas, que deberían convertirse en ajustes explícitos del modelo. Ejemplos:

| Situación | Sesgo esperado | Variables de entrada necesarias |
|-----------|---------------|--------------------------------|
| Mano sin pares y sin juego en posición postre | Cortar casi siempre | tipo_pares, tiene_juego, posicion |
| Cuatro cartas altas (R-R-R-R) en posición mano | Cortar siempre | valor_grande, posicion |
| Compañero ha señado juego | Dar mus si no tienes juego (para no «romper») | senas_companero |
| Marcador muy favorable, última mano | Cortar más de lo normal (evitar riesgos) | marcador, ronda |
| Pareja que va perdiendo y necesita la mano | Dar mus más de lo normal | marcador, ronda |

**C) Arquitectura propuesta para el módulo avanzado**

```
MotorDecisionAvanzado
├── DecisionCorte (actual)         ← base, sirve de prior
│   └── calibrado con datos reales via MLE
├── SeñasCompañero                 ← nuevo
│   └── actualiza beta dinámicamente
├── ContextoPartida                ← nuevo
│   ├── nivel_apuestas
│   ├── marcador
│   └── fase_ronda
└── AjustesEspecialistas           ← nuevo
    └── reglas explícitas validadas por maestros
```

### 4.2 Bonus de corte dependiente del contexto de apuestas

El `EV_CORTE_BONUS` actual es una constante (0.30 para postre). Debería ser función del nivel de apuestas:

$$
\text{bonus}(\text{pos}, \text{apuestas}) = \texttt{EV\_CORTE\_BONUS}[\text{pos}] \times f(\text{apuestas})
$$

Donde $f$ crece con el nivel de envite medio en la mano. Una primera aproximación lineal podría ajustarse con datos reales.

### 4.3 Sigma adaptativa

El ruido gaussiano `sigma` es actualmente fijo por perfil. Una mejora natural es que crezca con la incertidumbre de la mano (manos con EV cercano a `mu` merecen más variabilidad) y se reduzca cuando la decisión es obvia.

### 4.4 Validación cruzada

Una vez disponibles datos de expertos, validar mediante:
- **Accuracy de decisión**: ¿en qué % de casos el motor coincide con el maestro?
- **EV medio de la decisión**: ¿las partidas simuladas con parámetros calibrados producen más puntos que con los actuales?
- **Tasa de mus observada vs. objetivo**: contrastar el 20% teórico con datos reales.

---

## 5. Correcciones de desempate por posición (v2.6)

En v2.6 se corrigió un sesgo sistemático en el cálculo de probabilidades: el CSV base (`resultados_8reyes.csv`) fue generado con `es_mano=True` para todas las manos, lo que equivale a asumir que la posición 1 gana todos los desempates. Para posiciones 2, 3 y 4 esto sobreestima la probabilidad de victoria.

### 5.1 Factor de desempate

```python
factor_des = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}[posicion]
```

- **Posición 1 (Mano)**: gana todos los empates → `factor_des = 1.0`
- **Posiciones 2 y 3**: ganan/pierden la mitad → `factor_des = 0.5`
- **Posición 4 (Postre)**: pierde todos los empates → `factor_des = 0.0`

### 5.2 Grande y Chica

La corrección se aplica analíticamente antes del cálculo del EV:

$$P_{\text{adj}} = \max\!\bigl(0,\; P_{\text{CSV}} - 2 \cdot P_{\text{empate}} \cdot (1 - f_{\text{des}})\bigr)$$

Donde $P_{\text{empate}}$ es la probabilidad de empate exacto calculada combinatoriamente sobre las 36 cartas restantes (método `_calcular_probs_empate_gc`). El factor $2$ tiene en cuenta que hay dos rivales.

### 5.3 Pares

```python
P(\text{victoria pares}) = (1 - P_{\text{RL}}) + P_{\text{RL}} \cdot (p_{\text{menor}} + p_{\text{empate}} \cdot f_{\text{des}})
```

Donde $P_{\text{RL}}$ es la probabilidad de que el rival tenga pares (del CSV), y $p_{\text{menor}}$, $p_{\text{empate}}$ se obtienen de la distribución exacta sobre el ranking de pares (par < medias < duples).

### 5.4 Juego y Punto

**Con juego:**

$$P(\text{victoria juego}) = (1 - P_{\text{RL}}) + P_{\text{RL}} \cdot (p_{\text{menor\_j}} + p_{\text{empate\_j}} \cdot f_{\text{des}})$$

**Sin juego (punto):**

$$P(\text{victoria punto}) = (1 - P_{\text{RL}}) \cdot (p_{\text{menor\_p}} + p_{\text{empate\_p}} \cdot f_{\text{des}})$$

> Nota: si el jugador no tiene juego solo puede ganar el lance de Punto cuando *ningún* rival tiene juego (factor $1 - P_{\text{RL}}$) y dentro de ese escenario gana si su punto es superior o si hay empate y tiene ventaja de posición.

---

## 5. Cómo contribuir

Si eres jugador/maestro de Mus con experiencia y quieres colaborar en la calibración, el proceso sería:

1. Instalar el proyecto (ver `GUIA_EJECUCION.md`).
2. Ejecutar `demos/app.py` con tu mano real y registrar si tu decisión coincide con la del motor.
3. Anotar los casos donde el motor se equivoca y el contexto (apuestas, señas, marcador).
4. Compartir esas anotaciones como issues en el repositorio de GitHub.

Incluso 100-200 casos bien anotados mejorarían sustancialmente el módulo.

---

## 6. Referencias internas

- [FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md) — Derivación completa del EV y la sigmoide.
- [DESEMPATES_MATEMATICOS.md](DESEMPATES_MATEMATICOS.md) — Probabilidades exactas de desempate por posición.
- [TAREA_PENDIENTE_SESGO_POLITICAS.md](TAREA_PENDIENTE_SESGO_POLITICAS.md) — Sesgo residual en el lance de Juego.
- `params.py` — Todos los parámetros en un único lugar, bien documentados.
- `motor_decision.py` — Implementación completa con `decidir_cortar()` y `MotorDecisionMus`.
