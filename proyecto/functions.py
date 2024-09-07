import pandas as pd
import pickle

datos_medias = pd.read_csv('data/tarifas_limpias.csv')

# los valores de tarifa pueden ser 'fijo' y 'variable', creamos funcion que asigne los precios llano, valle y punta dependiendo del tipo de tarifa
def price_types(tarifa: bool) -> pd.DataFrame:
    price_df = pd.DataFrame()
    
    variable_df = datos_medias[datos_medias['tipo_tarifa'] == 'variable']
    fixed_df = datos_medias[datos_medias['tipo_tarifa'] == 'fija']

    variable_mean_llano = float(variable_df['precio_llano'].mean())
    variable_mean_valle = float(variable_df['precio_valle'].mean())
    variable_mean_punta = float(variable_df['precio_punta'].mean())

    # El llano, punta y valle son el mismo valor en las tarifas fijas
    fixed_mean = float(fixed_df['precio_punta'].mean())

    if tarifa:
        price_df['precio_llano'] = [variable_mean_llano]
        price_df['precio_punta'] = [variable_mean_punta]
        price_df['precio_valle'] = [variable_mean_valle]
    else:
        price_df['precio_llano'] = [fixed_mean]
        price_df['precio_punta'] = [fixed_mean]
        price_df['precio_valle'] = [fixed_mean]

    return price_df 


# Obtenemos una potencia y le asignamos una categoría en string (estamos simulando un get_dummies que es lo que recibe en los datos de entrenamiento)
def W_clarifications(potencia: float) -> pd.DataFrame:
    potencia_df = pd.DataFrame()

    if potencia <= 10:
        potencia_df['potencia_contratada_Entre 10 y 15'] = [False]
        potencia_df['potencia_contratada_≤10'] = [True]
        potencia_df['potencia_contratada_≤15'] = [False]
    
    elif (potencia > 10) and (potencia < 15):
        potencia_df['potencia_contratada_Entre 10 y 15'] = [True]
        potencia_df['potencia_contratada_≤10'] = [False]
        potencia_df['potencia_contratada_≤15'] = [False]
    
    elif potencia == 15:
        potencia_df['potencia_contratada_Entre 10 y 15'] = [False]
        potencia_df['potencia_contratada_≤10'] = [False]
        potencia_df['potencia_contratada_≤15'] = [True]
    
    else:
        potencia_df['potencia_contratada_Entre 10 y 15'] = [False]
        potencia_df['potencia_contratada_≤10'] = [False]
        potencia_df['potencia_contratada_≤15'] = [False]

    return potencia_df

# Recibe los string 'variable' o 'fija' y devuelve un booleano
def fee_clasifications(tarifa: str) -> bool:
    tarifa_bool = False

    if tarifa == 'variable':
        tarifa_bool = True
    else:
        tarifa_bool = False

    return tarifa_bool


# convertir los datos del user en un df valido para meterlo en el modelo de kmeans
# (el dataset tiene que tener el mismo formato que el pandas utilizado en el entrenamiento del modelo)

# precio: valor entre 0 y 1
# tarifa: valores: 'fijo' o 'variable'
# potencia: entre 0 y 20
# permanencia: 0 o 1
def user_information(precio: float, tarifa: str, potencia: float, permanencia: int) -> pd.DataFrame:
    information = pd.DataFrame()
    information['precio_€/kWh'] = [precio]

    prices = price_types(fee_clasifications(tarifa)) # ya que tarifa tiene que ser un bool no un variable o fija
    information = pd.concat([information, prices], axis=1)

    information['permanencia'] = [float(permanencia)] # los datos tienen que ser identicos a la entrada del modelo

    information['tipo_tarifa_variable'] = [float(fee_clasifications(tarifa))] # tenemos que convertir los bool en floats (1.0 o 0.0)

    tarifa_potencia = W_clarifications(potencia)
    information = pd.concat([information, tarifa_potencia], axis=1)

    return information



# aplicamos el modelo para ver a que cluster perteneceria la tarifa del usuario
def cluster_clasification(user_info: pd.DataFrame) -> int:
    with open('data/model_information.pkl', 'rb') as f:
        data = pickle.load(f)
        scaler = data['scaler']
        kmeans = data['kmeans']

    user_info_scaled = scaler.transform(user_info)
    cluster_asignado = kmeans.predict(user_info_scaled)[0] # devuelve una lista de un elemento 
    
    return cluster_asignado


# filtramos los datos con el cluster obtenido + filtro a mostrar al usuario (tarifas mas baratas), con los datos (X)
def filter_data(user_info: pd.DataFrame) -> pd.DataFrame:
    with open('data/model_information.pkl', 'rb') as f:
        data = pickle.load(f)
        db = data['clustered_data']
    
    # mascara para mostrar todos los datos de un mismo cluster
    cluster_asignado = cluster_clasification(user_info)
    datos_clasificados = db[db['cluster'] == cluster_asignado]
    datos_clasificados = datos_clasificados.drop(columns=['cluster']) # Una vez clasificado ya podemos eliminar el cluster
    
    # Sin embargo, los datos estan en formato "datos de entrenamiento del modelo" y no "user-friendly" asi que hay que transformarlos
    datos_convertidos = user_friendly_data(datos_clasificados)

    # Por último filtramos los datos para darle al usuario lo que quiere, en este caso una tarifa mas barata
    user_price = float(user_info['precio_€/kWh'].iloc[0]) # queremos el valor numerico exacto
    user_permanencia = int(user_info['permanencia'].iloc[0])
    datos_filtrados = datos_convertidos[(datos_convertidos['precio_€/kWh'] < user_price) & (datos_convertidos['permanencia'] == user_permanencia)]

    return datos_filtrados


# El dataframe que pasamos como parametro tiene que ser de una forma especifica, en caso contrario no funcionara
def user_friendly_data(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy() # para solucionar warnings

    data['tipo_tarifa'] = data['tipo_tarifa_variable'].map({False: 'fija', True: 'variable'})
    data = data.drop(columns=['tipo_tarifa_variable'])

    mapeo_potencia = {
        'potencia_contratada_Entre 10 y 15': 'Entre 10 y 15',
        'potencia_contratada_≤10': '≤10',
        'potencia_contratada_≤15': '≤15',
    }

    # Seleccionar las columnas dummy que quieres revertir
    columnas_dummies = ['potencia_contratada_Entre 10 y 15',
                        'potencia_contratada_≤10', 'potencia_contratada_≤15']

    # Crear una nueva columna con el valor revertido
    data['potencia_contratada'] = data[columnas_dummies].idxmax(axis=1).map(mapeo_potencia)

    # Eliminar las columnas dummy si ya no son necesarias
    data = data.drop(columns=columnas_dummies)

    return data


# user_variable = user_information(0.119746, 'variable', 12, 1)
# user_fixed = user_information(0.119746, 'fija', 12, 0)
# cluster = cluster_clasification(user_fixed)
# print(filter_data(cluster, user_variable))