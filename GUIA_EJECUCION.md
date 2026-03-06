# 🚀 Guía de Ejecución - Generación de Políticas de Descarte (Fase 2)

Esta guía proporciona recomendaciones detalladas sobre **dónde y cómo ejecutar** la generación de políticas óptimas de descarte mediante Q-Learning.

---

## 📊 Resumen de Requisitos

### Configuración Actual (params.py)

```python
N_ITERACIONES_ROLLOUT = 40_000_000  # 40 millones de iteraciones
MODO_8_REYES = True                 # Baraja de 8 reyes
RANDOM_SEED = 42                    # Semilla (reproducibilidad)
TASA_MUS_OBJETIVO = 0.20            # 20% de rondas válidas esperadas
```

### Recursos Necesarios

| Recurso | Mínimo | Recomendado | Óptimo |
|---------|--------|-------------|--------|
| **CPU** | 4 cores | 8 cores | 16+ cores |
| **RAM** | 8 GB | 16 GB | 32 GB |
| **Almacenamiento** | 1 GB | 2 GB | 5 GB |
| **Tiempo estimado** | ~24h | ~8-12h | ~4-6h |

---

## ☁️ Opción 1: Ejecución en la Nube (RECOMENDADO)

### ✅ Ventajas

1. **Paralelismo masivo**: Acceso a 16-32+ cores simultáneos
2. **No afecta tu equipo**: Tu máquina queda libre para otros trabajos
3. **Monitorización remota**: Puedes desconectarte y volver más tarde
4. **Costo controlado**: Solo pagas por tiempo de ejecución
5. **Sin interrupciones**: No depende del estado de tu PC local
6. **Logs persistentes**: Todo queda guardado en la máquina virtual

### 🔧 Servicios Recomendados

#### A) **Google Cloud Platform (GCP)** - Mejor Opción

**Tipo de máquina recomendada:**
- **n2-standard-16** (16 vCPUs, 64 GB RAM)
- **Costo aproximado**: ~$0.80/hora → $8-10 total (10-12 horas)
- **Región**: us-central1 o europe-west1 (más baratas)

**Pasos:**
```bash
# 1. Crear instancia de Compute Engine
gcloud compute instances create mus-politicas \
    --machine-type=n2-standard-16 \
    --zone=us-central1-a \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB

# 2. Conectar vía SSH
gcloud compute ssh mus-politicas --zone=us-central1-a

# 3. Instalar dependencias y clonar repo
sudo apt update && sudo apt install -y python3-pip git
git clone https://github.com/Marco-Ezquerra/Probabilidades-Mus
cd Probabilidades-Mus
pip3 install -r requirements.txt

# 4. Ejecutar con nohup (sigue corriendo si te desconectas)
cd calculadora_probabilidades_mus
nohup python3 generar_politicas_rollout.py > ../logs/generacion_politicas_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 5. Monitorizar progreso
tail -f ../logs/generacion_politicas_*.log

# 6. Descargar resultados cuando termine
exit  # Salir de SSH
gcloud compute scp mus-politicas:/home/USER/Probabilidades-Mus/calculadora_probabilidades_mus/politicas_optimas_fase2.csv . --zone=us-central1-a

# 7. Eliminar instancia (para no seguir pagando)
gcloud compute instances delete mus-politicas --zone=us-central1-a
```

#### B) **AWS EC2**

**Tipo de instancia recomendada:**
- **c6i.4xlarge** (16 vCPUs, 32 GB RAM)
- **Costo aproximado**: ~$0.68/hora → $7-9 total

**Alternativa económica:**
- **c6i.2xlarge** (8 vCPUs, 16 GB RAM)
- **Costo aproximado**: ~$0.34/hora → $5-6 total (más lento, ~16-18h)

#### C) **Azure Virtual Machines**

**Tipo de máquina recomendada:**
- **Standard_D16s_v3** (16 vCPUs, 64 GB RAM)
- **Costo aproximado**: ~$0.77/hora → $8-10 total

#### D) **Paperspace / Lambda Labs** (GPU no necesaria, pero opciones baratas para CPU)

**Paperspace:**
- **C7** (16 vCPUs, 120 GB RAM)
- **Costo aproximado**: ~$0.35/hora → $4-5 total

