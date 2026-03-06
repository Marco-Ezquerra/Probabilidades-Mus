# 📥 Instrucciones de Descarga y Ejecución Local

## 1️⃣ Clonar el Repositorio

```bash
# Opción 1: HTTPS (recomendado)
git clone https://github.com/Marco-Ezquerra/Probabilidades-Mus.git
cd Probabilidades-Mus

# Opción 2: SSH (si tienes configurada la clave)
git clone git@github.com:Marco-Ezquerra/Probabilidades-Mus.git
cd Probabilidades-Mus
```

---

## 2️⃣ Requisitos del Sistema

### Mínimo (para tests):
- **Python**: 3.8 o superior
- **RAM**: 4GB
- **Disco**: 200MB libres

### Recomendado (para Fase 2 completa):
- **CPU**: 8+ cores
- **RAM**: 16GB
- **Disco**: 1GB libres
- **Tiempo**: 12-24 horas disponibles

---

## 3️⃣ Instalación de Dependencias

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Dependencias instaladas:**
- pandas >= 1.3.0
- (numpy, tqdm se instalan como dependencias transitivas)

---

## 4️⃣ Verificar Instalación

### Opción A: Tests Rápidos (2-3 minutos)

```bash
# Test de motor de decisión (Fase 1)
python3 tests/test_motor_decision.py

# Test de evaluador de ronda
python3 tests/test_evaluador_ronda.py

# Test de descarte heurístico
python3 tests/test_descarte_heuristico.py

# Test de tracking de descartes (Fase 2)
python3 tests/test_tracking_descartes.py
```

**Resultado esperado:** Todos los tests deben pasar ✅

### Opción B: Validación Completa del Proyecto

```bash
python3 demos/validar_proyecto.py
```

---

## 5️⃣ Ejecuciones Posibles

### 🔹 Demo Interactiva (Fase 1)

```bash
python3 demos/demo_interactiva.py
```

Permite ingresar manos manualmente y ver decisiones del motor.

### 🔹 Fase 2 - Test Rápido (15-20 minutos)

```bash
cd calculadora_probabilidades_mus

# Ejecutar con 1M iteraciones (test)
python3 generar_politicas_rollout.py
```

Esto genera políticas con 1,000,000 de iteraciones para probar que todo funciona.

**Archivos generados:**
- `probabilidades_fase2_test.csv` (~150KB)
- `politicas_optimas_fase2_test.csv` (~300KB)

### 🔹 Fase 2 - Producción Completa (12-24 horas ⚠️)

**ADVERTENCIA:** Esta ejecución es muy intensiva. Lee [GUIA_EJECUCION.md](GUIA_EJECUCION.md) antes de ejecutar.

```bash
cd calculadora_probabilidades_mus

# Opción 1: Ejecución con nohup (recomendado)
nohup python3 generar_politicas_rollout.py \
    --num-iteraciones 40000000 \
    > ../logs/generacion_politicas_final.log 2>&1 &

# Ver progreso en tiempo real
tail -f ../logs/generacion_politicas_final.log

# Opción 2: Ejecución directa (bloquea terminal)
python3 generar_politicas_rollout.py --num-iteraciones 40000000
```

**Monitorización (desde otra terminal):**
```bash
# Ver últimas líneas del log
tail ../logs/generacion_politicas_final.log

# Ver progreso cada 30 segundos
watch -n 30 tail -20 ../logs/generacion_politicas_final.log

# Uso de CPU
top -o %CPU | head -20
```

**Archivos generados:**
- `probabilidades_fase2.csv` (~150KB)
- `politicas_optimas_fase2.csv` (~15MB)

### 🔹 Simulación con Políticas Óptimas

Una vez generadas las políticas:

```bash
cd calculadora_probabilidades_mus
python3 simulador_fase2.py
```

---

## 6️⃣ Estructura de Archivos

```
Probabilidades-Mus/
├── README.md                          # Guía principal
├── GUIA_EJECUCION.md                  # Recomendaciones cloud vs local
├── requirements.txt                   # Dependencias Python
│
├── calculadora_probabilidades_mus/   # 🧠 Motor principal
│   ├── motor_decision.py              # Decisión EV Fase 1
│   ├── calculadoramus.py              # Monte Carlo
│   ├── evaluador_ronda.py             # Evalúa lances
│   ├── generar_politicas_rollout.py   # Q-Learning Fase 2 ⭐
│   ├── simulador_fase2.py             # Simulador con políticas
│   └── params.py                      # Configuración
│
├── tests/                             # ✅ Suite de tests (7 archivos)
│   ├── test_motor_decision.py
│   ├── test_evaluador_ronda.py
│   ├── test_descarte_heuristico.py
│   └── test_tracking_descartes.py
│
├── demos/                             # 🎮 Scripts demostración
│   ├── demo_interactiva.py
│   └── validar_proyecto.py
│
├── docs/                              # 📚 Documentación técnica
│   ├── CHANGELOG_v2.4.md
│   ├── FUNDAMENTOS_MATEMATICOS.md
│   └── README_FASE2.md
│
├── logs/                              # 📊 Logs de ejecución
└── utils/                             # 🛠️ Utilidades
    ├── descarte_heuristico.py
    └── mascaras_descarte.py
```

