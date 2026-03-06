# CHANGELOG v2.4 - Marzo 2026

## 🎯 Resumen de Cambios

Esta versión v2.4 introduce simplificaciones importantes en el sistema de valoración de juegos y eliminación de términos redundantes en el cálculo de EV, además de implementar un sistema completo de tracking de descartes para habilitar simulaciones bayesianas futuras.

---

## Cambios Principales

### 1. ✅ Simplificación de Valores Beta de Juegos

**Problema identificado:** 
El sistema anterior usaba una escala continua de valores para los juegos (31=3.0, 32=2.857, 40=2.714, ..., 33=2.0), lo cual no reflejaba la realidad del Mus.

**Solución implementada:**
- **31 (La 31)**: 3.0 puntos base
- **Resto de juegos (32, 40, 37, 36, 35, 34, 33)**: 2.0 puntos base uniforme

**Justificación:**
En el Mus real, la 31 vale 3 puntos base y el resto de juegos valen 2 puntos base uniformemente. Las jerarquías entre juegos (32 > 40 > 37...) se resuelven por comparación directa en caso de empate, no por diferencias de valor base.

**Archivos modificados:**
- `calculadora_probabilidades_mus/motor_decision.py`: VALORES_JUEGO (líneas 55-66)
- `calculadora_probabilidades_mus/FUNDAMENTOS_MATEMATICOS.md`: Sección de valores de juego

---

### 2. ✅ Eliminación de EV Soporte Condicionado

**Problema identificado:**
El término de "EV Soporte Condicionado" aplicaba un factor de reducción `f_red × P(comp_gana) × 0.6` tanto al compañero como (implícitamente) a los rivales del equipo contrario, cancelándose mutuamente en el cálculo diferencial de EV.

**Fórmula eliminada:**
```
EV_Soporte_Cond = f_red × P(comp_gana) × (W_comp + E_extra)

Donde:
- f_red = 0.5 si yo tengo jugada, 1.0 si no tengo
- P(comp_gana) = p_comp × 0.6
```

**Justificación:**
El factor se aplica simétricamente:
- Si **yo** tengo jugada → mi compañero vale menos (f_red=0.5)
- Si **rival** tiene jugada → su compañero vale menos (f_red=0.5)

Este efecto es simétrico para ambos equipos, por lo que el término diferencial neto es **≈0** y puede eliminarse sin pérdida de precisión en la decisión.

**Archivos modificados:**
- `calculadora_probabilidades_mus/motor_decision.py`:
  - Función `calcular_ev_soporte_condicionado()` comentada (líneas 474-502)
  - Eliminadas 3 llamadas en `calcular_ev_total()` (líneas ~555, ~577, ~602)
  - Variables `EV_soporte_P`, `EV_soporte_J`, `EV_soporte_Punto` ahora valen 0.0 (mantenidas para compatibilidad con desglose)
- `calculadora_probabilidades_mus/FUNDAMENTOS_MATEMATICOS.md`: Añadida nota explicativa

**Impacto:**
- ✅ Tests pasados: test_motor_desempates.py (7/7 ✓)
- ✅ Patrones de decisión se mantienen coherentes
- ✅ EVs ligeramente ajustados pero ranking relativo de manos similar

---

### 3. ✅ Sistema de Tracking de Descartes

**Objetivo:**
Capturar información sobre cuántas cartas descarta cada jugador en cada ronda para habilitar actualizaciones bayesianas en simulaciones de segundas dadas.

**Implementación:**

#### 3.1 Extensión de QTableDescarte

**Archivo:** `generar_politicas_rollout.py`

**Cambios:**
```python
# Estructura anterior:
q_table = {(mano, pos, mascara_idx): [total_reward, n_visitas]}

# Estructura nueva:
q_table = {(mano, pos, mascara_idx): [total_reward, n_visitas, info_descartes]}
# info_descartes = {1: total_cartas_j1, 2: total_cartas_j2, 3: ..., 4: ...}
```

