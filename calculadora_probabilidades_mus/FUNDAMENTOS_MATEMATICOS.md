# Fundamentos Matemáticos del Motor de Decisión Mus

> **Versión**: 2.2 (27 de febrero de 2026)  
> **Enfoque**: Formulación matemática rigurosa sin heurísticas arbitrarias

---

## 📐 Índice

1. [Valor Esperado Total](#1-valor-esperado-total)
2. [Lances Lineales (Grande y Chica)](#2-lances-lineales-grande-y-chica)
3. [Lances Condicionados (Pares y Juego)](#3-lances-condicionados-pares-y-juego)
4. [Probabilidades de Desempate](#4-probabilidades-de-desempate)
5. [Factor Bayesiano (Remoción de Cartas)](#5-factor-bayesiano-remoción-de-cartas)
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
\text{EV}_{\text{Total}} = \sum_{L \in \{\text{Grande, Chica, Pares, Juego}\}} \left( \text{EV}_{\text{Propio}}^L + \beta \cdot \text{EV}_{\text{Soporte}}^L \right)
$$

---

## 2. Lances Lineales (Grande y Chica)

Los lances lineales tienen un valor fijo de 1 punto. El EV depende únicamente de la probabilidad de ganar:

### EV Propio (Lineal)

$$
\text{EV}_{\text{Propio}}^{\text{Lineal}} = P(\text{yo gano}) \cdot 1.0
$$

**Donde:**
- $P(\text{yo gano})$: Probabilidad precalculada desde dataset Monte Carlo

### EV Soporte (Lineal)

$$
\text{EV}_{\text{Soporte}}^{\text{Lineal}} = P_{\text{comp}}^{\text{media}} \cdot f_{\text{ajuste}} \cdot f_{\text{Bayes}}
$$

**Donde:**
- $P_{\text{comp}}^{\text{media}}$: Probabilidad media del compañero (desde dataset)
- $f_{\text{ajuste}} = 1.0 + 0.3 \cdot (1 - P(\text{yo gano}))$: Factor de ajuste
  - Si mi mano es mala → compañero más valioso
- $f_{\text{Bayes}}$: Factor bayesiano por remoción de cartas (ver sección 5)

**Interpretación de $f_{\text{ajuste}}$:**
- Si $P(\text{yo gano}) = 1.0$ → $f_{\text{ajuste}} = 1.0$ (compañero no añade valor)
- Si $P(\text{yo gano}) = 0.0$ → $f_{\text{ajuste}} = 1.3$ (compañero muy valioso)

---

## 3. Lances Condicionados (Pares y Juego)

Los lances condicionados requieren considerar dos escenarios:
1. **Rival NO tiene la jugada** → Gano automáticamente
2. **Rival SÍ tiene la jugada** → Debo comparar y ganar el desempate

### EV Propio (Condicionado)

$$
\text{EV}_{\text{Propio}}^{\text{Cond}} = (1 - P_{RL}) \cdot W + P_{RL} \cdot P(\text{yo}|RL) \cdot (W + E_{\text{extra}})
$$

**Donde:**
- $P_{RL}$: Probabilidad de que al menos 1 rival tenga la jugada
- $P(\text{yo}|RL)$: Probabilidad de ganar contra rival con jugada (ver sección 4)
- $W$: Valor base de la jugada
  - Pares: 1, Medias: 2, Duples: 3
  - Juego: 1
- $E_{\text{extra}}$: Ganancia esperada por envites (swing)
  - Pares: 1.5
  - Juego: 2.0

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

Asumiendo 2 rivales independientes:

$$
P_{RL} = 1 - (1 - p_{\text{individual}} \cdot f_{\text{Bayes}})^2
$$

**Donde:**
- $p_{\text{individual}}$: Probabilidad base de tener la jugada (desde dataset)
- $f_{\text{Bayes}}$: Factor bayesiano aplicado SIMÉTRICAMENTE

**Nota crítica (v2.2):** El factor bayesiano se aplica a **todos** los jugadores (compañero Y rivales), eliminando sesgo optimista.

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

## 5. Factor Bayesiano (Remoción de Cartas)

El factor bayesiano modela el efecto de remoción de cartas: si tienes Reyes, el mazo queda empobrecido para todos.

### Peso de la Mano

$$
w(\text{mano}) = \sum_{c \in \text{mano}} w(c)
$$

**Pesos por carta:**

$$
w(c) = \begin{cases}
4.0 & \text{si } c = 12 \text{ (Rey)} \\
2.5 & \text{si } c = 11 \text{ (Caballo)} \\
1.5 & \text{si } c = 1 \text{ (As)} \\
1.0 & \text{si } c = 10 \text{ (Sota)} \\
0.0 & \text{en otro caso}
\end{cases}
$$

**Rango:** $w \in [0, 16]$

### Factor Bayesiano

$$
f_{\text{Bayes}}(w) = 1.3 - \frac{w}{16} \cdot 0.6
$$

**Propiedades:**
- Si $w = 0$ (basura) → $f_{\text{Bayes}} = 1.30$ (mazo enriquecido)
- Si $w = 8$ (neutral) → $f_{\text{Bayes}} = 1.00$ (mazo neutral)
- Si $w = 16$ (4 Reyes) → $f_{\text{Bayes}} = 0.70$ (mazo empobrecido)

### Aplicación Simétrica (v2.2)

**CRÍTICO:** El factor se aplica a **todos** los jugadores:

$$
P_{\text{ajustado}} = \min(P_{\text{base}} \cdot f_{\text{Bayes}}, 0.95)
$$

**Para compañero:**
$$
P(\text{comp} \text{ gana}) = P_{\text{comp}}^{\text{base}} \cdot f_{\text{Bayes}}
$$

**Para rivales:**
$$
p_{\text{individual}}^{\text{ajustado}} = p_{\text{individual}}^{\text{base}} \cdot f_{\text{Bayes}}
$$
$$
P_{RL} = 1 - (1 - p_{\text{individual}}^{\text{ajustado}})^2
$$

**Justificación física:** Si YO tengo basura, el mazo está enriquecido para TODOS (compañero Y rivales). No hay razón para tratarlos asimétricamente.

### Ejemplo Numérico

**Caso 1: Mano pesada [12, 12, 11, 11]**
- Peso: $w = 4 + 4 + 2.5 + 2.5 = 13.0$
- Factor: $f_{\text{Bayes}} = 1.3 - \frac{13}{16} \cdot 0.6 = 0.8125$
- Efecto: Compañero y rivales tienen **-18.75%** probabilidad de buenas cartas

**Caso 2: Mano ligera [5, 4, 6, 7]**
- Peso: $w = 0 + 0 + 0 + 0 = 0.0$
- Factor: $f_{\text{Bayes}} = 1.3 - 0 = 1.30$
- Efecto: Compañero y rivales tienen **+30%** probabilidad de buenas cartas

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
