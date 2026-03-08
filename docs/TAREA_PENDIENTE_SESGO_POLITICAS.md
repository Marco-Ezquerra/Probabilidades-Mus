# Tarea Pendiente: Re-ejecución de Políticas de Descarte

**Estado:** Pendiente — los resultados actuales son válidos para análisis cualitativo pero tienen un sesgo cuantificable en el lance de Juego.

---

## 1. Origen del Sesgo

La función `_calcular_probabilidades_juego` en `motor_decision.py` calcula para cada mano con juego la probabilidad de que un rival aleatorio tenga un juego **peor** (`prob_menor`). Esta probabilidad alimenta el EV del lance de Juego y determina si el motor decide CORTAR o dar MUS durante el rollout.

La comparación original usaba el **valor numérico bruto**:

```python
# VERSIÓN CON BUG (ya corregida en código, commit 7190065)
if mano_j['valor_juego'] > mano_i['valor_juego']:
    n_menores += 1   # "j tiene peor juego que i"
```

El problema es que la jerarquía del Mus **no es monotónica** respecto al valor numérico:

| Posición jerárquica | Juego | Valor numérico | Rango correcto |
|---------------------|-------|---------------|----------------|
| 1ª (mejor) | 31 | 31 (mínimo) | 8 |
| 2ª | 32 | 32 | 7 |
| 3ª | **40** | **40 (máximo)** | **6** |
| 4ª | 37 | 37 | 5 |
| 5ª | 36 | 36 | 4 |
| 6ª | 35 | 35 | 3 |
| 7ª | 34 | 34 | 2 |
| 8ª (peor) | 33 | 33 | 1 |

El 40 es el 3er mejor juego pero tiene el mayor valor numérico. La comparación directa lo trata como el "mejor" y no encuentra ningún rival "peor" → su `prob_menor` resulta 0.

Notar que **31 y 32 son accidentalmente correctos**: 31 tiene el valor numérico mínimo Y el rango máximo; 32 es el segundo mínimo Y el segundo rango. A partir de 33 el orden numérico y el jerárquico divergen completamente.

---

## 2. Cuantificación del Sesgo

Distribución en baraja de 8 reyes: **104 manos únicas con juego** (de 330 totales, 31.5%).

| Juego | Rango | N manos | `prob_menor` con bug | `prob_menor` correcto | Δ (bug − correcto) |
|-------|-------|---------|---------------------|----------------------|--------------------|
| 31 | 8 | 25 | 0.767 | 0.767 | **0.000** ✓ |
| 32 | 7 | 12 | 0.650 | 0.650 | **0.000** ✓ |
| **40** | **6** | **15** | **0.000** | **0.505** | **−0.505** (severo) |
| 37 | 5 | 10 | ~0.146 | ~0.408 | ~**−0.262** |
| 36 | 4 | 10 | ~0.243 | ~0.311 | ~**−0.068** |
| 35 | 3 | 10 | ~0.340 | ~0.214 | ~**+0.126** |
| **34** | **2** | **16** | **~0.437** | **0.058** | ~**+0.379** (severo) |
| **33** | **1** | 6 | **~0.592** | **0.000** | ~**+0.592** (severo) |

Impacto en EV_J para juego=40 (W=2, P_RL≈0.34):
```
EV_J correcto = (1−0.34)×2 + 0.34×0.505×2 = 1.32 + 0.34 = 1.66
EV_J con bug  = (1−0.34)×2 + 0.34×0.000×2 = 1.32 + 0.00 = 1.32
                                               diferencia: −0.34 pts (−20%)
```

Impacto en EV_J para juego=34 (W=2, P_RL≈0.41):
```
EV_J correcto = (1−0.41)×2 + 0.41×0.058×2 = 1.18 + 0.05 = 1.23
EV_J con bug  = (1−0.41)×2 + 0.41×0.437×2 = 1.18 + 0.36 = 1.54
                                               diferencia: +0.31 pts (+25%)
```

---

## 3. Cómo Propaga a las Políticas de Descarte (Fase 2)

### Mecanismo

