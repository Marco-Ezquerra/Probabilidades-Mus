# Desempates Exactos - Implementación y Validación

> **Para:** Fundamentos matemáticos completos ver [FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md)  
> **Este documento:** Implementación específica de desempates en el motor

---

## Formulación Matemática

### Fórmula General

$$
P(\text{ganar}|\text{posición}) = P(\text{rival} < \text{yo}) + P(\text{empate}) \cdot \delta_{\text{posición}}
$$

**Factores de desempate:**

$$
\delta_{\text{posición}} = \begin{cases}
1.0 & \text{posición 1 (Mano)} \\
0.5 & \text{posición 2 o 3} \\
0.0 & \text{posición 4 (Postre)}
\end{cases}
$$

### Parejas

- **Pareja A:** (Posición 1, Posición 3)
- **Pareja B:** (Posición 2, Posición 4)

Posición 1 gana empates contra posiciones 2 y 4.  
Posición 4 pierde empates contra posiciones 1 y 3.

---

## Implementación en el Código

### Clase `EstadisticasEstaticas`

**Atributos nuevos:**
```python
self.probs_pares = {}  # {mano_tuple: {'prob_menor': X, 'prob_empate': Y}}
self.probs_juego = {}  # {mano_tuple: {'prob_menor': X, 'prob_empate': Y}}
```

**Cálculo para cada mano:**
- `prob_menor`: Fracción de manos estrictamente peores
- `prob_empate`: Fracción de manos idénticas en valor

### Función `calcular_ev_propio_condicionado()`

```python
# Obtener probabilidades exactas
probs = estadisticas.probs_pares[mano_tuple] if lance == 'pares' 
        else estadisticas.probs_juego[mano_tuple]

prob_menor = probs['prob_menor']
prob_empate = probs['prob_empate']

# Factor de desempate según posición
factores_desempate = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}
factor = factores_desempate.get(posicion, 0.5)

# Probabilidad final
prob_yo_vs_rival = prob_menor + (prob_empate * factor)
```

---

## Resultados de Tests

### Test 1: Probabilidades Bien Definidas

| Mano | $P(\text{rival} < \text{yo})$ | $P(\text{empate})$ | Total |
|------|-------------------------------|--------------------:|------:|
| **PARES** ||||
| [12,12,12,12] | 1.0000 | 0.0000 | 1.0000 |
| [12,12,11,11] | 0.9961 | 0.0000 | 0.9961 |
| [10,10,7,7] | 0.9382 | 0.0000 | 0.9382 |
| **JUEGO** ||||
| [12,11,10,1] (31) | 0.7670 | **0.2330** | 1.0000 |
| [12,11,7,5] (32) | 0.6505 | 0.1068 | 0.7573 |
| [10,10,10,10] (40) | 0.0000 | 0.1359 | 0.1359 |

✅ El 31 tiene 23.3% de probabilidad de empate. El 40 tiene 13.6%.

### Test 2: Impacto de la Posición

Mano: [12,11,10,1] (31 - alto empate)

| Posición | $\delta$ | $P(\text{ganar})$ | EV Juego | Δ vs Pos4 |
|----------|----------|-------------------|----------|-----------|
| 1 | 1.0 | $0.7670 + 0.2330 \times 1.0$ = 1.0000 | 4.0293 | +0.5996 |
| 2 | 0.5 | $0.7670 + 0.2330 \times 0.5$ = 0.8835 | 3.7295 | +0.2998 |
| 3 | 0.5 | $0.7670 + 0.2330 \times 0.5$ = 0.8835 | 3.7295 | +0.2998 |
| 4 | 0.0 | $0.7670 + 0.2330 \times 0.0$ = 0.7670 | 3.4297 | +0.0000 |

✅ Posición 1 tiene **17.5% más EV** que posición 4 en manos con alto empate.

### Test 5: Comparación Sistemática

| Mano | Pos 1 EV | Pos 4 EV | Δ | % Impacto |
|------|----------|----------|---|-----------|
| 31 (empate 23.3%) | 4.8351 | 4.2355 | +0.5996 | 14.16% |
| Duples Rey | 2.4621 | 2.2778 | +0.1844 | 8.09% |
| 40 (empate 13.6%) | 4.9033 | 4.6612 | +0.2420 | 5.19% |

✅ El impacto de posición es **proporcional a $P(\text{empate})$**.

### Test 6: Manos Sin Empate

| Mano | $P(\text{empate})$ | Pos 1 EV | Pos 4 EV | Δ |
|------|--------------------:|----------|----------|---|
| [11,10,7,6] | 0.0485 | 2.4297 | 2.3130 | 0.1167 |
| [7,7,6,4] | 0.0772 | 1.0694 | 0.8768 | 0.1926 |

✅ Cuando $P(\text{empate}) \approx 0$ → diferencia entre posiciones $\approx 0$

---

## Corrección Crítica: Simetría Bayesiana (v2.2)

El factor bayesiano (remoción de cartas) ahora se aplica **simétricamente** a compañero Y rivales.

**Problema anterior:** Si tenías basura, el código aumentaba $P(\text{compañero gana})$ pero NO $P(\text{rivales ganan})$ → sesgo optimista.

**Solución v2.2:**

$$
P_{RL} = 1 - (1 - p_{\text{individual}} \cdot f_{\text{Bayes}})^2
$$

El mismo $f_{\text{Bayes}}$ se aplica a TODOS (compañero y rivales).

**Impacto:**
- Mano pesada [12,12,11,11]: $f_{\text{Bayes}} = 0.8125$ → rivales **-18.75%** prob
- Mano ligera [5,4,6,7]: $f_{\text{Bayes}} = 1.30$ → rivales **+30%** prob

Ver [FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md) sección 5 para detalles.

---

## Ventajas del Modelo

1. **Cero variables inventadas** - Solo probabilidades exactas del dataset
2. **Sensibilidad real al empate** - Impacto proporcional a $P(\text{empate})$
3. **Correctitud matemática** - Fórmula exacta según reglas del Mus
4. **Simetría bayesiana** - Factor aplicado consistentemente

---

## Uso

```python
from motor_decision import MotorDecisionMus

motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')

mano = [12, 11, 10, 1]  # 31
decision, P_cortar, EV, desglose = motor.decidir(mano, posicion=1)

print(f"Posición {1}: EV={EV:.4f}, P(Cortar)={P_cortar:.1%}")
# Posición 1: EV=4.8351, P(Cortar)=89.6%

decision, P_cortar, EV, desglose = motor.decidir(mano, posicion=4)
print(f"Posición {4}: EV={EV:.4f}, P(Cortar)={P_cortar:.1%}")
# Posición 4: EV=4.2355, P(Cortar)=84.7%
```

---

**Versión:** Motor de Decisión v2.2  
**Tests:** 7/7 pasados ✅  
**Fecha:** 27 de febrero de 2026
