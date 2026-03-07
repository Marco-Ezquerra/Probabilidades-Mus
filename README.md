# 🎴 Sistema de Análisis de Mus - Motor IA y Simulador

Sistema completo de análisis probabilístico y toma de decisiones para el juego del **Mus**, implementado con **simulación Monte Carlo**, análisis dinámico condicionado y motor de decisión basado en **Valor Esperado (EV)** con fundamentos matemáticos rigurosos.

> **Versión**: v2.5 (Marzo 2026)  
> **Estado**: Fase 1 completa ✅ | Fase 2 regenerando con reglas corregidas 🔄  
> **Autor**: Marco Ezquerra  
> **Lances**: Grande, Chica, Pares, Juego y Punto

---

## 🎯 Características Principales

- ✅ **Simulación Monte Carlo** con 50,000-100,000 iteraciones por mano
- ✅ **Motor de decisión IA** basado en Valor Esperado (EV) matemático
- ✅ **Desempates exactos** por posición en la mesa (1 > 2 > 3 > 4)
- ✅ **Lance de Punto** implementado (cuando nadie tiene juego)
- ✅ **Política estocástica** (sigmoide) para evitar ser explotable
- ✅ **3 perfiles de juego**: Conservador, Normal, Agresivo
- ✅ **Fase 2 preparada**: Sistema de Q-Learning para políticas de descarte
- 🆕 **Tracking de descartes**: Información bayesiana para simulaciones avanzadas

---

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Marco-Ezquerra/Probabilidades-Mus
cd Probabilidades-Mus

# Instalar dependencias
pip install -r requirements.txt
```

### Demo Interactiva (Recomendado)

```bash
python3 demos/demo_interactiva.py
```

### Ejecutar Tests

```bash
# Tests del motor de decisión
python3 tests/test_motor_decision.py

# Tests de evaluación de ronda
python3 tests/test_evaluador_ronda.py

# Tests de descarte heurístico
python3 tests/test_descarte_heuristico.py

# Tests de tracking de descartes
python3 tests/test_tracking_descartes.py
```

---

## 📂 Estructura del Proyecto

```
Probabilidades-Mus/
├── 📁 calculadora_probabilidades_mus/   # Módulo principal
│   ├── calculadoramus.py                # Simulación Monte Carlo (Fase 1)
│   ├── motor_decision.py                # Motor IA de decisión (CORTAR/MUS)
│   ├── simular_dinamico.py              # Simulación condicionada
│   ├── evaluador_ronda.py               # Evaluación de lances y puntuación
│   ├── generar_politicas_rollout.py     # Q-Learning para descartes (Fase 2)
│   ├── simulador_fase2.py               # Simulador con políticas óptimas
│   ├── params.py                        # Configuración centralizada
│   ├── sanity_check_ev.py               # Verificación de coherencia
│   │
│   ├── resultados_8reyes.csv            # Dataset: 331 manos únicas (8 reyes)
│   ├── resultados_4reyes.csv            # Dataset: 716 manos únicas (4 reyes)
│   ├── calibracion_mu.json              # Caché: umbrales calibrados
│   ├── politicas_optimas_fase2.csv      # Políticas de descarte (generadas)
│   ├── probabilidades_fase2.csv         # Probabilidades post-descarte
│   │
│   └── README.md                        # Documentación del módulo
│
├── 📁 docs/                             # Documentación técnica
│   ├── CHANGELOG_v2.4.md                # Historial de cambios v2.4
│   ├── CHANGELOG_v2.3.md                # Historial de cambios v2.3
│   ├── FUNDAMENTOS_MATEMATICOS.md       # Formulación matemática completa
│   ├── README_FASE2.md                  # Guía de la Fase 2 (Q-Learning)
│   ├── DESEMPATES_MATEMATICOS.md        # Explicación de desempates
│   ├── ESTIMACION_N_MUESTRAL.md         # Cálculo de iteraciones necesarias
│   ├── SANITY_CHECK_README.md           # Guía de verificación
│   ├── TABLA_MAESTRA_EV.md              # Ranking completo de manos
│   └── interpretacion_politicas.txt     # Análisis de políticas generadas
│
├── 📁 tests/                            # Suite de tests
│   ├── test_motor_decision.py           # Tests del motor de decisión
│   ├── test_evaluador_ronda.py          # Tests de evaluación de lances
│   ├── test_descarte_heuristico.py      # Tests de heurística de descartes
│   ├── test_tracking_descartes.py       # Tests de tracking de descartes
│   ├── test_baraja.py                   # Tests de baraja y combinaciones
│   ├── test_mascaras.py                 # Tests de máscaras de descarte
│   └── test_simulador_dinamico.py       # Tests de simulación dinámica
│
├── 📁 demos/                            # Scripts de demostración
│   ├── demo_interactiva.py              # Demo interactiva completa
│   ├── demo_fase2.py                    # Demo de Fase 2 (descartes)
│   ├── diagnostico_mus.py               # Diagnóstico del sistema
│   └── validar_proyecto.py              # Validador completo
│
├── 📁 utils/                            # Utilidades
│   ├── mascaras_descarte.py             # Gestión de máscaras de descarte
│   ├── descarte_heuristico.py           # Heurística baseline de descartes
│   └── ordenartabla.py                  # Análisis y ordenamiento de CSVs
│
├── 📁 logs/                             # Logs de ejecución (generados)
│   ├── generacion_politicas.log         # Logs de generación de políticas
│   └── simulacion_fase2.log             # Logs de simulaciones
│
├── README.md                            # Este archivo
├── requirements.txt                     # Dependencias del proyecto
└── .gitignore                           # Archivos ignorados por Git
```

---

## 🎮 Componentes del Sistema

### 1️⃣ Fase 1: Motor de Decisión (Primeras Dadas)

**Objetivo:** Decidir si **CORTAR** o dar **MUS** en las primeras dadas basándose en el Valor Esperado (EV) matemático de la mano.

**Archivos principales:**
- `calculadoramus.py`: Generación de probabilidades base (Monte Carlo)
- `motor_decision.py`: Motor de decisión IA (EV + política estocástica)

**Uso:**
```python
from motor_decision import MotorDecisionMus

motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
mano = [12, 12, 10, 10]  # Duples Rey-Sota

decision, probabilidad, ev, desglose = motor.decidir(mano, posicion=1)

print(f"Decisión: {'CORTAR' if decision else 'MUS'}")
print(f"Probabilidad de cortar: {probabilidad:.1%}")
print(f"EV total: {ev:.2f} puntos")
```

**Fundamentos matemáticos:**
```
EV_Total = EV_Grande + EV_Chica + EV_Pares + EV_Juego + EV_Punto

EV_Lance = P(yo gano) × W_lance × (1 + factor_posición)

P(Cortar) = sigmoid(K × (EV - μ))
  donde:
    K ~ N(k_base, σ²) = Componente estocástico
    μ = Umbral calibrado por perfil
```

**Perfiles disponibles:**
- **Conservador**: β=0.65, μ=percentil 80 → Corta solo con EVs altos
- **Normal**: β=0.75, μ=percentil 74 → Equilibrado
- **Agresivo**: β=0.85, μ=percentil 65 → Toma más riesgos

---

### 2️⃣ Fase 2: Políticas de Descarte (Q-Learning)

**Objetivo:** Determinar la estrategia óptima de descarte mediante simulaciones de rollout (partida completa) y medición de puntos reales obtenidos.

**Archivos principales:**
- `generar_politicas_rollout.py`: Generación de políticas mediante Q-Learning
- `simulador_fase2.py`: Simulador con políticas óptimas
- `evaluador_ronda.py`: Evaluación de 4 lances + puntuación real

**Sistema de puntuación:**
- **Grande/Chica**: 1 punto fijo para el equipo ganador
- **Pares**: Suma de valores base de AMBOS miembros del equipo ganador
  - Sin pares: 0, Pares: 1, Medias: 2, Duples: 3
- **Juego**: Suma de valores base de AMBOS miembros del equipo ganador
  - La 31: 3 puntos, Resto de juegos: 2 puntos
- **Punto**: 1 punto (cuando nadie tiene juego)

**Tracking de descartes (v2.4):**
- Captura cuántas cartas descarta cada jugador en cada ronda
- Información almacenada en CSV de políticas: `n_descarte_j1`, `n_descarte_j2`, etc.
- Habilita actualizaciones bayesianas para simulaciones de segundas dadas

**Para ejecutar (ver GUIA_EJECUCION.md):**
```bash
cd calculadora_probabilidades_mus
python3 generar_politicas_rollout.py
```

---

### 3️⃣ Sistema de Evaluación de Rondas

**Archivo:** `evaluador_ronda.py`

Evalúa una ronda completa con los 4 lances y calcula puntos reales por equipo según las reglas oficiales del Mus.

**Características:**
- Desempates estrictos por posición (1 > 2 > 3 > 4)
- Puntuación por equipos (A: posiciones 1+3, B: posiciones 2+4)
- Suma de puntos base de AMBOS miembros del equipo ganador
- Lance de Punto implementado (cuando nadie tiene juego)

---

## 📊 Datasets Generados

### `resultados_8reyes.csv` (331 manos únicas)
Estadísticas precomputadas para el modo de 8 reyes (más jugado).

### `politicas_optimas_fase2.csv` (generado en Fase 2)
Políticas óptimas de descarte para cada (mano, posición, máscara).

**Estructura:**
```csv
mano,posicion,mascara_idx,reward_promedio,n_visitas,n_descarte_j1,n_descarte_j2,n_descarte_j3,n_descarte_j4
[4,6,11,12],1,0,-2.34,1582,1.2,2.8,3.1,1.5
```

---

## 🔬 Verificación y Tests

### Suite de Tests Completa

```bash
# Test 1: Motor de desempates (7 tests)
python3 tests/test_motor_decision.py

