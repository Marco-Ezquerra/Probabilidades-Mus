# 📦 Módulo: calculadora_probabilidades_mus

Motor de decisión para Mus basado en **Valor Esperado (EV)** con fundamentos matemáticos rigurosos.

**Versión:** 2.2 (27 de febrero de 2026)

---

## 📚 Documentación Matemática

| Documento | Descripción |
|-----------|-------------|
| **[FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md)** | 📐 **PIZARRA PRINCIPAL** - Formulación matemática completa |
| **[DESEMPATES_MATEMATICOS.md](DESEMPATES_MATEMATICOS.md)** | 🎯 Implementación de desempates exactos y tests |

---

## 🎲 Archivos Principales

### `calculadoramus.py`
**Simulador Monte Carlo** - Genera estadísticas a priori mediante 50-100k simulaciones.

```bash
python3 calculadoramus.py  # Genera resultados_{4,8}reyes.csv
```

### `motor_decision.py`
**Motor de decisión basado en EV**

**Formulación:**
$$
\text{EV}_{\text{Total}} = \text{EV}_{\text{Propio}} + \beta \cdot \text{EV}_{\text{Soporte}}
$$

**Características:**
- Desempates exactos: $P(\text{ganar}) = P(\text{rival} < \text{yo}) + P(\text{empate}) \cdot \delta_{\text{posición}}$
- Factor bayesiano simétrico (remoción de cartas)
- Política estocástica (sigmoide + ruido gaussiano)

**Perfiles:**

| Perfil | $\beta$ | $\mu$ | % Cortes |
|--------|---------|-------|----------|
| Conservador | 0.65 | 4.95 | ~31% |
| Normal | 0.75 | 4.34 | ~41% |
| Agresivo | 0.85 | 2.87 | ~60% |

**Uso:**
```python
from motor_decision import MotorDecisionMus

motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
decision, P_cortar, EV, desglose = motor.decidir([12,11,10,1], posicion=1)
```

### `analizar_mano_detallado.py`
**Análisis paso a paso con desglose matemático**

```bash
python3 analizar_mano_detallado.py --mano 12 11 10 1 --posicion 1 --beta 0.75
```

Muestra:
- Cálculo de EV por lance
- Probabilidades exactas ($P(\text{menor})$, $P(\text{empate})$)
- Factor bayesiano aplicado
- Impacto de $\beta$ en EV de soporte

### `test_motor_desempates.py`
**Suite de 7 tests automáticos**

```bash
python3 test_motor_desempates.py  # ✅ 7/7 pasados
```

Valida:
1. Probabilidades exactas
2. Impacto de posición
3. Casos límite
4. Casos típicos
5. Comparación sistemática
6. Estabilidad sin empate
7. Estocasticidad

### `prueba_bayesiana.py`
**Validador de simetría bayesiana (v2.2)**

```bash
python3 prueba_bayesiana.py
```

Verifica que $f_{\text{Bayes}}$ se aplica simétricamente a compañero Y rivales.

---

## 📊 Datasets

| Archivo | Contenido | Generado Por |
|---------|-----------|-------------|
| `resultados_4reyes.csv` | 715 manos únicas (4 reyes) | calculadoramus.py |
| `resultados_8reyes.csv` | 245 manos únicas (8 reyes) | calculadoramus.py |
| `calibracion_mu.json` | Umbrales $\mu$ por perfil | motor_decision.py |

---

## 🧮 Formulación Matemática Clave

### Valor Esperado Total

$$
\text{EV}_{\text{Total}} = \sum_{L \in \{\text{G, Ch, P, J}\}} \left( \text{EV}_{\text{Propio}}^L + \beta \cdot \text{EV}_{\text{Soporte}}^L \right)
$$

### Lance Lineal (Grande, Chica)

$$
\text{EV}_{\text{Propio}}^{\text{Lineal}} = P(\text{yo gano}) \cdot 1.0
$$

### Lance Condicionado (Pares, Juego)

$$
\text{EV}_{\text{Propio}}^{\text{Cond}} = (1 - P_{RL}) \cdot W + P_{RL} \cdot P(\text{yo}|RL) \cdot (W + E_{\text{extra}})
$$

**Donde:**
$$
\begin{aligned}
P_{RL} &= 1 - (1 - p_{\text{individual}} \cdot f_{\text{Bayes}})^2 \\
P(\text{yo}|RL) &= P(\text{rival} < \text{yo}) + P(\text{empate}) \cdot \delta_{\text{posición}} \\
\delta_{\text{posición}} &\in \{1.0, 0.5, 0.5, 0.0\} \text{ para pos } \{1, 2, 3, 4\}
\end{aligned}
$$

### Factor Bayesiano

$$
f_{\text{Bayes}}(w) = 1.3 - \frac{w}{16} \cdot 0.6
$$

**Peso:** $w = \sum_{c \in \text{mano}} w(c)$

| Carta | Peso |
|-------|------|
| Rey (12) | 4.0 |
| Caballo (11) | 2.5 |
| As (1) | 1.5 |
| Sota (10) | 1.0 |
| Resto | 0.0 |

### Política de Decisión

$$
P(\text{Cortar}|\text{EV}) = \frac{1}{1 + e^{-k \cdot (\text{EV} - \mu)}}
$$

Con ruido: $\text{EV}_{\text{decisión}} = \text{EV}_{\text{Total}} + \mathcal{N}(0, 0.15^2)$

---

## ✅ Estado del Proyecto

| Característica | Estado |
|----------------|--------|
| Tests automáticos | ✅ 7/7 pasados |
| Versión actual | Motor v2.2 |
| Desempates exactos | ✅ Implementado |
| Simetría bayesiana | ✅ Corregido (v2.2) |
| Documentación matemática | ✅ Completa |

**Próxima fase:** Segundas dadas y estrategia de descarte

---

## 🎯 Ejemplo de Uso

```python
from motor_decision import MotorDecisionMus

# Inicializar motor
motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')

# Mano con alto empate (31)
mano = [12, 11, 10, 1]

# Decidir desde posición 1 (Mano)
decision, P_cortar, EV, desglose = motor.decidir(mano, posicion=1)
print(f"Posición 1: EV={EV:.2f}, P(Cortar)={P_cortar:.1%}")
# Output: Posición 1: EV=4.84, P(Cortar)=89.6%

# Decidir desde posición 4 (Postre)
decision, P_cortar, EV, desglose = motor.decidir(mano, posicion=4)
print(f"Posición 4: EV={EV:.2f}, P(Cortar)={P_cortar:.1%}")
# Output: Posición 4: EV=4.24, P(Cortar)=84.7%

# Diferencia por posición: +14.2% en EV por estar en Mano
```

---

**Ver [FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md) para teoría completa**
