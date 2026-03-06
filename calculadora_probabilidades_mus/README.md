# Motor de Decisión Mus - Fase 1 y Fase 2

> **Versión**: 2.4 (marzo 2026)  
> **Estado**: Fase 1 completada y verificada ✅ | Fase 2 lista para ejecutar 🚀  
> **Lances modelados**: Grande, Chica, Pares, Juego y **Punto**

---

## 🎯 Descripción

Motor de decisión basado en Valor Esperado (EV) matemático para el juego del Mus. Implementa un agente IA que decide **"Cortar"** o dar **"Mus"** en las primeras dadas, utilizando:

- ✅ Probabilidades exactas precomputadas (Monte Carlo 10,000 iteraciones)
- ✅ Modelo de soporte del compañero (desconocido)
- ✅ Desempates exactos por posición en la mesa
- ✅ Jerarquía correcta del juego (31 > 32 > 40 > 37 > 36 > 35 > 34 > 33)
- ✅ Lance de Punto implementado (cuando nadie tiene juego)
- ✅ Política de decisión estocástica (sigmoide)

---

## 📦 Estructura del Proyecto

```
calculadora_probabilidades_mus/
├── calculadoramus.py           # Simulación Monte Carlo y cálculo de probabilidades
├── motor_decision.py            # Motor de decisión basado en EV
├── test_motor_desempates.py     # Suite de tests (7/7 ✓)
├── sanity_check_ev.py           # Verificación de coherencia matemática
│
├── resultados_8reyes.csv        # Probabilidades precomputadas (330 manos)
├── sanity_check_ev_8reyes.csv  # EVs de todas las manos en 4 posiciones
│
├── README.md                    # Este archivo
├── FUNDAMENTOS_MATEMATICOS.md   # Documentación matemática completa
├── CHANGELOG_v2.3.md            # Historial de cambios y correcciones
├── SANITY_CHECK_README.md       # Guía del sanity check
└── TABLA_MAESTRA_EV.md          # 📊 Ranking completo de manos por EV
```

---

## 🚀 Uso Rápido

### 1. Calcular Valor Esperado (EV) de una mano

```python
from motor_decision import MotorDecisionMus

# Inicializar motor
motor = MotorDecisionMus(modo_8_reyes=True, perfil='normal')

# Analizar una mano (posición 1)
mano = [12, 12, 10, 10]  # Duples Rey-Sota
decision, probabilidad, ev, desglose = motor.decidir(mano, posicion=1)

print(f"Decisión: {decision}")           # "CORTAR" o "MUS"
print(f"Probabilidad: {probabilidad:.1%}")  # % de cortar
print(f"EV total: {ev:.2f} puntos")      # Valor esperado

# Desglose detallado
print(f"EV Grande: {desglose['grande']['decision']:.2f}")
print(f"EV Chica:  {desglose['chica']['decision']:.2f}")
print(f"EV Pares:  {desglose['pares']['decision']:.2f}")
print(f"EV Juego:  {desglose['juego']['decision']:.2f}")
print(f"EV Punto:  {desglose['punto']['decision']:.2f}")
```

### 2. Generar estadísticas (si no existen)

```bash
# Calcular probabilidades para todas las 330 manos únicas
python3 calculadoramus.py

# Esto genera: resultados_8reyes.csv (tarda ~5-10 minutos)
```

### 3. Verificar coherencia del modelo

```bash
# Ejecutar sanity check completo
python3 sanity_check_ev.py

# Genera:
# - sanity_check_ev_8reyes.csv (EVs de todas las manos)
# - sanity_check_report_8reyes.txt (resumen de verificaciones)
```

---

## 📊 Resultados Clave

### Estadísticas Globales (330 manos únicas × 4 posiciones)

| Métrica | Posición 1 (Mano) | Posición 4 (Postre) |
|---------|-------------------|---------------------|
| **EV Medio** | 3.43 ± 1.49 | 3.34 ± 1.44 |
| **EV Máximo** | 7.17 | 7.03 |
| **EV Mínimo** | 2.05 | 2.05 |

### Top 5 Mejores Manos

| Mano | EV (pos1) | Composición |
|------|-----------|-------------|
| [6,6,12,12] | 7.17 | Duples + Juego 32 |
| [12,12,12,12] | 6.71 | Duples + Juego 40 |
| [1,12,12,12] | 6.70 | Medias + Juego 31 |
| [11,11,12,12] | 6.68 | Duples + Juego 40 |
| [10,10,12,12] | 6.61 | Duples  + Juego 40 |

### Composición de Manos