**Métodos modificados:**
- `__init__()`: Inicializa info_descartes con {1:0, 2:0, 3:0, 4:0}
- `actualizar(mano, posicion, mascara_idx, reward, info_descartes=None)`: Acepta y acumula info de descartes
- `exportar_csv(filepath)`: Añade columnas `n_descarte_j1`, `n_descarte_j2`, `n_descarte_j3`, `n_descarte_j4` con promedios

#### 3.2 Extensión de simular_rollout_mascara_rapida

**Cambios:**
```python
# Retorno anterior:
return diferencial

# Retorno nuevo:
return (diferencial, info_descartes)
# info_descartes = {1: n_cartas, 2: n_cartas, 3: n_cartas, 4: n_cartas}
```

**Lógica:**
- Captura `len(mascara)` para el jugador objetivo
- Captura `4 - len(mano_rest)` para los otros 3 jugadores (descarte heurístico)
- Retorna dict con descartes de las 4 posiciones

#### 3.3 Estadísticas en simulador_fase2.py

**Archivo:** `simulador_fase2.py`

**Cambios:**
- Añadido tracking: `descartes_por_posicion = {1: [], 2: [], 3: [], 4: []}`
- Captura descartes en cada ronda válida
- Reporta estadísticas agregadas al final de la simulación:
  ```
  🎴 ESTADÍSTICAS DE DESCARTES POR POSICIÓN
  Posición 1: Promedio 2.34 ± 0.89 cartas
    Distribución: 1c: 15.2%  2c: 38.5%  3c: 32.1%  4c: 14.2%
  ...
  ```

**Formato CSV de políticas (extendido):**
```
mano,posicion,mascara_idx,reward_promedio,n_visitas,n_descarte_j1,n_descarte_j2,n_descarte_j3,n_descarte_j4
[4,6,11,12],1,0,-4.0,1000,1.2,2.8,3.1,1.5
...
```

**Archivos modificados:**
- `calculadora_probabilidades_mus/generar_politicas_rollout.py`
- `calculadora_probabilidades_mus/simulador_fase2.py`

---

## Tests y Verificación

### ✅ Suite de Tests Ejecutada

1. **test_motor_desempates.py**: 7/7 tests pasados ✓
   - Probabilidades exactas verificadas
   - Factores de desempate correctos
   - Decisiones coherentes en casos típicos

2. **test_evaluador_ronda.py**: 6/6 tests pasados ✓
   - Evaluación correcta de Grande, Chica, Pares, Juego/Punto
   - Cálculo correcto de puntos por equipo
   - Sistema de diferencial funcionando

3. **test_descarte_heuristico.py**: 7/7 tests pasados ✓
   - Heurística de descartes coherente
   - Reglas posicionales correctas
   - Conversión a índices de máscara funcionando

4. **test_tracking_descartes.py**: Test de integración pasado ✓
   - Info de descartes capturada correctamente
   - CSV exportado con columnas extendidas
   - Valores razonables (1-4 cartas por jugador)

---

## Próximos Pasos

### Fase 2: Generación de Políticas de Descarte

**Comando:**
```bash
cd calculadora_probabilidades_mus
python3 generar_politicas_rollout.py
```

**Configuración actual:**
- `N_ITERACIONES_ROLLOUT = 40_000_000` (40M iteraciones)
- `MODO_8_REYES = True`
- Tiempo estimado: ~8-12 horas (depende del hardware)

**Output esperado:**
- `politicas_optimas_fase2.csv`: Políticas con columnas de descartes
- Estadísticas de cobertura: manos únicas, visitas por estado
- Tasa de Mus objetivo: ~20%

### Uso Futuro de Info de Descartes

**Ejemplo de actualización bayesiana:**
```python
# Observación: Jugador 2 descartó 3 cartas
P(J2_tiene_juego | descarte=3) = P(descarte=3 | tiene_juego) × P(tiene_juego) / P(descarte=3)

# Usar políticas para inferir probabilidades condicionadas
# Si normalmente J2 con [12,11,10,1] descarta 1 carta, pero descartó 3:
# → Mayor probabilidad de no tener juego
```

