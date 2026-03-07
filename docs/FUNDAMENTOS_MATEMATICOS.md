# Fundamentos Matemáticos del Motor de Decisión Mus

> **Versión**: 2.5 (marzo de 2026)  
> **Enfoque**: Probabilidades condicionadas exactas mediante distribución hipergeométrica  
> **Fase 1 COMPLETA**: Grande, Chica, Pares, Juego y **Punto**

---

## 📐 Índice

1. [Valor Esperado Total](#1-valor-esperado-total)
2. [Lances Lineales (Grande y Chica)](#2-lances-lineales-grande-y-chica)
3. [Lances Condicionados (Pares, Juego y Punto)](#3-lances-condicionados-pares-juego-y-punto)
4. [Probabilidades de Desempate](#4-probabilidades-de-desempate)
5. [Probabilidades Condicionadas Exactas](#5-probabilidades-condicionadas-exactas)
6. [Política de Decisión Estocástica](#6-política-de-decisión-estocástica)

---

## 1. Valor Esperado Total

El valor esperado de una mano combina el valor propio con el soporte del compañero:

$$
\text{EV}_{\text{Total}} = \text{EV}_{\text{Propio}} + \beta \cdot \text{EV}_{\text{Soporte}}
$$

**Donde:**
- $\text{EV}_{\text{Propio}}$: Valor esperado de la mano propia
- $\text{EV}_{\text{Soporte}}$: Valor esperado del soporte del compañero
- $\beta \in [0, 1]$: Factor de confianza en el compañero
  - $\beta = 0.65$ (conservador)
  - $\beta = 0.75$ (normal)
  - $\beta = 0.85$ (agresivo)

**Descomposición por lances:**

$$
\text{EV}_{\text{Total}} = \sum_{L \in \{\text{Grande, Chica, Pares, Juego, Punto}\}} \left( \text{EV}_{\text{Propio}}^L + \beta \cdot \text{EV}_{\text{Soporte}}^L \right)
$$

**Nota sobre Juego vs Punto:**
- Si yo tengo juego (31-40) → se usa $\text{EV}_{\text{Juego}}$ (con jerarquía)
- Si yo NO tengo juego → se usa $\text{EV}_{\text{Punto}}$ (solo si ningún rival tiene juego)
- Son **mutuamente excluyentes**: solo uno contribuye al EV total

---

## 2. Lances Lineales (Grande y Chica)

Los lances lineales tienen un valor fijo de 1 punto. El EV depende únicamente de la probabilidad de ganar:

### EV Propio (Lineal)

$$
\text{EV}_{\text{Propio}}^{\text{Lineal}} = P(\text{yo gano}) \cdot 1.0
$$

**Donde:**
- $P(\text{yo gano})$: Probabilidad precalculada desde dataset Monte Carlo


## 3. Lances Condicionados (Pares, Juego y Punto)

Los lances condicionados requieren considerar dos escenarios:
1. **Rival NO tiene la jugada** → Gano automáticamente
2. **Rival SÍ tiene la jugada** → Debo comparar y ganar el desempate

### 3.1 Pares y Juego

#### EV Propio (Condicionado)

$$
\text{EV}_{\text{Propio}}^{\text{Cond}} = (1 - P_{RL}) \cdot W + P_{RL} \cdot P(\text{yo}|RL) \cdot (W + E_{\text{extra}})
$$

**Donde:**
- $P_{RL}$: Probabilidad de que al menos 1 rival tenga la jugada
- $P(\text{yo}|RL)$: Probabilidad de ganar contra rival con jugada (ver sección 4)
- $W$: Valor base de la jugada (puntos garantizados)
  - **Pares**: sin_pares: 0, pares: 1, medias: 2, duples: 3
  - **Juego** (jerarquía: 31 > 32 > 40 > 37 > 36 > 35 > 34 > 33):
    - 31: 3.0 (La 31 - mejor juego)
    - Resto de juegos (32, 40, 37, 36, 35, 34, 33): 2.0
    - **Nota (v2.4):** Sistema binario simplificado. En el Mus real, la 31 vale 3 puntos base y el resto de juegos valen 2 puntos base uniformemente. Las jerarquías se resuelven por comparación directa en caso de empate.
    - **Regla de cálculo (v2.5):** As(1) = **1 punto**, Sota/Caballo/Rey(10/11/12) = **10 puntos**, resto = valor nominal. La comparación entre juegos usa el **rango jeárquico** (31=rango 8, 32=7, 40=6…), no el valor numérico bruto.
- $E_{\text{extra}}$: Ganancia esperada por envites (swing)
  - **Actualmente: 0** (sistema de envites por implementar)
  - Pares: 0
  - Juego: 0

### 3.2 Punto (cuando nadie tiene juego)

**Regla:** El lance de Punto **solo se juega** si ninguno de los 4 jugadores tiene juego (31-40).

**Cálculo:**
- Suma de las cartas (máximo 10 por carta)
- Gana el más cercano a 30
- **W_punto = 1.0** (independiente del valor del punto)

#### EV Punto (cuando yo NO tengo juego)

$$
\text{EV}_{\text{Punto}} = (1 - P_{RL}^{\text{juego}}) \cdot P(\text{yo gano punto}) \cdot W_{\text{punto}}
$$

**Donde:**
- $P_{RL}^{\text{juego}}$: Probabilidad de que algún rival tenga juego
  - Si algún rival tiene juego → pierdo automático (no se juega punto)
- $P(\text{yo gano punto})$: Probabilidad de ganar en comparación de puntos
  - Precomputada en `prob_juego` del dataset (incluye victorias por punto)
- $W_{\text{punto}} = 1.0$: Todos los puntos valen 1 punto base

**Interpretación:**
- $(1 - P_{RL}^{\text{juego}})$: Probabilidad de que **ningún jugador** tenga juego
- Solo en ese caso se compara por punto

**Ejemplo:**
```
Mano: [1,1,12,12] (duples sin juego, punto 22)
- EV_pares: ~3.0 puntos (duples)
- EV_punto: ~2.0 puntos (si ningún rival tiene juego)
- EV_total: ~6.1 puntos
```

**Nota importante sobre EV Soporte Condicionado (ELIMINADO en v2.4):**
En versiones anteriores se incluía un término de "EV Soporte Condicionado" que modelaba el aporte del compañero en lances de Pares y Juego usando un factor de reducción:
- `f_red × P(comp_gana) × (W_comp + E_extra)`

Este término fue **eliminado** porque se aplica simétricamente tanto al compañero como a los rivales del equipo contrario, cancelándose mutuamente en el cálculo diferencial. No aporta información útil para la decisión de cortar o dar Mus.

**Descomposición:**

*Escenario 1 (rival sin jugada):*
$$
\text{Contribución}_1 = (1 - P_{RL}) \cdot W
$$

*Escenario 2 (rival con jugada):*
$$
\text{Contribución}_2 = P_{RL} \cdot P(\text{yo}|RL) \cdot (W + E_{\text{extra}})
$$

### Cálculo de $P_{RL}$ (Probabilidad Rival)

La probabilidad de que al menos un rival tenga la jugada es **PRECOMPUTADA** usando distribución hipergeométrica exacta:

$$
P_{RL}(\text{lance}|\text{mano}_{\text{yo}}) = \text{precomputado desde simulación Monte Carlo}
$$

**Proceso de precomputación (ver sección 5):**
1. Genero mi mano de 4 cartas
2. Quedan 36 cartas disponibles en el mazo (40 - 4)
3. Simulo 10,000 repartos de 2 rivales con 4 cartas cada uno
4. Cuento en cuántos casos AL MENOS 1 rival tiene la jugada
5. $P_{RL} = \frac{\text{casos con rival}}{\text{total simulaciones}}$

**Ventajas sobre aproximaciones lineales:**
- ✅ Considera la composición exacta de mi mano
- ✅ Respeta la distribución hipergeométrica real
- ✅ No asume independencia entre cartas
- ✅ No requiere pesos arbitrarios ni factores lineales

**Fallback si mano no está en dataset:**

$$
P_{RL} = 1 - (1 - p_{\text{individual}})^2^{\text{base
$$

Donde $p_{\text{individual}}$ es la probabilidad general base de tener la jugada.

### EV Soporte (Condicionado)

$$
\text{EV}_{\text{Soporte}}^{\text{Cond}} = f_{\text{red}} \cdot P(\text{comp} \text{ gana}) \cdot (W_{\text{comp}} + E_{\text{extra}})
$$

**Donde:**
- $f_{\text{red}}$: Factor de reducción (si yo tengo la jugada, compañero menos valioso)
  - Si yo tengo jugada: $f_{\text{red}} = 0.5$
  - Si yo NO tengo jugada: $f_{\text{red}} = 1.0$
- $P(\text{comp} \text{ gana}) = p_{\text{comp}} \cdot f_{\text{Bayes}} \cdot 0.6$

---

## 4. Probabilidades de Desempate

Cuando comparas tu mano con un rival, existen 3 escenarios mutuamente excluyentes:

$$
P(\text{ganar|posición}) = P(\text{rival} < \text{yo}) + P(\text{empate}) \cdot \delta_{\text{posición}}
$$

**Donde:**
- $P(\text{rival} < \text{yo})$: Probabilidad exacta de victoria estricta (desde dataset)
- $P(\text{empate})$: Probabilidad exacta de empate (desde dataset)
- $\delta_{\text{posición}}$: Factor de desempate según posición en la mesa

### Factores de Desempate por Posición

$$
\delta_{\text{posición}} = \begin{cases}
1.0 & \text{si posición 1 (Mano) - gana todos los empates} \\
0.5 & \text{si posición 2 o 3 - gana empates a uno, pierde a otro} \\
0.0 & \text{si posición 4 (Postre) - pierde todos los empates}
\end{cases}
$$

**Parejas:**
- (Posición 1, Posición 3) vs (Posición 2, Posición 4)

### Ejemplo Numérico

Mano: [12, 11, 10, 1] (juego 31)

Desde dataset:
- $P(\text{rival} < \text{yo}) = 0.7670$
- $P(\text{empate}) = 0.2330$ (23.3% de probabilidad de empate!)

**Probabilidades finales:**

| Posición | $\delta$ | $P(\text{ganar})$ | Cálculo |
|----------|----------|-------------------|---------|
| 1 (Mano) | 1.0 | 1.0000 | 0.7670 + 0.2330 × 1.0 |
| 2 | 0.5 | 0.8835 | 0.7670 + 0.2330 × 0.5 |
| 3 | 0.5 | 0.8835 | 0.7670 + 0.2330 × 0.5 |
| 4 (Postre) | 0.0 | 0.7670 | 0.7670 + 0.2330 × 0.0 |

**Impacto:** Posición 1 tiene 30.3% más probabilidad de ganar que posición 4 en esta mano.

---

## 5. Probabilidades Condicionadas Exactas

En lugar de aproximaciones lineales o heurísticas, el motor usa **probabilidades condicionadas exactas** precomputadas mediante simulación Monte Carlo con distribución hipergeométrica.

### Problema Fundamental

Cuando tengo una mano específica de 4 cartas, ¿cuál es la probabilidad de que al menos 1 de 2 rivales tenga pares o juego?

**Enfoque anterior (ELIMINADO en v2.3):**
- Pesos lineales arbitrarios (Rey=4, Caballo=2.5, As=1.5, Sota=1)
- Factor bayesiano: $f_{\text{Bayes}}(w) = 1.3 - \frac{w}{16} \cdot 0.6$
- ❌ **Problema**: Asume relación lineal entre cartas y probabilidades
- ❌ **Problema**: No respeta distribución hipergeométrica real

**Enfoque actual (v2.3):**
- ✅ Simulación Monte Carlo con 36 cartas disponibles (40 - 4 mías)
- ✅ Distribución hipergeométrica exacta
- ✅ Sin pesos arbitrarios ni factores lineales

### Método de Precomputación

Para cada mano única posible:

**1. Inicialización:**
```python
mi_mano = [12, 11, 10, 1]  # Ejemplo
baraja_disponible = [40 cartas] - mi_mano  # 36 cartas restantes
```

**2. Simulación Monte Carlo (10,000 iteraciones):**
```python
for i in range(10000):
    # Repartir 2 rivales con 4 cartas cada uno (de las 36 disponibles)
    rival_1 = random.sample(baraja_disponible, 4)
    rival_2 = random.sample(baraja_disponible - rival_1, 4)
    
    # Verificar si alguno tiene pares/juego
    if tiene_pares(rival_1) or tiene_pares(rival_2):
        contador_pares += 1
    
    if tiene_juego(rival_1) or tiene_juego(rival_2):
        contador_juego += 1
```

**3. Cálculo de probabilidades:**
$$
P_{RL}(\text{pares}|\text{mano}) = \frac{\text{contador\_pares}}{10000}
$$

$$
P_{RL}(\text{juego}|\text{mano}) = \frac{\text{contador\_juego}}{10000}
$$

### Resultados Almacenados

Las probabilidades se almacenan en CSV con las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| `mano` | Lista de 4 cartas ordenadas |
| `probabilidad_grande` | P(yo gano Grande) |
| `probabilidad_chica` | P(yo gano Chica) |
| `probabilidad_pares` | P(mi mano tiene pares) |
| `probabilidad_juego` | P(mi mano tiene juego) |
| `prob_rival_pares_condicionada` | **P(≥1 rival tiene pares \| mi mano)** |
| `prob_rival_juego_condicionada` | **P(≥1 rival tiene juego \| mi mano)** |

### Ejemplo Numérico Real

**Caso 1: Mano pesada [12, 12, 11, 11]**
- Mano de 2 pares potente
- Probabilidades precomputadas:
  - $P_{RL}(\text{pares}|\text{mano}) = 0.7810$ (78.1%)
  - $P_{RL}(\text{juego}|\text{mano}) = 0.4863$ (48.6%)
- **Interpretación**: Con esta mano, 78% de las veces al menos un rival tiene pares

**Caso 2: Mano ligera [1, 1, 1, 1]**
- 4 Ases (pares potentes)
- Probabilidades precomputadas:
  - $P_{RL}(\text{pares}|\text{mano}) = 0.7841$ (78.4%)
  - $P_{RL}(\text{juego}|\text{mano}) = 0.6272$ (62.7%)
- **Interpretación**: Aunque tengo pares, 78% de las veces un rival también tiene

**Caso 3: Mano sin figuras [4, 5, 6, 7]**
- Sin Reyes ni Ases
- Probabilidades precomputadas:
  - $P_{RL}(\text{pares}|\text{mano}) \approx 0.82$ (82%)
  - $P_{RL}(\text{juego}|\text{mano}) \approx 0.55$ (55%)
- **Interpretación**: Mazo enriquecido → rivales con mayor probabilidad

### Ventajas del Enfoque Exacto

| Aspecto | Heurística Lineal (v2.2) | Probabilidad Exacta (v2.3) |
|---------|--------------------------|----------------------------|
| **Base matemática** | Pesos arbitrarios | Distribución hipergeométrica |
| **Cálculo** | $f(w) = 1.3 - 0.6w/16$ | Simulación Monte Carlo |
| **Precisión** | Aproximación ±10% | Exacta (error Monte Carlo < 1%) |
| **Dependencias** | Asume linealidad | Considera combinatoria real |
| **Ejemplo [12,12,11,11]** | Factor 0.81 → ~77% | Exacto 78.1% |

### Integración en el Motor

```python
def calcular_prob_rival(lance, mano, estadisticas):
    """
    Obtiene P_RL precomputado desde dataset.
    
    Returns:
        float: Probabilidad condicionada exacta
    """
    mano_tuple = tuple(sorted(mano))
    
    if mano_tuple in estadisticas.manos_dict:
        if lance == 'pares':
            return estadisticas.manos_dict[mano_tuple]['prob_rival_pares_condicionada']
        elif lance == 'juego':
            return estadisticas.manos_dict[mano_tuple]['prob_rival_juego_condicionada']
    
    # Fallback: probabilidad general sin condicionar
    p_individual = estadisticas.estadisticas_generales[f'prob_tener_{lance}']
    return 1 - (1 - p_individual) ** 2
```

**Sin cálculos en tiempo real:** Solo lookup en diccionario O(1).

---

## 6. Política de Decisión Estocástica

Para evitar ser explotable, el motor usa una política estocástica con función sigmoide.

### Probabilidad de Cortar

$$
P(\text{Cortar}|\text{EV}) = \frac{1}{1 + e^{-k \cdot (\text{EV} - \mu)}}
$$

**Donde:**
- $\mu$: Umbral calibrado (valor medio donde $P(\text{Cortar}) = 0.5$)
- $k = 2.0$: Pendiente de la sigmoide (controla suavidad)
- EV: Valor esperado total calculado

### Ruido Gaussiano

Para añadir variabilidad adicional:

$$
\text{EV}_{\text{decisión}} = \text{EV}_{\text{Total}} + \mathcal{N}(0, \sigma^2)
$$

**Donde:**
- $\sigma = 0.15$: Desviación estándar del ruido

### Umbrales Calibrados (modo 8 reyes)

| Perfil | $\beta$ | $\mu$ | % Cortes Esperado |
|--------|---------|-------|-------------------|
| Conservador | 0.65 | 4.95 | ~31% |
| Normal | 0.75 | 4.34 | ~41% |
| Agresivo | 0.85 | 2.87 | ~60% |

**Calibración:** Los umbrales $\mu$ se ajustan automáticamente para lograr el porcentaje deseado de cortes sobre todas las manos posibles.

### Visualización

```
P(Cortar)
    1.0 ┤                              ╭───────
        ┤                          ╭───╯
    0.5 ┤                    ╭─────╯           μ
        ┤              ╭─────╯
    0.0 ┤──────────────╯
        └───────────────────────────────────▶ EV
```

**Propiedades:**
- Suave (no hay umbral duro)
- No explotable (incluye ruido)
- Ajustable (diferentes perfiles)

---

## 📊 Resumen de Constantes

### Valores Base de Lances (W)

| Lance | Valor |
|-------|-------|
| Grande | 1.0 |
| Chica | 1.0 |
| Pares | 1.0 |
| Medias | 2.0 |
| Duples | 3.0 |
| Juego | 1.0 |

### Ganancia Extra por Envites ($E_{\text{extra}}$)

| Lance | Swing |
|-------|-------|
| Pares/Medias/Duples | 1.5 |
| Juego | 2.0 |

### Factores de Ajuste

| Parámetro | Rango | Uso |
|-----------|-------|-----|
| $\beta$ (confianza compañero) | [0.65, 0.85] | EV Total |
| $f_{\text{ajuste}}$ | [1.0, 1.3] | EV Soporte Lineal |
| $f_{\text{red}}$ | {0.5, 1.0} | EV Soporte Condicionado |
| $f_{\text{Bayes}}$ | [0.7, 1.3] | Remoción de cartas |
| $\delta_{\text{posición}}$ | {0.0, 0.5, 1.0} | Desempates |

---

## ✅ Validación Matemática

### Propiedades Verificadas

1. **Linealidad del EV:**
   $$
   \text{EV}(a \cdot X_1 + b \cdot X_2) = a \cdot \text{EV}(X_1) + b \cdot \text{EV}(X_2)
   $$

2. **Conservación de probabilidades:**
   $$
   P(\text{rival} < \text{yo}) + P(\text{rival} = \text{yo}) + P(\text{rival} > \text{yo}) = 1.0
   $$

3. **Monotonicidad:**
   - A mayor peso → menor factor bayesiano
   - A mayor EV → mayor probabilidad de cortar
   - A mayor percentil → mayor probabilidad de ganar

4. **Simetría bayesiana (v2.2):**
   - Mismo $f_{\text{Bayes}}$ aplicado a compañero y rivales

### Tests Pasados

- ✅ 7/7 tests de desempates exactos
- ✅ Validación de factor bayesiano simétrico
- ✅ Casos extremos (Reyes vs basura)
- ✅ Convergencia estocástica

---

## 📚 Historial de Versiones

### v2.2 (27/02/2026) - Simetría Bayesiana
- **CRÍTICO:** Factor bayesiano aplicado simétricamente a rivales Y compañero
- Eliminado sesgo optimista en manos débiles
- Modificada `calcular_prob_rival()` para aceptar parámetro `mano`

### v2.1 (26/02/2026) - Desempates Exactos
- Reemplazados percentiles por probabilidades exactas
- Fórmula: $P(\text{ganar}) = P(\text{rival} < \text{yo}) + P(\text{empate}) \cdot \delta_{\text{posición}}$
- Factores de posición: {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}

### v2.0 (25/02/2026) - Factor Bayesiano
- Implementado cálculo de peso de mano
- Inferencia bayesiana por remoción de cartas
- Eliminados descuentos arbitrarios en $E_{\text{extra}}$

---

## 🎓 Referencias Teóricas

1. **Valor Esperado:**
   - $\text{EV}(X) = \sum_i P(x_i) \cdot x_i$

2. **Teorema de Bayes:**
   - $P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$

3. **Probabilidad Condicional:**
   - $P(A \cap B) = P(A|B) \cdot P(B)$

4. **Independencia:**
   - $P(A \cap B) = P(A) \cdot P(B)$ si A, B independientes

5. **Complemento:**
   - $P(\neg A) = 1 - P(A)$
   - $P(\text{al menos 1}) = 1 - P(\text{ninguno})$

---

**Documento actualizado:** 27 de febrero de 2026  
**Próxima fase:** Segundas dadas y estrategia de descarte
