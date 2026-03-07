# CHANGELOG v2.5 - Marzo 2026

## 🎯 Resumen de Cambios

Esta versión v2.5 corrige **dos bugs críticos** en la lógica del lance de Juego que afectaban a todas las manos con ases y a cualquier enfrentamiento en el que participara la 31. Todos los CSVs generados (políticas, probabilidades, análisis) han sido regenerados con las reglas correctas.

---

## Cambios Principales

### 1. 🐛 Corrección Crítica: Valor del As en Juego

**Archivo:** `calculadora_probabilidades_mus/calculadoramus.py`  
**Función:** `calcular_valor_juego` → `valor_carta_juego`

**Problema:**
El As (carta 1) se contabilizaba como **11 puntos** en lugar de **1 punto**, lo que causaba que manos sin juego real se clasificaran incorrectamente como juego.

```python
# ANTES (incorrecto)
def valor_carta_juego(carta):
    if carta == 1: return 11   # ← BUG: As valía 11
    if carta >= 10: return 10
    return carta

# DESPUÉS (correcto, v2.5)
def valor_carta_juego(carta):
    if carta >= 10: return 10  # Sota(10)/Caballo(11)/Rey(12) = 10
    return carta               # As(1) = 1, resto = valor nominal
```

**Regla oficial del Mus:**
- As = 1 punto
- Sota / Caballo / Rey = 10 puntos cada uno
- 4, 5, 6, 7 = su valor nominal

**Impacto:**
- **110 de 120 manos con ases** tenían clasificación de juego incorrecta.
- Ejemplos de manos incorrectamente clasificadas como juego antes del fix:

| Mano | Suma antes (bug) | Suma ahora (correcto) | Clasificación correcta |
|------|------------------|-----------------------|------------------------|
| `[1,1,1,1]` | 44 (juego!) | 4 | NO juego |
| `[1,1,1,10]` | 43 (juego!) | 13 | NO juego |
| `[1,1,1,4]` | 37 (juego!) | 7 | NO juego |
| `[1,1,4,5]` | 31 (juego!) | 11 | NO juego |
| `[1,12,12,12]` | 43 → 31 (correcto) | 31 | JUEGO ✓ |
| `[10,10,10,1]` | 41 → 31 (correcto) | 31 | JUEGO ✓ |

---

### 2. 🐛 Corrección Crítica: Jerarquía de Juego por Rango

**Archivo:** `calculadora_probabilidades_mus/evaluador_ronda.py`  
**Función:** `evaluar_juego`

**Problema:**
El ganador de un enfrentamiento de juegos se determinaba comparando los **valores numéricos brutos** (40 > 37 > ... > 32 > 31), cuando la jerarquía real del Mus es:

```
31 > 32 > 40 > 37 > 36 > 35 > 34 > 33
```

La 31 es el **mejor juego** (gana a todos los demás), pero numéricamente 31 < 32 < 40, por lo que la comparación directa daba ganadores incorrectos en cualquier enfrentamiento que involucara la 31.

**Solución:**
Se usa `convertir_valor_juego` para obtener el rango de cada juego y comparar por rango descendente:

```python
# Tabla de rangos (convertir_valor_juego)
RANGOS = {31: 8, 32: 7, 40: 6, 37: 5, 36: 4, 35: 3, 34: 2, 33: 1}
# Rango mayor = mejor juego
```

```python
# ANTES (incorrecto)
if valor_actual > mejor_valor:   # comparación por valor bruto
    ganador = pos

# DESPUÉS (correcto, v2.5)
rank = convertir_valor_juego(raw)
if ganador is None:
    ganador = pos; mejor_raw = raw; mejor_rank = rank
else:
    resultado = comparar_juego(mejor_rank, rank, es_mano=True)
    if resultado == -1:
        ganador = pos; mejor_raw = raw; mejor_rank = rank
```

**Impacto:**
- Todos los enfrentamientos `31 vs 32`, `31 vs 40`, `32 vs 40`, etc. ahora devuelven el ganador correcto.
- Afecta a cualquier ronda en la que se presente la 31 contra otro juego.

---

### 3. ✅ Tests Verificados

Tras las correcciones, se verificó el correcto funcionamiento con los tests unitarios existentes:

```
[1,1,1,1]    → raw=0,  rank=0  NO-juego  ✓
[1,1,1,10]   → raw=0,  rank=0  NO-juego  ✓  (antes era raw=43!)
[1,12,12,12] → raw=31, rank=8  JUEGO     ✓
[10,10,10,1] → raw=31, rank=8  JUEGO     ✓
J1=31 vs J2=32 → J1 gana (rango 8 > 7)  ✓
J1=32 vs J2=40 → J1 gana (rango 7 > 6)  ✓
J1=40 vs J2=31 → J2 gana (rango 8 > 6)  ✓
```

Todos los tests pasaron: `test_evaluador_ronda.py` ✅

---

### 4. 🔄 Regeneración Completa del Pipeline

Como consecuencia de los dos bugs corregidos, todos los archivos generados previamente han sido invalidados y se ha relanzado el pipeline completo:

**Archivos regenerados:**
- `calculadora_probabilidades_mus/politicas_optimas_fase2.csv`
- `calculadora_probabilidades_mus/probabilidades_fase2.csv`
- `calculadora_probabilidades_mus/politicas_legibles.csv`
- `calculadora_probabilidades_mus/interpretacion_politicas.txt`
- `calculadora_probabilidades_mus/analisis_fase1_vs_fase2.csv`
- `calculadora_probabilidades_mus/sanity_check_ev_8reyes.csv`

**Comando de regeneración (Windows):**
```powershell
$logFile = "logs\generacion_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Start-Process python -ArgumentList "-u", "generar_politicas_rollout.py" `
  -WorkingDirectory "calculadora_probabilidades_mus" `
  -RedirectStandardOutput $logFile -WindowStyle Normal -PassThru
```

---

## Archivos Modificados

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `calculadora_probabilidades_mus/calculadoramus.py` | Fix | As=1 en `valor_carta_juego` |
| `calculadora_probabilidades_mus/evaluador_ronda.py` | Fix | Jerarquía por rango en `evaluar_juego` |
| `docs/FUNDAMENTOS_MATEMATICOS.md` | Docs | Versión 2.5, nota as=1 y rango |
| `README.md` | Docs | Versión v2.5, sección Novedades v2.5 |
