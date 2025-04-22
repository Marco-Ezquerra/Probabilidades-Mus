import random

import itertools
import numpy as np
import pandas as pd
def inicializar_baraja():
    return [1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 5, 5, 5, 5,
            6, 6, 6, 6, 7, 7, 7, 7, 10, 10, 10, 10,
            11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12]
import itertools
import numpy as np
def guardar_resultados(resultados, filename):
    df = pd.DataFrame(resultados)
    df.to_csv(filename, index=False)
    return df
def inicializar_baraja():
    return [1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 5, 5, 5, 5,
            6, 6, 6, 6, 7, 7, 7, 7, 10, 10, 10, 10,
            11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12]

def guardar_resultados_en_txt(df, filename):
    with open(filename, 'w') as f:
        f.write(df.to_string(index=False))

def generar_manos_unicas():
    # generamso las combinaciones de 4 Cartas
    baraja = inicializar_baraja()
    combinaciones_manos = list(itertools.combinations(baraja, 4))

    # Eliminamos manos duplicadas
    manos_unicas_dict = {}
    for mano in combinaciones_manos:
        key = tuple(sorted(mano))
        if key not in manos_unicas_dict:
            manos_unicas_dict[key] = True

    # Convertir las llaves del diccionario a una lista de listas para facilitar el procesamiento posterior
    manos_unicas_list = [list(mano) for mano in manos_unicas_dict.keys()]

  
    

    return manos_unicas_list


manos_unicas_list = generar_manos_unicas()

#print(f"Total de manos únicas: {len(manos_unicas_array)}")
#print("Ejemplos de manos únicas:", manos_unicas_array[:5])
#print(manos_unicas_array[320])


def tiene_pares(mano):
    valores = [carta for carta in mano]
    pares = {valor: valores.count(valor) for valor in set(valores)}
    pares = {k: v for k, v in pares.items() if v > 1}
    return pares

def clasificar_pares(mano):
    pares = tiene_pares(mano)
    if len(pares) == 0:
        return "no tiene pares", 0, 0
    elif len(pares) == 1 and list(pares.values())[0] == 4:
        return "duples", max(pares), max(pares)
    elif len(pares) == 1 and list(pares.values())[0] == 3:
        return "medias", max(pares), 0
    elif len(pares) == 1 and list(pares.values())[0] == 2:
        return "pares", max(pares), 0
    elif len(pares) == 2 and all(v == 2 for v in pares.values()):
        return "duples", max(pares), min(pares)
    else:
        raise ValueError("La mano tiene una combinación no válida de pares")

def comparar_pares(tipo1, valor1, valor2_1, tipo2, valor2, valor2_2, es_mano):
    jerarquia = {"no tiene pares": 0, "pares": 1, "medias": 2, "duples": 3}
    if jerarquia[tipo1] > jerarquia[tipo2]:
        return 1
    elif jerarquia[tipo1] < jerarquia[tipo2]:
        return -1
    else:
        if tipo1 == "duples":
            if valor1 > valor2:
                return 1
            elif valor1 < valor2:
                return -1
            else:
                if valor2_1 > valor2_2:
                    return 1
                elif valor2_1 < valor2_2:
                    return -1
                else:
                    return 1 if es_mano else -1  #  gana la mano
        else:
            if valor1 > valor2:
                return 1
            elif valor1 < valor2:
                return -1
            else:
                return 1 if es_mano else -1  #  gana la mano

def comparar_manos(mano, mano_oponente, es_mano):
    for i in range(len(mano)):
        if mano_oponente[i] > mano[i]:
            return -1
        elif mano_oponente[i] < mano[i]:
            return 1
    return 1 if es_mano else -1  #gana la mano

def calcular_valor_juego(mano):
    valor = sum(min(carta, 10) for carta in mano)
    return valor if valor >= 31 else 0

def convertir_valor_juego(valor):
    if valor == 31:
        return 8
    elif valor == 32:
        return 7
    elif valor == 40:
        return 6
    elif valor == 37:
        return 5
    elif valor == 36:
        return 4
    elif valor == 35:
        return 3
    elif valor == 34:
        return 2
    elif valor == 33:
        return 1
    else:
        return 0

def comparar_juego(valor1, valor2, es_mano):
    if valor1 > valor2:
        return 1
    elif valor1 < valor2:
        return -1
    else:
        return 1 if es_mano else -1  # Si hay empate, gana la mano

def calcular_valor_punto(mano):
    return sum(min(carta, 10) for carta in mano)

def comparar_punto(punto1, punto2, es_mano):
    if abs(punto1 - 30) < abs(punto2 - 30):
        return 1
    elif abs(punto1 - 30) > abs(punto2 - 30):
        return -1
    else:
        return 1 if es_mano else -1  # Si hay empate, gana la mano