---

## 💻 Opción 2: Ejecución Local

### ✅ Ventajas

1. **Sin costos adicionales**: Usa tu propia máquina
2. **Control total**: Acceso directo a archivos y logs
3. **Sin configuración cloud**: No requiere cuenta ni tarjeta de crédito
4. **Ideal para pruebas**: Fácil de debuggear y ajustar

### ⚠️ Desventajas

1. **Tiempo prolongado**: 12-24+ horas dependiendo de tu CPU
2. **Bloquea tu equipo**: No podrás usarlo para otras tareas intensivas
3. **Riesgo de interrupción**: Si se reinicia el PC por error, pierdes progreso
4. **Calentamiento**: CPU al 100% durante horas (considerar ventilación)

### 🔧 Pre-requisitos Local

```bash
# 1. Verificar CPU y RAM
python3 -c "import os; print(f'CPUs disponibles: {os.cpu_count()}')"
free -h  # Ver RAM disponible (Linux)

# 2. Verificar Python y dependencias
python3 --version  # Debe ser 3.8+
pip3 install -r requirements.txt

# 3. Verificar espacio en disco
df -h .  # Necesitas al menos 2 GB libres
```

### 🚀 Ejecución Local Recomendada

```bash
cd calculadora_probabilidades_mus

# Opción A: Con nohup (sigue corriendo si cierras terminal)
nohup python3 generar_politicas_rollout.py > ../logs/generacion_politicas_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo $!  # Guarda este número (PID del proceso)

# Monitorizar progreso
tail -f ../logs/generacion_politicas_*.log

# Opción B: Con screen (sesión persistente)
screen -S mus_politicas
python3 generar_politicas_rollout.py
# Ctrl+A, D para desconectar (sigue corriendo)
# screen -r mus_politicas para reconectar

# Opción C: Directa (bloqueante, no cerrar terminal)
python3 generar_politicas_rollout.py | tee ../logs/generacion_politicas_$(date +%Y%m%d_%H%M%S).log
```

### 📊 Monitorización del Progreso

```bash
# Ver progreso en tiempo real
tail -f ../logs/generacion_politicas_*.log

# Ver uso de CPU
top -p $(pgrep -f generar_politicas_rollout)

# Ver uso de RAM
ps aux | grep generar_politicas_rollout

# Estimar tiempo restante (busca "Tiempo estimado" en logs)
grep "Tiempo estimado" ../logs/generacion_politicas_*.log
```

---

## 🎯 Recomendaciones por Escenario

### Escenario 1: **Tienes poco tiempo y quieres resultados rápidos**
→ **NUBE (GCP n2-standard-16)**  
Costo: ~$10, Tiempo: 6-8h

### Escenario 2: **Quieres minimizar costos y no tienes prisa**
→ **Local (si tienes 8+ cores)** o **Nube económica (AWS c6i.2xlarge)**  
Costo: $0 (local) o ~$5 (nube), Tiempo: 16-24h

### Escenario 3: **Tu PC es antiguo/lento (< 4 cores)**
→ **NUBE obligatoria (cualquier opción con 8+ cores)**  
Local sería impracticable (>48h)

### Escenario 4: **Quieres experimentar/debuggear primero**
→ **Local con N_ITERACIONES_ROLLOUT reducido**  
Cambiar en `params.py`: `N_ITERACIONES_ROLLOUT = 1_000_000` (prueba rápida ~15 min)

### Escenario 5: **Presentación/defensa inminente**
→ **NUBE con máquina potente (16+ cores)**  
GCP n2-standard-16 o AWS c6i.4xlarge para garantizar finalización en <8h

---

## ⚙️ Configuración Avanzada

### Ajustar Número de Iteraciones

Editar `calculadora_probabilidades_mus/params.py`:

```python
# Para prueba rápida (15-30 minutos)
N_ITERACIONES_ROLLOUT = 1_000_000

# Para resultados intermedios (2-4 horas en 16 cores)
N_ITERACIONES_ROLLOUT = 10_000_000

# Para resultados óptimos (8-12 horas en 16 cores) - RECOMENDADO
N_ITERACIONES_ROLLOUT = 40_000_000

# Para máxima precisión (1-2 días en 16 cores)
N_ITERACIONES_ROLLOUT = 100_000_000
```