`generar_politicas_rollout.py` llama a `motor.decidir(mano, pos)` por cada jugador antes de iniciar un universo de simulación. Si cualquier jugador decide CORTAR, ese universo completo se descarta. Solo los universos donde los 4 jugadores dan MUS alimentan la Q-table.

Con el bug, el EV_J distorsionado alteraba las tasas de corte por tipo de mano:

| Tipo de mano rival | EV_J sesgado | Corta | Efecto en la muestra de entrenamiento |
|--------------------|-------------|-------|---------------------------------------|
| Juego = 40 (15 manos) | −20% (subestimado) | Menos de lo correcto | **Más** universos con rivales juego=40 |
| Juego = 37 (10 manos) | −16% (subestimado) | Menos | Más universos con rivales juego=37 |
| Juego = 34 (16 manos) | +25% (sobreestimado) | Más de lo correcto | **Menos** universos con rivales juego=34 |
| Juego = 33 (6 manos) | +40% (sobreestimado) | Más | Menos universos con rivales juego=33 |
| Juego = 31, 32 | Sin sesgo | Normal | Sin efecto |

**Resultado neto:** la muestra de entrenamiento contenía artificialmente más partidas contra rivales con juegos de rango alto (40, 37) y menos contra juegos débiles (33, 34).

### Dirección del sesgo en las políticas

1. **Rewards absolutos de descarte orientado a juego están conservadoramente subestimados.** El rollout competía contra un campo ligeramente más duro de lo real.

2. **La dirección del óptimo por mano probablemente se preserva.** El ranking relativo entre máscaras de la misma mano depende de la diferencia de rewards entre ellas, que es más robusta al nivel absoluto.

3. **El alcance es limitado:** Juego es 1 de 5 lances. El bias Opera solo en el 20% de manos (67 de 330, excluyendo 31 y 32 que son correctos). El efecto en la decisión de corte es acotado por el carácter estocástico del motor (sigmoide con ruido gaussiano).

4. **Manos más afectadas:** aquellas en el rango juego=33–40 donde la distorsión de EV_J supera ~0.3 pts (manos con juego=34, 37 y 40 principalmente).

---

## 4. Estado Actual de los Ficheros

| Fichero | Estado |
|---------|--------|
| `motor_decision.py` | ✅ Corregido — `_calcular_probabilidades_juego` usa `convertir_valor_juego` |
| `evaluador_ronda.py` | ✅ Corregido — `evaluar_juego` usa rangos jerárquicos |
| `calculadoramus.py` | ✅ Corregido — As = 1 punto en juego |
| `sanity_check_ev_8reyes.csv` | ✅ Regenerado — ranking de EV correcto |
| `politicas_optimas_fase2.csv` | ⚠️ Generado con bug — válido cualitativamente |
| `probabilidades_fase2.csv` | ⚠️ Generado con bug — válido cualitativamente |

---

## 5. Cómo Regenerar Correctamente

Todos los ficheros de código están ya corregidos. Basta con re-ejecutar el pipeline:

```powershell
# Desde la raíz del proyecto
cd calculadora_probabilidades_mus

# Lanzar en background ~12h (Windows)
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = "..\logs\generacion_$ts.log"
$proc = Start-Process python `
  -ArgumentList "-u","generar_politicas_rollout.py" `
  -WorkingDirectory (Get-Location) `
  -RedirectStandardOutput $log `
  -RedirectStandardError ($log -replace '\.log$','_err.log') `
  -WindowStyle Normal -PassThru
Write-Host "PID: $($proc.Id) | Log: $log"

# Monitorizar
Get-Content $log -Tail 10

# Tras completarse, regenerar análisis derivados
python interpretar_politicas.py
python analizar_comparativo.py
python sanity_check_ev.py
python probabilidades_segundas.py
```

### Estadísticas esperadas post-corrección

| Métrica | Actual (con sesgo) | Esperado (sin sesgo) |
|---------|-------------------|----------------------|
| Filas politicas_optimas_fase2.csv | 19.800 | 19.800 |
| Reward medio manos juego=40 | Ligeramente bajo | +0.2 a +0.5 pts |
| Reward medio manos juego=34 | Ligeramente alto | −0.2 a −0.4 pts |
| Ranking relativo máscaras por mano | Probablemente correcto | Confirmado |
