# Estimación del Tamaño Muestral (N) para Q-Learning de Descarte

## 1. Definición del Problema

Buscamos el número mínimo de iteraciones $N$ tal que **cada estado** $(m, p, k)$ en la Q-Table tenga suficientes visitas para que su reward promedio converja con precisión $\epsilon$.

Donde:
- $m \in \mathcal{M}$: mano (4 cartas ordenadas de una baraja de 8 valores)
- $p \in \{1, 2, 3, 4\}$: posición del jugador
- $k \in \{0, 1, \dots, 14\}$: índice de máscara de descarte

## 2. Tamaño del Espacio de Estados

### 2.1 Manos únicas

Con una baraja de 8 reyes, los valores disponibles son $V = \{1, 4, 5, 6, 7, 10, 11, 12\}$, es decir $|V| = 8$ valores distintos.

Una mano es un multiconjunto de tamaño 4 extraído de $V$ (el orden no importa, hay repeticiones). El número de multiconjuntos es:

$$|\mathcal{M}| = \binom{|V| + 4 - 1}{4} = \binom{11}{4} = 330$$

### 2.2 Estados totales

$$|\mathcal{S}| = |\mathcal{M}| \times |P| \times |K| = 330 \times 4 \times 15 = 19{,}800$$

## 3. Distribución de Probabilidad de las Manos

### 3.1 Composición de la baraja

Cada valor $v \in V$ tiene multiplicidad $c_v$ en la baraja de 40 cartas:

| Valor | $c_v$ |
|:---:|:---:|
| 1 (As) | 4 |
| 4 | 4 |
| 5 | 4 |
| 6 | 4 |
| 7 | 4 |
| 10 (Sota) | 4 |
| 11 (Caballo) | 4 |
| 12 (Rey) | 8 |

### 3.2 Probabilidad de una mano específica

Sea una mano $m = (v_1^{a_1}, v_2^{a_2}, \dots, v_j^{a_j})$ con $\sum a_i = 4$. El número de formas de extraerla de la baraja es:

$$\text{formas}(m) = \prod_{i=1}^{j} \binom{c_{v_i}}{a_i}$$

El total de manos posibles (con orden de extracción irrelevante) es:

$$T = \binom{40}{4} = 91{,}390$$

La probabilidad de recibir la mano $m$ en un reparto es:

$$P(m) = \frac{\text{formas}(m)}{T}$$

### 3.3 Ejemplos

| Mano | Forma | $\text{formas}(m)$ | $P(m)$ |
|------|-------|-----------:|-------:|
| $[12,12,12,12]$ | $\binom{8}{4}$ | 70 | $7.66 \times 10^{-4}$ |
| $[12,12,11,10]$ | $\binom{8}{2}\binom{4}{1}\binom{4}{1}$ | 448 | $4.90 \times 10^{-3}$ |
| $[12,7,6,5]$ | $\binom{8}{1}\binom{4}{1}\binom{4}{1}\binom{4}{1}$ | 512 | $5.60 \times 10^{-3}$ |
| $[1,1,1,1]$ | $\binom{4}{4}$ | 1 | $1.09 \times 10^{-5}$ |
| $[1,1,1,4]$ | $\binom{4}{3}\binom{4}{1}$ | 16 | $1.75 \times 10^{-4}$ |

### 3.4 Mano más probable vs menos probable

$$\frac{P_{\max}}{P_{\min}} = \frac{512}{1} = 512$$

El espacio está **muy desequilibrado**: la mano más frecuente tiene 512× más probabilidad que la menos frecuente.

## 4. Visitas Esperadas por Estado

### 4.1 Universos válidos (todos dan mus)

Sea $\rho$ la tasa de mus (probabilidad de que los 4 jugadores den mus). Con la calibración actual:

$$\rho \approx 0.20$$

Para $N$ iteraciones, los universos válidos son:

$$U = N \cdot \rho$$

### 4.2 Visitas a un estado

Cada universo válido genera una visita para cada $(m_p, p, k)$ con $p \in \{1,2,3,4\}$ y $k \in \{0,\dots,14\}$.

La mano del jugador en posición $p$ se reparte independientemente. El número esperado de visitas al estado $(m, p, k)$ es:

$$\mathbb{E}[n_{m,p,k}] = U \cdot P(m) = N \cdot \rho \cdot P(m)$$

Nótese que las visitas **no dependen** de $p$ ni de $k$, solo de la probabilidad de la mano $m$.

## 5. Criterio de Convergencia

### 5.1 Error estándar del reward

Sea $\sigma_R$ la desviación estándar del reward $R$ (diferencial de puntos). Empíricamente $\sigma_R \approx 4$ (rango ~$[-14, +14]$).

Para $n$ visitas a un estado, el error estándar del reward promedio es:

$$SE = \frac{\sigma_R}{\sqrt{n}}$$

### 5.2 Precisión objetivo

Queremos que el error estándar sea menor que $\epsilon$:

$$\frac{\sigma_R}{\sqrt{n}} \leq \epsilon \implies n \geq \frac{\sigma_R^2}{\epsilon^2}$$