resultados=[]
for i in range(len(manos_unicas_list)):
    
    mano = manos_unicas_list[i]
    print(mano)
    
    baraja = inicializar_baraja()
    for carta in mano:
        if carta in baraja:
            baraja[baraja.index(carta)] = 0

    # Filtramos  los ceros de la baraja modificada
    baraja_sin_ceros_original = [carta for carta in baraja if carta != 0]

   #Hacemos una simulacion de 100000 partidas por cada mano, con este numero obtenemos unos resultados fiables, aunque para una precisión "exacta"
   #sería conveniente iter=10**5
    iteraciones = 100000
    ggrande = 0
    pgrande = 0
    gchica = 0
    pchica = 0
    gpares = 0
    ppares = 0
    gjuego = 0
    pjuego = 0

    # Definir si la mano es la mano principal
    es_mano = True

    # Simular las manos
    for _ in range(iteraciones):
        baraja_sin_ceros = baraja_sin_ceros_original.copy()
        
        mano_aleatoria = random.sample(baraja_sin_ceros, 4)
        for carta in mano_aleatoria:
            if carta in baraja_sin_ceros:
                baraja_sin_ceros[baraja_sin_ceros.index(carta)] = 0

        mano2 = random.sample([carta for carta in baraja_sin_ceros if carta != 0], 4)

        # Ordenamos las manos para la comparación de los lances de garnde y chica
        mano.sort()
        mano_aleatoria.sort()
        mano2.sort()

        #   Grande
        resultado_grande1 = comparar_manos(mano, mano_aleatoria, es_mano)
        resultado_grande2 = comparar_manos(mano, mano2, es_mano)
        
        if resultado_grande1 < 0 and resultado_grande2 < 0:
            ggrande += 1
        else:
            pgrande += 1

        # Pequeña
        mano.sort(reverse=True)
        mano_aleatoria.sort(reverse=True)
        mano2.sort(reverse=True)
        
        resultado_chica1 = comparar_manos(mano, mano_aleatoria, es_mano)
        resultado_chica2 = comparar_manos(mano, mano2, es_mano)

        if resultado_chica1 > 0 and resultado_chica2 > 0:
            gchica += 1
        else:
            pchica += 1

        #Pares
        tipo_mano, valor_mano, valor_mano2 = clasificar_pares(mano)
        tipo_mano_aleatoria, valor_mano_aleatoria, valor_mano2_aleatoria = clasificar_pares(mano_aleatoria)
        tipo_mano2, valor_mano2_mano2, valor_mano2_2 = clasificar_pares(mano2)
        
        resultado_pares1 = comparar_pares(tipo_mano, valor_mano, valor_mano2, tipo_mano_aleatoria, valor_mano_aleatoria, valor_mano2_aleatoria, es_mano)
        resultado_pares2 = comparar_pares(tipo_mano, valor_mano, valor_mano2, tipo_mano2, valor_mano2_mano2, valor_mano2_2, es_mano)
        
        if resultado_pares1 > 0 and resultado_pares2 > 0:
            gpares += 1
        else:
            ppares += 1

        # Juego
        valor_juego = convertir_valor_juego(calcular_valor_juego(mano))
        valor_juego_aleatoria = convertir_valor_juego(calcular_valor_juego(mano_aleatoria))
        valor_juego2 = convertir_valor_juego(calcular_valor_juego(mano2))
        
        if valor_juego > 0 or valor_juego_aleatoria > 0 or valor_juego2 > 0:
            resultado_juego1 = comparar_juego(valor_juego, valor_juego_aleatoria, es_mano)
            resultado_juego2 = comparar_juego(valor_juego, valor_juego2, es_mano)
            
            if resultado_juego1 > 0 and resultado_juego2 > 0:
                gjuego += 1
            else:
                pjuego += 1
        else:
            # Comparar para punto
            valor_punto = calcular_valor_punto(mano)
            valor_punto_aleatoria = calcular_valor_punto(mano_aleatoria)
            valor_punto2 = calcular_valor_punto(mano2)
            
            resultado_punto1 = comparar_punto(valor_punto, valor_punto_aleatoria, es_mano)
            resultado_punto2 = comparar_punto(valor_punto, valor_punto2, es_mano)
            
            if resultado_punto1 > 0 and resultado_punto2 > 0:
                gjuego += 1
            else:
                pjuego += 1
  # Mostrar los resultados
    #print(f"Probabilidad de ganar a GRANDE: {gchica / iteraciones:.2%}")
    #print(f"Probabilidad de ganar a PEKE: {ggrande / iteraciones:.2%}")
    #print(f"Probab(ilidad de ganar a pares: {gpares / iteraciones:.2%}")
    #print(f"Probabilidad de ganar a juego: {gjuego / iteraciones:.2%}")   
    #print(gchica/iteraciones)
    #print(ggrande/iteraciones)
    #print(gpares/iteraciones)
    #print(gjuego/iteraciones)
    resultado = {
        "mano": mano,
        "probabilidad_grande": gchica / iteraciones,
        "probabilidad_chica": ggrande / iteraciones,
        "probabilidad_pares": gpares / iteraciones,
        "probabilidad_juego": gjuego / iteraciones
    }
    resultados.append(resultado)
  
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv('resultados_probabilidades.csv', index=False)
print("Resultados guardados en 'resultados_probabilidades.csv'")
print(df_resultados.head()) 
print(df_resultados)   
# Guardar todos los resultados en un fichero de texto al final del bucle
guardar_resultados_en_txt(df_resultados, 'resultados_probabilidades.txt')
print("Resultados guardados en 'resultados_probabilidades.txt'")

    
 



    



       

 




#### LOS PRINGT ESTAN MAL GCHICA=GGRANDE