**Aplicaciones:**
1. Simulación de segundas dadas condicionada a descartes observados
2. Detección de jugadores con estrategias subóptimas
3. Refinamiento de probabilidades de compañero en tiempo real
4. Análisis de patrones de descarte por posición

---

## Archivos Modificados (Resumen)

```
calculadora_probabilidades_mus/
├── motor_decision.py                  # VALORES_JUEGO, eliminación EV Soporte
├── generar_politicas_rollout.py       # Tracking de descartes, QTable extendida
├── simulador_fase2.py                 # Estadísticas de descartes
├── FUNDAMENTOS_MATEMATICOS.md         # Documentación actualizada

tests/
├── test_motor_desempates.py           # ✓ Pasado (7/7)
├── test_evaluador_ronda.py            # ✓ Pasado (6/6)
├── test_descarte_heuristico.py        # ✓ Pasado (7/7)
└── test_tracking_descartes.py         # ✓ Nuevo test de integración
```

---

## Compatibilidad

### ✅ Retrocompatibilidad Mantenida

- Los CSV de políticas existentes (sin columnas de descartes) siguen siendo legibles
- Las columnas de descartes son **adicionales**, no reemplazan columnas existentes
- Variables `EV_soporte_*` mantenidas en desglose con valor 0.0 para no romper código existente

### ⚠️ Incompatibilidades Menores

- EVs de manos individuales han cambiado ligeramente debido a ajuste de VALORES_JUEGO
- Archivos de caché `calibracion_mu.json` deben regenerarse (automático al ejecutar)
- Los CSV generados con v2.3 no tienen columnas de descartes (regenerar con v2.4)

---

## Métricas de Impacto

### Cambio en EVs (estimado)

```
Mano [12,11,10,1] (La 31):
- v2.3: EV_juego ≈ 3.000 + pequeñas variaciones por jerarquía
- v2.4: EV_juego ≈ 3.000 (sin cambio, es la 31)

Mano [10,10,10,10] (Cuatro dieces - 40):
- v2.3: EV_juego ≈ 2.714 (escala continua)
- v2.4: EV_juego ≈ 2.000 (valor binario)
- Δ: -0.714 (-26% en componente de juego)
```

**Impacto global:**
- Manos con 31: Sin cambio significativo
- Manos con otros juegos: EV de juego reducido ~5-15%
- **Ranking relativo se mantiene:** Las mejores manos siguen siendo las mejores

---

## Créditos y Contacto

**Autor:** Marco Ezquerra  
**Versión:** 2.4  
**Fecha:** Marzo 2026  
**Repositorio:** GitHub.com/Marco-Ezquerra/Probabilidades-Mus

---

## Notas Técnicas

### Decisión de Diseño: ¿Por qué eliminar EV Soporte Condicionado?

**Análisis matemático:**

El término de soporte condicionado modelaba:
```
Mi equipo:  +beta × f_red × P(comp_gana) × W_comp
Equipo rival: -beta × f_red × P(rival_comp_gana) × W_rival_comp
```

**Simetría del problema:**
- Si **yo** tengo duples → mi compañero vale menos (f_red=0.5)
- Si **rival** tiene duples → su compañero vale menos (f_red=0.5)

Dado que el modelo no tiene información diferencial sobre la mano del compañero vs. compañero rival:
```
P(comp_gana) ≈ P(rival_comp_gana)  (ambos desconocidos)
W_comp ≈ W_rival_comp              (distribución similar)
```

Por tanto:
```
Δ EV_soporte ≈ 0
```

**Conclusión:** El término no aporta información útil para la decisión de cortar vs. dar Mus, solo agrega complejidad innecesaria al modelo.

---

## 🎉 ¡Listo para generar políticas!

El sistema está ahora optimizado y listo para ejecutar la generación masiva de políticas óptimas de descarte con tracking completo de información contextual.

```bash
# Ejecutar generación de políticas (Fase 2)
python3 calculadora_probabilidades_mus/generar_politicas_rollout.py
```