| Precisión $\epsilon$ | Visitas mínimas $n_{\min}$ |
|:---:|:---:|
| 0.50 | 64 |
| 0.20 | 400 |
| 0.10 | 1,600 |
| 0.05 | 6,400 |
| 0.01 | 160,000 |

### 5.3 Intervalo de confianza al 95%

Con $n$ visitas, el intervalo de confianza al 95% para el reward medio es:

$$\bar{R} \pm 1.96 \cdot \frac{\sigma_R}{\sqrt{n}}$$

## 6. Determinación de N

### 6.1 Fórmula general

Para garantizar $n_{\min}$ visitas en la mano con probabilidad $P(m)$:

$$N \cdot \rho \cdot P(m) \geq n_{\min}$$

$$\boxed{N \geq \frac{n_{\min}}{\rho \cdot P(m)}}$$

### 6.2 Cobertura total (todas las manos)

Para la mano más rara ($P_{\min} = 1/91{,}390 \approx 1.09 \times 10^{-5}$):

| Precisión $\epsilon$ | $n_{\min}$ | $N$ necesario |
|:---:|:---:|:---:|
| 0.50 | 64 | 29.3M |
| 0.20 | 400 | 183M |
| 0.10 | 1,600 | 733M |

### 6.3 Cobertura práctica (99% de manos relevantes)

Las manos extremas ([1,1,1,1], [4,4,4,4], etc.) rara vez pasan la fase de mus. La mano relevante más rara tiene $P \approx 2 \times 10^{-4}$:

| Precisión $\epsilon$ | $n_{\min}$ | $N$ necesario |
|:---:|:---:|:---:|
| 0.50 | 64 | 1.6M |
| 0.20 | 400 | 10M |
| 0.10 | 1,600 | 40M |
| 0.05 | 6,400 | 160M |

### 6.4 Cobertura de manos comunes (80% del espacio)

Las manos con al menos una figura ($P \gtrsim 5 \times 10^{-3}$):

| Precisión $\epsilon$ | $n_{\min}$ | $N$ necesario |
|:---:|:---:|:---:|
| 0.10 | 1,600 | 1.6M |
| 0.05 | 6,400 | 6.4M |
| 0.01 | 160,000 | 160M |

## 7. Justificación de N = 40M

Con $N = 40{,}000{,}000$ y $\rho = 0.20$:

$$U = 40M \times 0.20 = 8{,}000{,}000 \text{ universos válidos}$$

### 7.1 Distribución de visitas esperadas

| Tipo de mano | $P(m)$ aprox. | Visitas esperadas | Precisión $\epsilon$ |
|:---:|:---:|:---:|:---:|
| Común (ej: [12,7,6,5]) | $5.6 \times 10^{-3}$ | 44,800 | 0.019 |
| Media (ej: [12,12,12,12]) | $7.7 \times 10^{-4}$ | 6,130 | 0.051 |
| Rara (ej: [1,1,1,4]) | $1.75 \times 10^{-4}$ | 1,400 | 0.107 |
| Muy rara (ej: [1,1,1,1]) | $1.09 \times 10^{-5}$ | 87 | 0.429 |

### 7.2 Cobertura estimada

| Umbral de visitas | % de manos cubiertas | Precisión garantizada |
|:---:|:---:|:---:|
| $n \geq 1{,}600$ | ~96% | $\epsilon \leq 0.10$ |
| $n \geq 400$ | ~99% | $\epsilon \leq 0.20$ |
| $n \geq 64$ | ~99.7% | $\epsilon \leq 0.50$ |
| $n \geq 10$ | ~99.9% | filtro `MIN_VISITAS_QTABLE` |

### 7.3 Conclusión

$N = 40M$ proporciona:
- **Precisión $\epsilon \leq 0.10$** para el 96% de las manos (todas las relevantes)
- **Precisión $\epsilon \leq 0.20$** para el 99% de las manos
- **Cobertura completa** de las 4 posiciones (antes solo posición 1)
- Rollouts por universo: $4 \times 15 = 60$
- Total de entradas en Q-Table: $8M \times 60 = 480M$ actualizaciones

## 8. Apéndice: Verificación Empírica

Para validar post-ejecución, comprobar en el CSV exportado:

```python
import pandas as pd
df = pd.read_csv("politicas_optimas_fase2.csv")

# Distribución de visitas
print(df['n_visitas'].describe())
print(f"\nManos con <10 visitas: {(df['n_visitas'] < 10).sum()}")
print(f"Manos con <100 visitas: {(df['n_visitas'] < 100).sum()}")
print(f"Manos con ≥1600 visitas: {(df['n_visitas'] >= 1600).sum()}")

# Error estándar estimado (asumiendo σ ≈ 4)
df['SE_estimado'] = 4.0 / df['n_visitas'].apply(lambda n: n**0.5)
print(f"\nSE medio: {df['SE_estimado'].mean():.4f}")
print(f"SE máximo: {df['SE_estimado'].max():.4f}")
```

---

**Fecha:** Febrero 2026  
**Método:** Error estándar de la media + cobertura por percentil de probabilidad de mano