---

## 7️⃣ Flujo de Trabajo Recomendado

### Para Desarrollo/Testing:

1. **Clonar repositorio** (paso 1)
2. **Instalar dependencias** (paso 3)
3. **Ejecutar tests** (paso 4)
4. **Probar demo interactiva** (paso 5.1)
5. **Ejecutar Fase 2 test** (1M iteraciones, paso 5.2)

### Para Producción Final:

1. **Todo lo anterior**
2. **Leer** [GUIA_EJECUCION.md](GUIA_EJECUCION.md)
3. **Decidir:** Local (12-24h) vs Nube (6-8h, $8-10)
4. **Ejecutar Fase 2 completa** (40M iteraciones, paso 5.3)
5. **Verificar resultados**
6. **Ejecutar simulaciones** (paso 5.4)

---

## 8️⃣ Verificación de Resultados

### Después de Fase 2:

```bash
cd calculadora_probabilidades_mus

# Verificar que se generaron los archivos
ls -lh probabilidades_fase2.csv
ls -lh politicas_optimas_fase2.csv

# Ver primeras líneas de probabilidades
head -20 probabilidades_fase2.csv

# Ver primeras líneas de políticas
head -20 politicas_optimas_fase2.csv

# Interpretar políticas (genera CSV legible)
python3 interpretar_politicas.py
cat politicas_legibles.csv
```

### Sanity Checks:

```bash
# Verificar coherencia matemática Fase 1
python3 calculadora_probabilidades_mus/sanity_check_ev.py

# Validar proyecto completo
python3 demos/validar_proyecto.py
```

---

## 9️⃣ Troubleshooting

### Error: `ModuleNotFoundError`

```bash
# Verificar instalación de pandas
pip list | grep pandas

# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

### Error: `FileNotFoundError` en tests

```bash
# Asegúrate de ejecutar desde la raíz del proyecto
pwd  # Debe mostrar: .../Probabilidades-Mus

# Ejecutar tests correctamente
python3 tests/test_motor_decision.py
```

### Error: Proceso muy lento en Fase 2

**Solución 1:** Reducir iteraciones para test
```bash
# Solo 100k iteraciones (~30 segundos)
python3 generar_politicas_rollout.py --num-iteraciones 100000
```

**Solución 2:** Usar la nube (ver [GUIA_EJECUCION.md](GUIA_EJECUCION.md))

### Error: `MemoryError`

Tu ordenador no tiene suficiente RAM. Opciones:
1. Cerrar otros programas
2. Reducir iteraciones
3. Usar nube (recomendado)

---

## 🆘 Soporte

Si encuentras problemas:

1. **Verifica requisitos del sistema** (paso 2)
2. **Ejecuta tests de validación** (paso 4)
3. **Revisa logs** en `logs/`
4. **Consulta documentación:**
   - [README.md](README.md) - Visión general
   - [GUIA_EJECUCION.md](GUIA_EJECUCION.md) - Ejecución detallada
   - [docs/FUNDAMENTOS_MATEMATICOS.md](docs/FUNDAMENTOS_MATEMATICOS.md) - Teoría
   - [docs/CHANGELOG_v2.4.md](docs/CHANGELOG_v2.4.md) - Cambios recientes

---

## ✅ Checklist de Verificación

- [ ] Repositorio clonado
- [ ] Python 3.8+ instalado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Tests de motor_decision.py pasando
- [ ] Tests de evaluador_ronda.py pasando
- [ ] Tests de tracking_descartes.py pasando
- [ ] Demo interactiva funciona
- [ ] Fase 2 test (1M) completado
- [ ] Decisión tomada: local vs nube
- [ ] (Opcional) Fase 2 completa (40M) ejecutada
- [ ] (Opcional) Simulaciones ejecutadas

---

**¡Listo para ejecutar! 🚀**

Si vas a ejecutar la Fase 2 completa (40M iteraciones), **lee primero [GUIA_EJECUCION.md](GUIA_EJECUCION.md)** para decidir entre local o nube.
