# Calculadora de Probabilidades de Mus

Calculadora de probabilidades para el juego del **Mus** mediante simulación **Monte Carlo**. Este programa calcula las probabilidades de victoria de todas las manos iniciales posibles en los cuatro lances principales: **GRANDE**, **CHICA**, **PARES** y **JUEGO/PUNTO**.

## 🎯 ¿Qué hace este programa?

Simula 100.000 partidas por cada mano inicial única, enfrentándola contra dos manos aleatorias generadas con el resto de la baraja. Esto permite estimar con precisión estadística las probabilidades reales de cada mano en cada lance del juego.



## 🚀 Uso

```bash
python calculadoramus.py
```

El programa te pedirá que elijas el modo de juego (4 u 8 reyes) y generará automáticamente:

- **CSV**: Tabla de resultados en formato de datos
- **TXT**: Tabla de resultados en formato legible

## 📊 Resultados

Para cada mano única, el programa calcula:

- **Probabilidad de ganar a GRANDE**: Comparación de mayor a menor
- **Probabilidad de ganar a CHICA**: Comparación de menor a mayor  
- **Probabilidad de ganar a PARES**: Pares, medias y duples
- **Probabilidad de ganar a JUEGO/PUNTO**: Juego (31-40) o punto si no hay juego

## 📦 Requisitos

Python 3.7 o superior.

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

O instalar manualmente:
```bash
pip install pandas
```

## 🔧 Scripts adicionales

### ordenartabla.py
Permite ordenar los resultados por cualquier criterio (por defecto, por probabilidad de GRANDE).

```bash
python ordenartabla.py
```

## 📖 Método Monte Carlo

El método Monte Carlo es una técnica estadística que utiliza la repetición aleatoria para obtener resultados numéricos. En este caso:

1. Para cada mano inicial, se simulan 100.000 enfrentamientos
2. En cada simulación se generan dos manos contrincantes aleatorias
3. Se evalúan los cuatro lances del juego
4. Se contabilizan las victorias y se calcula la probabilidad

Con 100.000 iteraciones se obtienen resultados muy fiables estadísticamente.

## 📝 Estructura del código

```
calculadora_probabilidades_mus/
├── calculadoramus.py       # Programa principal
├── ordenartabla.py          # Script para ordenar resultados
└── README_MonteCarlo_Mus.txt  # Documentación original
```

El código está estructurado de forma modular:
- Funciones separadas para cada lance
- Configuración de baraja según modo
- Simulación Monte Carlo optimizada
- Exportación de resultados limpia

## 🎲 Ejemplo de salida

```
Mano         | Grande | Chica | Pares | Juego
[1,1,1,1]    | 0.9542 | 0.0021| 0.8923| 0.1234
[12,12,12,12]| 0.0018 | 0.9673| 0.8854| 0.9876
...
```

## 📄 Licencia

Proyecto de código abierto para análisis estadístico del juego del Mus.

---

**Nota**: El Mus es un juego de cartas tradicional español. Este programa es una herramienta de análisis probabilístico para entender mejor las matemáticas detrás del juego.