# Test 2: Evaluador de ronda (6 tests)
python3 tests/test_evaluador_ronda.py

# Test 3: Descarte heurístico (7 tests)
python3 tests/test_descarte_heuristico.py

# Test 4: Tracking de descartes (integración)
python3 tests/test_tracking_descartes.py
```

### Sanity Check (Coherencia Matemática)

```bash
cd calculadora_probabilidades_mus
python3 sanity_check_ev.py
```

Verifica:
- EVs de todas las 331 manos en 4 posiciones
- Coherencia entre posiciones
- Ranking de manos por EV
- Impacto de desempates

---

## 📈 Novedades v2.5 (Marzo 2026)

### 🐛 Corrección Crítica: Valor del As en Juego

**Bug corregido:** `calcular_valor_juego` contabilizaba el As como **11 puntos** cuando la regla oficial del Mus establece que el As vale **1 punto** en el lance de Juego.

**Impacto:** 110 de 120 manos con ases tenían clasificación de juego incorrecta. Por ejemplo, `[1,1,1,1]` (suma=4) y `[1,1,1,10]` (suma=13) se clasificaban erróneamente como juego.

**Archivo corregido:** `calculadora_probabilidades_mus/calculadoramus.py` — función `calcular_valor_juego`.

```python
# ANTES (incorrecto)
def valor_carta_juego(carta):
    if carta == 1: return 11   # As = 11 ← ERROR
    if carta >= 10: return 10
    return carta

# DESPUÉS (correcto)
def valor_carta_juego(carta):
    if carta >= 10: return 10  # Sota/Caballo/Rey = 10
    return carta               # As = 1, resto = valor nominal