- **Con pares**: 104 manos (31.5%)
- **Con juego (31-40)**: 104 manos (31.5%)  
- **Solo punto**: 226 manos (68.5%)
  - Punto promedio: 22.8 (min: 4, max: 30)
  - EV promedio: ~2.9 puntos

---

## 🔬 Fundamentos Matemáticos

### Fórmula EV Total

$$
\text{EV}_{\text{Total}} = \text{EV}_{\text{Grande}} + \text{EV}_{\text{Chica}} + \text{EV}_{\text{Pares}} + \text{EV}_{\text{Juego/Punto}}
$$

**Donde cada lance se descompone en:**

$$
\text{EV}_{\text{Lance}} = \text{EV}_{\text{Propio}} + \beta \cdot \text{EV}_{\text{Soporte}}
$$

- **EV_Propio**: Valor esperado de mi mano propia
- **EV_Soporte**: Valor esperado del soporte del compañero
- **β** ∈ [0, 1]: Factor de confianza (0.65 conservador, 0.75 normal, 0.85 agresivo)

### Valores Base (W)

| Lance | Valor W |
|-------|---------|
| **Grande/Chica** | 1.0 |
| **Pares** | 1 (pares), 2 (medias), 3 (duples) |
| **Juego** | 2.0-3.0 (según jerarquía 31 > 32 > 40 > ... > 33) |
| **Punto** | 1.0 (todos los puntos) |

**Documentación completa**: Ver [FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md)

---

## ✅ Verificaciones

### Tests Automatizados

```bash
python3 test_motor_desempates.py
```

**Resultado**: 7/7 tests pasados ✓

**Verificaciones incluidas**:
- Probabilidades exactas (prob_menor + prob_empate)
- Factor de desempate por posición
- Casos típicos de partida
- Coherencia entre posiciones
- Decisión estocástica

### Sanity Check

```bash
python3 sanity_check_ev.py
```

**Verificaciones**:
1. ✅ Posición 1 siempre EV ≥ otras posiciones
2. ✅ Correlaciones entre posiciones > 0.99
3. ✅ Diferencias proporcionales a P(empate)
4. ✅ Rankings coherentes (juego 31 arriba, sin jugadas abajo)

---

## 🛠️ Configuración

### Perfiles de Juego

```python
PERFILES = {
    'conservador': {'beta': 0.65, 'percentil_mu': 55},  # Menos confianza, más cortes
    'normal':      {'beta': 0.75, 'percentil_mu': 45},  # Equilibrado
    'agresivo':    {'beta': 0.85, 'percentil_mu': 30}   # Alta confianza, menos cortes
}
```

### Modos de Juego

- **Modo 8 Reyes**: 40 cartas (4 ases, 4 reyes, 4 caballos, 4 sotas, 6×4 cartas 4-10)
- **Modo 4 Reyes**: 32 cartas (sin 10s)

---

## 📚 Historial de Versiones

### v2.3 (febrero 2026) - FASE 1 COMPLETA ✅

**Cambios principales:**
1. ✅ Eliminación de heurística bayesiana lineal
2. ✅ Probabilidades condicionadas exactas (hipergeométrica)
3. ✅ Corrección de valores base (E_EXTRA → 0.0)
4. ✅ **Jerarquía del juego** implementada (31 > 32 > 40 > ...)
5. ✅ **Lance de Punto** implementado
6. ✅ Desempates exactos por posición

**Ver historial completo**: [CHANGELOG_v2.3.md](CHANGELOG_v2.3.md)

---

## 🎯 Próximos Pasos (Fase 2)

- [ ] Simulaciones masivas de partidas completas
- [ ] Validación estadística contra juego real
- [ ] Implementación de sistema de envites (E_EXTRA > 0)
- [ ] Modelo de descarte óptimo (qué cartas tirar)
- [ ] Tracking de historial de partida (señales, faroleos)

---

## 📖 Documentación Completa

- **[README.md](README.md)** (este archivo): Visión general y uso rápido
- **[FUNDAMENTOS_MATEMATICOS.md](FUNDAMENTOS_MATEMATICOS.md)**: Fórmulas y modelado matemático
- **[CHANGELOG_v2.3.md](CHANGELOG_v2.3.md)**: Historial detallado de cambios
- **[SANITY_CHECK_README.md](SANITY_CHECK_README.md)**: Guía de verificación

---

## 📄 Licencia

Este proyecto es de código abierto para uso educativo y de investigación.

---

**Desarrollado por**: Marco Ezquerra  
**Fecha**: Febrero 2026  
**Versión**: 2.3 - Fase 1 Completa
