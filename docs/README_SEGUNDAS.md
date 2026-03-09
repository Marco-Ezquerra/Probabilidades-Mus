# Probabilidades de Victoria "A Segundas"
## Estimación Monte Carlo Condicionada al Descarte Rival

**Archivo**: `calculadora_probabilidades_mus/probabilidades_segundas.py`  
**Outputs**: `probabilidades_segundas.csv` · `resumen_segundas.csv`  
**Versión**: v2.6 · Marzo 2026

---

## 1. Qué calcula este módulo

Cuando un jugador pide **Mus** y se produce la fase de descarte, cada jugador descarta algunas cartas y roba otras nuevas. La señal observable que queda en la mesa es **cuántas cartas ha guardado cada jugador** (`n_kept ∈ {0,1,2,3}`), no cuáles.

Este módulo calcula, para cada combinación posible de esa información:

$$P(J_1 \text{ gana el lance } L \;|\; h_1,\, \text{pos}_1,\, k_2,\, k_3,\, k_4)$$

donde $h_1$ es la mano final conocida del jugador focal $J_1$, $\text{pos}_1 \in \{1,2,3,4\}$ es su posición en la mesa, y $k_j \in \{0,1,2,3\}$ son las cartas que ha guardado cada uno de los otros tres jugadores.

Los **cuatro lances** calculados son: Grande, Chica, Pares (equipo A), Juego/Punto (equipo A).

---

## 2. Modelo Matemático

### 2.1 Espacio de Probabilidad

Sea $B$ la baraja ($|B| = 40$ en modo 8 reyes). Fijada la mano del jugador focal $h_1 \subset B$, el espacio muestral elemental es:

$$\Omega = \bigl\{\, (h_2, h_3, h_4) \;:\; h_j \subset B \setminus h_1,\; |h_j| = 4,\; h_j \cap h_{j'} = \emptyset \;\forall\, j \neq j' \,\bigr\}$$

### 2.2 Proceso de Descarte

Cada jugador $j$ recibe un reparto inicial $r_j$ (4 cartas uniformes de las cartas no asignadas), aplica una **política de descarte** $\pi_j : \mathcal{H} \times \{1..4\} \to \mathcal{P}(\{0,1,2,3\})$, y roba tantas cartas como ha descartado:

$$n_{\text{kept},j} := 4 - |\pi_j(r_j, \text{pos}_j)| \in \{0, 1, 2, 3\}$$

| valor | significado |
|:-----:|-------------|
| 0 | descarta las 4 cartas (Mus completo) |
| 1 | guarda 1, descarta 3 |
| 2 | guarda 2, descarta 2 |
| 3 | guarda 3, descarta solo 1 |
| 4 | **imposible** — al pedir Mus se descarta al menos 1 |

### 2.3 Política Óptima π*

La política óptima $\pi^*$ se toma de la **Q-table** (Fase 2, Q-Learning con 40M partidas simuladas). Para cada par (mano, posición) se elige la máscara de descarte que maximiza el reward esperado:

$$\pi^*(h, \text{pos}) = \underset{m \in \mathcal{M}}{\arg\max}\; Q(h, \text{pos}, m)$$

donde $\mathcal{M} = \texttt{MASCARAS\_DESCARTE}$ contiene las **15 máscaras** posibles (todos los subconjuntos no vacíos de $\{0,1,2,3\}$ como índices de la mano ordenada descendentemente).

### 2.4 Estimador Monte Carlo por Rejection Sampling

La distribución objetivo es $P(h_2, h_3, h_4 \mid k_2, k_3, k_4)$ bajo la hipótesis de que todos juegan con $\pi^*$. Por el **Teorema de Bayes**:

$$P_\text{acc}(r_2, r_3, r_4) \;\propto\; P_\text{prior}(r_2, r_3, r_4) \;\cdot\; \mathbf{1}\!\left[n_{\text{kept},2} = k_2\right]\cdot \mathbf{1}\!\left[n_{\text{kept},3} = k_3\right]\cdot \mathbf{1}\!\left[n_{\text{kept},4} = k_4\right]$$

El estimador finalmente es:

$$\hat{P}(J_1 \text{ gana } L) = \frac{1}{N_\text{acc}} \sum_{i=1}^{N_\text{acc}} \mathbf{1}\!\left[J_1 \text{ gana } L \text{ en la muestra aceptada } \omega_i\right]$$

**Algoritmo RS** (Rejection Sampling bajo $\pi^*$):

```
for t = 1 … MAX_ATTEMPTS:
  1. PROPONER  : muestrear uniformemente (r₂, r₃, r₄) ⊂ B \ h₁ (4 cartas c/u)
  2. POLÍTICAS : calcular π*(rⱼ, posⱼ) para cada j ∈ {comp, rival1, rival2}
  3. OBSERVAR  : n̂ⱼ = 4 − |π*(rⱼ, posⱼ)|
  4. ACEPTAR   : si n̂₂ = k₂  ∧  n̂₃ = k₃  ∧  n̂₄ = k₄  → aceptar
     RECHAZAR  : en otro caso → continue (early-exit al primer fallo)
  5. COMPLETAR : cada rival roba (4 − n̂ⱼ) cartas del pozo residual
  6. EVALUAR   : computar ganadores de Grande, Chica, Pares, Juego
  7. ACUMULAR  : win_L += 1  si J₁ gana el lance L

devolver P̂ si N_acc ≥ N_SIMS_MIN;  None si la configuración es inviable bajo π*
```

---

## 3. Garantías Estadísticas

Por el **Teorema Central del Límite**, $\hat{P}$ es asintóticamente normal:

$$\sqrt{N_\text{acc}} \cdot (\hat{P} - p) \;\xrightarrow{d}\; \mathcal{N}(0,\; p(1-p))$$

El **intervalo de confianza al 95%** (con $z_{0.025} = 1.96$) tiene anchura máxima:

$$E = 1.96 \cdot \sqrt{\frac{0.25}{N_\text{acc}}}$$

que es máxima en el peor caso $p = 0.5$. Despejando el tamaño muestral mínimo:

$$n_\text{min}(E) = \left\lceil \left(\frac{1.96}{E}\right)^2 \cdot 0.25 \right\rceil$$

| Margen $E$ | $n_\text{min}$ | Uso en este módulo |
|:----------:|:-----------:|---------------------|
| 1 % | **9 604** | `N_SIMS_TARGET = 10 000` — objetivo en configs comunes |
| 5 % | **385** | `N_SIMS_MIN = 400` — mínimo; por debajo → `None` |

---

## 4. Dimensionamiento de MAX_ATTEMPTS

La **tasa de aceptación conjunta** bajo $\pi^*$:

$$\alpha_\text{config} = \alpha_2 \cdot \alpha_3 \cdot \alpha_4 \qquad \text{donde } \alpha_j = P\!\left(n_{\text{kept},j} = k_j \;\big|\; \pi^*\right)$$

El número esperado de muestras aceptadas es $\mathbb{E}[N_\text{acc}] = \texttt{MAX\_ATTEMPTS} \cdot \alpha_\text{config}$.

| Tipo de config | $\alpha_\text{config}$ estimada | $\mathbb{E}[N_\text{acc}]$ con 500k intentos | Resultado |
|----------------|:-------------------------------:|:-------------------------------------------:|-----------|
| Común  — $k = (2, 2, 2)$ | ≈ 4.3 % | ≈ 21 500 | ≥ `N_SIMS_TARGET` ✓ |
| Moderada — $k = (1, 1, 1)$ | ≈ 0.3 % | ≈ 1 500 | ≥ `N_SIMS_MIN` ✓ |
| Rara — $k = (0, 0, 0)$ | ≈ 0.01 % | ≈ 62 | < `N_SIMS_MIN` → `None` ✓ |

---

## 5. Dimensiones del Problema

| Dimensión | Valor |
|-----------|------:|
| Manos únicas $\|H\|$ | 330 |
| Posiciones focales | 4 |
| Configs $(k_2, k_3, k_4) \in \{0,1,2,3\}^3$ | 64 |
| **Total de estados** | **84 480** |
| Lances estimados por estado | 4 (Grande, Chica, Pares, Juego) |
| Workers paralelos | 4 |

---

## 6. Estimación de Tiempo de Ejecución

### Benchmark real (máquina de desarrollo, 4 cores)

| Config tipo | Tiempo por tarea | Motivo |
|-------------|:----------------:|--------|
| `(2,2,2)` — común | **1.2 s** | `N_acc ≈ 21 500`: alcanza `N_SIMS_TARGET` pronto |
| `(1,1,1)` — moderada | **4.0 s** | `α_config ≈ 0.3 %`: agota casi todo `MAX_ATTEMPTS` |
| `(0,2,2)` — rara | **4.0 s** | `α_config ≈ 0.01 %`: agota `MAX_ATTEMPTS`, devuelve `None` |

### Cálculo de tiempo total

De las 64 configs, **8** tienen todos los $k_j \in \{2,3\}$ (comunes, ~1.2s) y las **56** restantes tienen al menos un $k_j \in \{0,1\}$ (raras/moderadas, ~4s):

$$T_\text{pared} = \frac{330 \times 4 \times (8 \times 1.2 + 56 \times 4)}{4 \text{ workers}} = \frac{330 \times 4 \times 233.6}{4} \approx 77\,000\text{ s} \approx \mathbf{21\text{ horas}}$$

> **Estimación práctica: 18 – 24 horas** con 4 workers en paralelo.
> 
> El tiempo varía según las tasas de aceptación reales de la Q-table.  
> La barra de progreso `tqdm` muestra el porcentaje completado y la ETA en tiempo real.

---

## 7. Estructura de Outputs

### `probabilidades_segundas.csv` — tabla completa

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `mano` | str | Mano del jugador focal, e.g. `"[12, 12, 12, 1]"` |
| `posicion_focal` | int | Posición en la mesa: 1 (Mano) … 4 (Postre) |
| `n_kept_comp` | int | Cartas guardadas por el compañero $\in \{0,1,2,3\}$ |
| `n_kept_rival1` | int | Cartas guardadas por el rival 1 $\in \{0,1,2,3\}$ |
| `n_kept_rival2` | int | Cartas guardadas por el rival 2 $\in \{0,1,2,3\}$ |
| `prob_grande` | float\|None | $\hat{P}(J_1 \text{ gana Grande})$ |
| `prob_chica` | float\|None | $\hat{P}(J_1 \text{ gana Chica})$ |
| `prob_pares` | float\|None | $\hat{P}(\text{Equipo A gana Pares})$ |
| `prob_juego` | float\|None | $\hat{P}(\text{Equipo A gana Juego/Punto})$ |
| `n_sims` | int | $N_\text{acc}$ — muestras aceptadas efectivamente usadas |

`None` indica que la config es **inviable bajo** $\pi^*$ ($N_\text{acc} < 400$): los rivales nunca guardarían exactamente esas cartas según su política óptima.

### `resumen_segundas.csv` — agregado por config

Promedia `prob_*` sobre las 330 manos para cada combinación `(posicion_focal, config)`.  
Contiene solo filas válidas (sin `None`). Útil para análisis de sensibilidad.

---

## 8. Cómo Ejecutar

### 8.1 Ejecución estándar (con barra de progreso)

```bash
cd calculadora_probabilidades_mus
python probabilidades_segundas.py
```

La barra de progreso muestra:
```
Simulando:  23%|████████▌                            | 19 430/84 480 [1:12:33<3:54:21, 4.63cfg/s]
```

### 8.2 Ejecución en background (redirigiendo logs)

**Windows PowerShell:**
```powershell
cd calculadora_probabilidades_mus
Start-Process python -ArgumentList "probabilidades_segundas.py" `
    -RedirectStandardOutput "..\logs\seg_out.txt" `
    -RedirectStandardError  "..\logs\seg_err.txt" `
    -NoNewWindow
```

**Linux / macOS:**
```bash
nohup python probabilidades_segundas.py \
    > ../logs/seg_out.txt 2> ../logs/seg_err.txt &
echo "PID: $!"
```

### 8.3 Monitorear progreso (Windows)

```powershell
# Ver las últimas líneas del log en tiempo real
Get-Content logs\seg_out.txt -Wait -Tail 5
```

---

## 9. Validación de Resultados

Una vez generado el CSV, se puede verificar la coherencia con:

```python
import pandas as pd

df = pd.read_csv("probabilidades_segundas.csv")

# Sanity check: para manos de As, la prob_grande debe ser BAJA (As es carta pequeña)
as_manos = df[df['mano'].str.startswith('[1,') | df['mano'].str.startswith('[1 ,')]
print("P(Grande) media para manos con As:", as_manos['prob_grande'].mean())

# Sanity check: para manos de figuras (Rey=12), prob_grande debe ser ALTA
rey_manos = df[df['mano'].str.startswith('[12, 12')]
print("P(Grande) media para manos de Reyes:", rey_manos['prob_grande'].mean())

# Fracción de configs inviables bajo pi*
print(f"Configs None: {df['prob_grande'].isna().sum():,} / {len(df):,} ({100*df['prob_grande'].isna().mean():.1f}%)")
```

---

## 10. Integración con la App (Tab 2)

La app Streamlit en `demos/app.py` carga el CSV y permite consultar interactivamente:

1. **Seleccionar la mano** del jugador focal (4 cartas)
2. **Elegir su posición** en la mesa (1–4)
3. **Informar cuántas cartas guardó** cada rivals/compañero ($k_j \in \{0,1,2,3\}$)
4. La app devuelve el vector de probabilidades $(\hat{P}_G, \hat{P}_C, \hat{P}_P, \hat{P}_J)$

Las configs imposibles bajo $\pi^*$ se muestran como `—` con el tooltip *"Config imposible bajo política óptima"*.

---

## 11. Relación con las Probabilidades de Primeras

Las **probabilidades de primeras** (Fase 1) calculan $P(J_1 \text{ gana } L \mid h_1, \text{pos}_1)$ sin ninguna información adicional — integran sobre todos los posibles $h_2, h_3, h_4$.

Las **probabilidades de segundas** condicionan sobre $(k_2, k_3, k_4)$, que revelan información sobre la calidad de las manos rivales a través de la política óptima $\pi^*$. Intuitivamente:

- Rival que guarda **3 cartas** → tenía una mano buena → sus cartas finales son fuertes
- Rival que guarda **0 cartas** → descarta todo → su mano inicial era muy débil

Esta señal actualiza las probabilidades de manera similar al **Teorema de Bayes**: la política $\pi^*$ actúa como un mecanismo de revelación parcial de información.