```

### 🐛 Corrección Crítica: Jerarquía de Juego por Rango

**Bug corregido:** `evaluar_juego` comparaba los juegos por su **valor numérico bruto** (40 > 37 > ... > 31) cuando la jerarquía real es **31 > 32 > 40 > 37 > 36 > 35 > 34 > 33** (la 31 gana a todas).

**Impacto:** Cualquier enfrentamiento entre 31 y otro juego (32, 40…) daba ganador incorrecto.

**Archivo corregido:** `calculadora_probabilidades_mus/evaluador_ronda.py` — función `evaluar_juego` ahora usa `convertir_valor_juego` para comparar por rango.

**Consecuencia:** Todos los CSV generados anteriormente (políticas, probabilidades, análisis) han sido regenerados con las reglas correctas.

---

## 📈 Novedades v2.4 (Marzo 2026)

### 🎯 Simplificación de Valores Beta

**Antes:** Escala continua (31=3.0, 32=2.857, 40=2.714, ..., 33=2.0)  
**Ahora:** Sistema binario (31=3.0, resto=2.0)

**Justificación:** En el Mus real, la 31 vale 3 puntos y el resto de juegos valen 2 puntos uniformemente. Las jerarquías se resuelven por comparación directa.

### ❌ Eliminación de EV Soporte Condicionado

**Removido:** Término `f_red × P(comp_gana) × 0.6`

**Justificación:** Este factor se aplica simétricamente tanto al compañero como a los rivales del equipo contrario, cancelándose en el cálculo diferencial. No aporta información útil para la decisión.

### 📊 Sistema de Tracking de Descartes

**Nuevo:** Captura información sobre cuántas cartas descarta cada jugador.

**Beneficios:**
- Permite actualización bayesiana de probabilidades en segundas dadas
- Habilita detección de patrones de juego subóptimos
- Información almacenada en CSV de políticas para uso futuro

**Ver detalles completos:** [docs/CHANGELOG_v2.4.md](docs/CHANGELOG_v2.4.md)

---

## 📚 Documentación Adicional

- **[docs/FUNDAMENTOS_MATEMATICOS.md](docs/FUNDAMENTOS_MATEMATICOS.md)**: Formulación matemática completa del sistema
- **[docs/README_FASE2.md](docs/README_FASE2.md)**: Guía detallada de la Fase 2 (Q-Learning)
- **[docs/CHANGELOG_v2.5.md](docs/CHANGELOG_v2.5.md)**: Correcciones críticas v2.5 (as=1, jerarquía juego)
- **[docs/CHANGELOG_v2.4.md](docs/CHANGELOG_v2.4.md)**: Historial completo de cambios v2.4
- **[docs/DESEMPATES_MATEMATICOS.md](docs/DESEMPATES_MATEMATICOS.md)**: Explicación de desempates por posición
- **[docs/TABLA_MAESTRA_EV.md](docs/TABLA_MAESTRA_EV.md)**: Ranking completo de 331 manos por EV

---

## 🛠️ Requisitos del Sistema

### Software
- Python 3.8+
- Librerías: `numpy`, `pandas`, `tqdm`

### Hardware (para Fase 2: Generación de Políticas)
- **CPU**: Recomendado multi-core (8+ cores)
- **RAM**: Mínimo 8 GB, recomendado 16 GB
- **Almacenamiento**: ~500 MB para datasets y políticas
- **Tiempo estimado**: 8-12 horas con 40M iteraciones

---

## 👤 Autor y Contacto

**Marco Ezquerra**  
**Repositorio**: [GitHub.com/Marco-Ezquerra/Probabilidades-Mus](https://github.com/Marco-Ezquerra/Probabilidades-Mus)  
**Versión actual**: v2.5 (Marzo 2026)

---

## 📄 Licencia

Este proyecto es de código abierto. Consulta el archivo LICENSE para más detalles.

---

## 🎉 Próximos Pasos

### Para ejecutar la Fase 2 (Generación de Políticas):

1. ✅ Estructura organizada
2. ✅ Tests pasados (20/20)
3. ✅ Documentación actualizada
4. 🚀 **Listo para ejecutar:** Ver [GUIA_EJECUCION.md](GUIA_EJECUCION.md)

```bash
cd calculadora_probabilidades_mus
python3 generar_politicas_rollout.py
```

**Configuración actual:**
- `N_ITERACIONES_ROLLOUT = 40_000_000` (40M iteraciones)
- `MODO_8_REYES = True`
- Multiprocessing activado (usa todos los cores disponibles)

**Ver recomendaciones de ejecución:** [GUIA_EJECUCION.md](GUIA_EJECUCION.md)

> **Estado actual (v2.5):** La Fase 2 está en ejecución con el código corregido (as=1, jerarquía de juego por rango). Los resultados estarán disponibles en ~12 horas.