### Multiprocessing (Automático)

El sistema usa `multiprocessing` automáticamente detectando el número de cores disponibles:

```python
# En generar_politicas_rollout.py
n_cores = os.cpu_count()  # Detecta cores automáticamente
print(f"Usando {n_cores} workers en paralelo")
```

Para limitar manualmente:
```python
# Editar en generar_politicas_rollout.py línea ~350
n_cores = min(os.cpu_count(), 8)  # Limitar a 8 cores máximo
```

---

## 📝 Checklist Pre-Ejecución

### ✅ Antes de Ejecutar (Local o Nube)

- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Tests pasados (ejecutar `python3 tests/test_tracking_descartes.py`)
- [ ] Al menos 2 GB de espacio libre en disco
- [ ] Archivo `resultados_8reyes.csv` existe en `calculadora_probabilidades_mus/`
- [ ] Configuración revisada en `params.py`

### ✅ Solo para Nube

- [ ] Cuenta creada y configurada (GCP/AWS/Azure)
- [ ] Instancia creada con especificaciones adecuadas
- [ ] Acceso SSH funcionando
- [ ] Repositorio clonado en la instancia
- [ ] Configurado para ejecución con `nohup` o `screen`

---

## 🔍 Verificación de Resultados

Una vez finalizada la ejecución:

```bash
# 1. Verificar que el archivo existe
ls -lh calculadora_probabilidades_mus/politicas_optimas_fase2.csv

# 2. Ver primeras líneas
head calculadora_probabilidades_mus/politicas_optimas_fase2.csv

# 3. Contar entradas generadas
wc -l calculadora_probabilidades_mus/politicas_optimas_fase2.csv

# 4. Verificar columnas de descartes
head -1 calculadora_probabilidades_mus/politicas_optimas_fase2.csv | grep "n_descarte"

# Debe mostrar: mano,posicion,mascara_idx,reward_promedio,n_visitas,n_descarte_j1,n_descarte_j2,n_descarte_j3,n_descarte_j4
```

### Estadísticas Esperadas

```
- Archivo generado: politicas_optimas_fase2.csv
- Tamaño aproximado: 5-20 MB
- Número de entradas: ~20,000-50,000 (depende de cobertura)
- Columnas: 9 (incluyendo las 4 de descartes)
```

---

## 🆘 Troubleshooting

### Error: "Out of Memory"
**Solución:** Reducir `N_ITERACIONES_ROLLOUT` o usar máquina con más RAM

### Error: "ModuleNotFoundError"
**Solución:** `pip install -r requirements.txt`

### Proceso muy lento (< 1000 iteraciones/seg)
**Solución:** Verificar que multiprocessing está activado y que tienes suficientes cores

### Se interrumpió a mitad de ejecución
**Solución:** El progreso se pierde. En próxima ejecución, usar `screen` o `nohup` para evitar interrupciones

---

## 💡 Recomendación Final

### **Para presentación/defensa profesional:**

🎯 **Ejecutar en Nube (GCP n2-standard-16)**

**Ventajas:**
- ✅ Resultados en 6-8 horas garantizadas
- ✅ No bloquea tu equipo para preparar presentación
- ✅ Logs completos y reproducibles
- ✅ Se puede monitorizar remotamente
- ✅ Costo total: $8-10 (muy razonable para un TFG/proyecto académico)

**Comando completo:**
```bash
# En instancia GCP (después de configurar según instrucciones arriba)
cd calculadora_probabilidades_mus
nohup python3 generar_politicas_rollout.py > ../logs/generacion_politicas_final.log 2>&1 &
tail -f ../logs/generacion_politicas_final.log
```

---

## 📞 Soporte

Si encuentras problemas durante la ejecución:

1. Revisar logs en `logs/generacion_politicas_*.log`
2. Ejecutar `python3 tests/test_tracking_descartes.py` para verificar sistema
3. Consultar [docs/CHANGELOG_v2.4.md](docs/CHANGELOG_v2.4.md) para detalles de implementación
4. Abrir issue en GitHub con log completo si persiste el error

---

**Última actualización:** Marzo 2026  
**Versión:** 2.4
