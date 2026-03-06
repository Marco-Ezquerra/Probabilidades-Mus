# 🎴 Sistema de Análisis de Mus - Fase 1 COMPLETA ✅

Sistema completo de análisis probabilístico y toma de decisiones para el juego del **Mus**, implementado con **simulación Monte Carlo**, análisis dinámico condicionado y motor de decisión basado en **Valor Esperado (EV)** con fundamentos matemáticos rigurosos.

> **Estado**: Fase 1 cerrada (febrero 2026)  
> **Versión**: v2.3  
> **Lances**: Grande, Chica, Pares, Juego y Punto

---

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Demo interactiva (recomendado para empezar)
python3 demo_interactiva.py

# 3. Tests de validación
python3 test_baraja.py
python3 test_motor_decision.py
python3 test_simulador_dinamico.py
```

---

## 📂 Estructura del Proyecto

```
Probabilidades-Mus/
├── calculadora_probabilidades_mus/    # 📦 Módulo principal
│   ├── calculadoramus.py              # Monte Carlo: estadísticas precalculadas
│   ├── simular_dinamico.py            # Simulación condicionada (con compañero)
│   ├── motor_decision.py              # Motor IA de decisión (CORTAR/MUS)
│   ├── resultados_4reyes.csv          # Dataset: estadísticas modo tradicional
│   ├── resultados_8reyes.csv          # Dataset: estadísticas modo 8 reyes
│   ├── calibracion_mu.json            # Caché: umbrales calibrados por perfil
│   │
│   ├── README.md                      # 📖 Doc: guía del módulo
│   ├── FUNDAMENTOS_MATEMATICOS.md     # 📐 Doc: formulación matemática
│   ├── CHANGELOG_v2.3.md              # 📝 Doc: historial de cambios
│   └── SANITY_CHECK_README.md         # 🔍 Doc: verificación de coherencia
│
├── demo_interactiva.py                # 🎮 Demo: interfaz interactiva completa
├── test_*.py                          # ✅ Tests unitarios
├── validar_proyecto.py                # 🔍 Validador del sistema completo
└── utils/                             # 🛠️ Scripts auxiliares
    └── ordenartabla.py                # Análisis y ordenamiento de CSVs
```

---

## 🎯 Componentes del Sistema

### 1️⃣ Probabilidades Estáticas (Monte Carlo)

**Archivo:** `calculadoramus.py`

Simula **50,000-100,000 partidas** por cada mano inicial única, enfrentándola contra dos manos aleatorias. Genera tablas precalculadas con probabilidades a priori para cada lance.

```bash
cd calculadora_probabilidades_mus
python3 calculadoramus.py
```

**Salida:**
- `resultados_4reyes.csv`: 716 manos únicas en modo tradicional
- `resultados_8reyes.csv`: 331 manos únicas en modo 8 reyes

**Columnas del CSV:**
- `probabilidad_grande`: P(ganar Grande) [0,1]
- `probabilidad_chica`: P(ganar Chica) [0,1]
- `probabilidad_pares`: P(ganar Pares) [0,1]
- `probabilidad_juego`: P(ganar Juego/Punto) [0,1]

---

### 2️⃣ Simulación Dinámica (Condicionada)

**Archivo:** `simular_dinamico.py`

Calcula probabilidades **condicionadas** cuando conoces las 8 cartas de tu pareja (tú + compañero). Son probabilidades *a posteriori* que incorporan información adicional.

**Uso:**
```python
from simular_dinamico import simular_con_companero
from calculadoramus import inicializar_baraja

baraja = inicializar_baraja(modo_8_reyes=True)
tu_mano = [12, 12, 11, 10]
mano_companero = [1, 1, 1, 1]

