Cálculo de probabilidades a primeras dadas en el juego de Mus mediante Monte Carlo
==================================================================================

Este proyecto en Python emplea el **método Monte Carlo** para estimar las probabilidades de victoria de todas las posibles manos iniciales ("a primeras dadas") en el juego del Mus. El programa se centra en los lances principales: GRANDE, CHICA, PARES y JUEGO o PUNTO si no hay juego

-------------------------------------------------------------------------------

ENFOQUE MONTE CARLO
-------------------

Se simulan 100.000 partidas por cada mano inicial posible (únicas en valor), enfrentándola a dos manos aleatorias generadas con el resto del mazo. Este enfoque estadístico permite estimar la probabilidad de que una mano gane en cada uno de los lances del juego.

Cada iteración selecciona dos manos contrincantes válidas, y se comparan con la mano fija en todos los lances, contabilizando las veces que la mano principal gana.

-------------------------------------------------------------------------------

DESCRIPCIÓN DEL CÓDIGO PRINCIPAL (calculadoramus.py)
-----------------------------------------------------

- Se generan todas las combinaciones únicas de 4 cartas posibles del mazo.
- Por cada mano única:
    - Se simulan 100.000 partidas contra manos aleatorias válidas.
    - Se evalúa si la mano gana en GRANDE, CHICA, PARES y JUEGO/PUNTO.
- Las reglas del Mus se implementan de forma precisa (clasificación de pares, valores de juego, resolución de empates).
- Los resultados se guardan en dos archivos: CSV y TXT.

ARCHIVOS GENERADOS:
- resultados_probabilidades.csv  → Tabla con las probabilidades estimadas por mano.
- resultados_probabilidades.txt  → Versión legible de la tabla anterior.

-------------------------------------------------------------------------------

ORDENACIÓN DE RESULTADOS (ordenartabla.py)
------------------------------------------

El script `ordenartabla.py` permite **ordenar la tabla de resultados** por la probabilidad de victoria en GRANDE (u otro criterio modificable). Esto facilita el análisis estratégico de las mejores manos iniciales.

Genera:
- tabla_resultados_ordenados.csv  → Tabla ordenada por probabilidad.
- tabla_resultados_ordenados.txt  → Versión en texto de la tabla ordenada.

