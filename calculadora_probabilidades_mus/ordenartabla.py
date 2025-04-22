import pandas as pd

# Cargar los resultados
df = pd.read_csv("tabla_de_resultados.csv")

# Ordenar todas las filas según la probabilidad de ganar a GRANDE
df_ordenado = df.sort_values(by="probabilidad_grande", ascending=False)

# Guardar resultados ordenados
df_ordenado.to_csv("tabla_resultados_ordenados.csv", index=False)

with open("tabla_resultados_ordenados.txt", "w") as f:
    f.write(df_ordenado.to_string(index=False))