resultado = simular_con_companero(tu_mano, mano_companero, baraja, iteraciones=50000)
# Retorna: {'probabilidad_grande', 'probabilidad_chica', 'probabilidad_pares', 'probabilidad_juego'}
```

**Diferencia clave:**
- **Estáticas**: P(ganar | mi mano) - No sé qué tiene el compañero
- **Dinámicas**: P(ganar | mi mano, mano compañero) - Sé qué tiene el compañero

---

### 3️⃣ Motor de Decisión IA

**Archivo:** `motor_decision.py`

Motor de IA que decide **CORTAR** o dar **MUS** en primeras dadas basándose en Valor Esperado (EV) y teoría de juegos.

#### 🧠 Fundamentos Matemáticos

**Modelo de Valor Esperado:**
```
EV_Total = EV_Propio + β · EV_Soporte

EV_Propio  = Σ (valor del lance considerando probabilidad de victoria)
EV_Soporte = Σ (valor esperado de la contribución del compañero)
β ∈ [0.65, 0.85] = Factor de confianza en el compañero
```

**Política de Decisión (Sigmoide):**
```
P(Cortar) = sigmoid(K · (EV - μ))

donde:
  K ~ N(k_base, σ²) = Componente estocástico (evita ser explotable)
  μ = Umbral calibrado por perfil (percentil de distribución de EVs)
```

#### 🎮 Tres Perfiles

| Perfil      | β (confianza) | μ (percentil) | Comportamiento           |
|-------------|---------------|---------------|--------------------------|
| Conservador | 0.65          | P55           | Corta solo con EVs altos |
| Normal      | 0.75          | P45           | Equilibrado              |
| Agresivo    | 0.85          | P30           | Toma más riesgos         |

#### 🔬 Mejoras Matemáticas v2.0

Implementadas en **26/02/2026** (ver [CHANGELOG_v2.3.md](calculadora_probabilidades_mus/CHANGELOG_v2.3.md)):

1. **Percentiles CDF para P(yo|RL)**: Usa ranking real en lugar de probabilidad general
2. **Factor Bayesiano**: Modelado del efecto de remoción de cartas
   - Peso de mano: 12=4pts, 11=2.5pts, 1=1.5pts, 10=1pts
   - Factor ∈ [0.7, 1.3]: Mano pesada reduce prob. compañero, ligera la aumenta
3. **Eliminación de descuentos artificiales**: EVs matemáticamente consistentes

**Uso:**
```python
from motor_decision import MotorDecisionMus

motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')
mano = [1, 1, 1, 10]

decision, prob_corte, ev, desglose = motor.decidir(mano)
# decision: bool (True=CORTAR, False=MUS)
# prob_corte: float [0,1] (Probabilidad de cortar)
# ev: float (Valor esperado total)
# desglose: dict (EV por lance y componentes)
```

---

## 🃏 Modos de Juego

### Modo 4 REYES (Tradicional)
- **Reyes**: 1 (×8) y 12 (×8)
- **Baraja**: 1, 4, 5, 6, 7, 10, 11, 12 (40 cartas)

### Modo 8 REYES
- **Reyes**: 1 (×8), 2 (×4), 3 (×4 vale 12), 12 (×8)
- **Baraja**: 1, 2, 4, 5, 6, 7, 10, 11, 12 (40 cartas)
- **Nota**: El 2 vale 2, el 3 vale 12

---

## 🧪 Tests y Validación

```bash
# Test individual de cada componente
python3 test_baraja.py              # Valida inicialización y reglas de baraja
python3 test_motor_decision.py      # Valida motor IA y cálculos de EV
python3 test_simulador_dinamico.py  # Valida simulaciones dinámicas

