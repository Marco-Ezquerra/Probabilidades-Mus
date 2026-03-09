# Changelog v2.6 — Marzo 2026

## Resumen

Versión 2.6 añade correcciones de desempate por posición para los cuatro lances (Grande, Chica, Pares, Juego/Punto), completa la simulación de probabilidades condicionadas a segundas dadas con información de posición, y hace operativa la Pestaña 2 de la app.

---

## Cambios

### `calculadora_probabilidades_mus/motor_decision.py`

#### Nuevos atributos en `EstadisticasEstaticas`

- `probs_empate_gc`: `dict {mano_tuple: float}` — P(empate exacto grande/chica vs. 1 rival) calculada combinatoriamente sobre las 36 cartas restantes.
- `probs_punto`: `dict {mano_tuple: {'prob_menor', 'prob_empate'}}` — distribución de punto para las 226 manos sin juego.

#### Nuevos métodos privados

- `_calcular_probs_empate_gc()`: calcula `probs_empate_gc` usando `math.comb` sobre la composición real de las 36 cartas no usadas. Llamado al final de `_cargar()`.
- `_calcular_probabilidades_punto()`: llena `probs_punto` para las 226 manos sin juego. Llamado al final de `_cargar()`.

#### Nuevos métodos públicos

```python
def obtener_prob_empate_gc(self, mano) -> float
def obtener_prob_punto(self, mano) -> dict   # {'prob_menor', 'prob_empate'}

def prob_victoria_pares(self, mano, posicion, P_RL) -> float
    # (1 - P_RL) + P_RL * (prob_menor + prob_empate * factor_des)
    # Retorna 0.0 si la mano no tiene pares

def prob_victoria_juego_punto(self, mano, posicion, P_RL) -> float
    # Con juego:  (1 - P_RL) + P_RL * (prob_menor_j + prob_empate_j * factor_des)
    # Sin juego:  (1 - P_RL) * (prob_menor_p + prob_empate_p * factor_des)
```

Donde `factor_des = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}[posicion]`.

#### `calcular_ev_total()` — corregido

Las probabilidades de Grande y Chica ahora se ajustan por posición antes de calcular el EV:

```python
_factor_des_gc = {1: 1.0, 2: 0.5, 3: 0.5, 4: 0.0}.get(posicion, 0.5)
_p_empate_gc   = estadisticas.obtener_prob_empate_gc(mano)
_prob_grande_adj = max(0.0, prob_mano['prob_grande'] - 2 * _p_empate_gc * (1 - _factor_des_gc))
_prob_chica_adj  = max(0.0, prob_mano['prob_chica']  - 2 * _p_empate_gc * (1 - _factor_des_gc))
```

#### Validación de resultados

| Lance | Mano | Pos 1 (Mano) | Pos 4 (Postre) |
|---|---|:---:|:---:|
| Juego 31 | [Rey, Rey, Rey, As] | 100.0% | 90.3% |
| Medias (pares) | [Rey, Rey, Rey, As] | 89.2% | 87.3% |
| Punto | [4, 5, 6, 7] | 19.8% | 15.6% |

---

### `demos/app.py`

- Nueva función cacheada `_load_estadisticas()` que instancia `EstadisticasEstaticas(modo_8_reyes=True)` una sola vez.
- **Pestaña 1**: las cuatro métricas de probabilidad (Grande, Chica, Pares, Juego/Punto) ahora reflejan la posición seleccionada en el sidebar. P(Pares) muestra `—` si la mano no tiene pares.
- **Pestaña 2**: operativa — muestra la política de descarte óptima de la Q-table para la mano y posición seleccionadas.
- Caption actualizado: *"Todas las probabilidades ajustadas por posición (desempates: Mano gana, Postre pierde)."*

---

### `calculadora_probabilidades_mus/probabilidades_segundas.py`

- **Fix**: reemplazados caracteres Unicode (`∈`, `×`) por equivalentes ASCII para compatibilidad con cp1252 en Windows (evita `UnicodeEncodeError` al redirigir stdout).
- Añadida columna `posicion_focal` a la salida: la simulación ahora genera 4 posiciones separadas por mano y configuración → **84.480 filas** (330 × 4 × 64) en lugar de 330 × 64 = 21.120.

---

### Nuevos ficheros de datos

| Fichero | Filas | Columnas | Descripción |
|---|:---:|:---:|---|
| `probabilidades_segundas.csv` | 84.480 | 10 | P(victoria) por mano × posición × config de descarte rival |
| `resumen_segundas.csv` | 256 | 9 | Resumen promediado por posición × config |

**Estadísticas clave (`resumen_segundas.csv`):**

| Posición | P(pares) media | P(juego) media |
|:---:|:---:|:---:|
| 1 (Mano) | 59.7% | 53.5% |
| 4 (Postre) | 58.2% | 50.5% |

---

## Versión anterior

Ver [CHANGELOG_v2.5.md](CHANGELOG_v2.5.md) para los cambios de la versión 2.5.