# Validación completa del sistema
python3 validar_proyecto.py
```

---

## 📊 Demo Interactiva

```bash
python3 demo_interactiva.py
```

**Opciones disponibles:**
1. **Análisis Estático**: Consulta probabilidades precalculadas
2. **Simulación Dinámica**: Simula con mano del compañero conocida
3. **Motor IA**: Decisión CORTAR/MUS con los 3 perfiles
4. **Análisis Detallado**: Razonamiento completo del motor (EV desglosado)
5. **Comparación Completa**: Compara los 3 sistemas sobre la misma mano

---

## 🛣️ Roadmap: Próximas Fases

### ✅ Fase 1: Primeras Dadas (COMPLETADO)
- ✅ Estadísticas Monte Carlo
- ✅ Simulador dinámico con compañero
- ✅ Motor de decisión IA con mejoras matemáticas v2.0
- ✅ Tres perfiles (conservador/normal/agresivo)

### 🚧 Fase 2: Segundas Dadas (EN DESARROLLO)
- [ ] **Estadísticas condicionadas a mus**: P(ganar | hubo mus, descarté X cartas)
- [ ] **Optimizador de descarte**: ¿Qué cartas descartar para maximizar EV?
- [ ] **Motor de decisión extendido**: Decisión CORTAR/MUS en segundas dadas
- [ ] **Análisis de información**: Inferencia bayesiana sobre manos rivales

**Implementación prevista:**
```python
# Nuevo módulo: segundas_dadas.py
def calcular_probabilidades_tras_mus(mano_original, cartas_descartadas, baraja):
    """
    Calcula P(ganar | hubo mus, descarté X cartas, recibí Y nuevas)
    Considera el efecto de remoción de cartas y distribución actualizada.
    """
    pass

def optimizar_descarte(mano, estadisticas, n_descartar):
    """
    Encuentra la combinación óptima de descarte para maximizar EV.
    Usa programación dinámica o búsqueda exhaustiva.
    """
    pass
```

### 🔮 Fase 3: Juego Completo (PLANIFICADO)
- [ ] Estrategia de envites (órdago, paso, quiero, no quiero)
- [ ] Faroles y detección de faroles
- [ ] Gestión de puntuación y riesgo

---

## 📚 Documentación

Toda la documentación está en el módulo `calculadora_probabilidades_mus/`:

- **[README.md](calculadora_probabilidades_mus/README.md)** - Guía completa del módulo
- **[FUNDAMENTOS_MATEMATICOS.md](calculadora_probabilidades_mus/FUNDAMENTOS_MATEMATICOS.md)** - Formulación matemática completa
- **[CHANGELOG_v2.3.md](calculadora_probabilidades_mus/CHANGELOG_v2.3.md)** - Historial de cambios y correcciones
- **[TABLA_MAESTRA_EV.md](calculadora_probabilidades_mus/TABLA_MAESTRA_EV.md)** - 📊 Ranking completo de manos por EV
- **[SANITY_CHECK_README.md](calculadora_probabilidades_mus/SANITY_CHECK_README.md)** - Verificación de coherencia
- **[DESEMPATES_MATEMATICOS.md](calculadora_probabilidades_mus/DESEMPATES_MATEMATICOS.md)** - Implementación de desempates

---

## 🔧 Requisitos Técnicos

- **Python**: 3.7 o superior
- **Dependencias**: 
  ```bash
  pip install pandas numpy
  ```

---

## 📈 Precisión Estadística

**Monte Carlo (Estadísticas estáticas):**
- Iteraciones: 50,000-100,000 por mano
- Error típico: ±0.15-0.30%
- Intervalo de confianza: 95%

**Simulación Dinámica:**
- Iteraciones recomendadas: 50,000
- Tiempo de ejecución: ~1-2 segundos
- Error típico: ±0.20-0.40%

**Motor de Decisión:**
- Calibración de μ: Basada en 700+ manos únicas
- Umbrales típicos: μ ∈ [2.7, 4.1]
- Ruido estocástico: σ ∈ [0.3, 0.4]

---

## 🤝 Contribuciones

Este proyecto implementa teoría de juegos, inferencia bayesiana y estadística computacional aplicada al Mus. Las contribuciones son bienvenidas, especialmente en:

- Optimización de algoritmos de descarte
- Mejoras en el modelado bayesiano
- Estrategias de envite y farol
- Interfaz gráfica

---

## 📝 Licencia

Proyecto educativo y de investigación sobre teoría de juegos aplicada.

---

## 🎓 Referencias Matemáticas

- **Teoría de Juegos**: Nash equilibrium, mixed strategies
- **Estadística Bayesiana**: Prior/posterior probabilities, card removal effect
- **Simulación Monte Carlo**: Law of large numbers, confidence intervals
- **Optimización**: Expected Value maximization, dynamic programming

---

*Última actualización: 26/02/2026*  
*Versión: 2.0 (Mejoras Matemáticas Implementadas)*
