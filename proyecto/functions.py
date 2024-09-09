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

    # Hacemos unos cambios para que el json se vea bien y ordenamos por precio
    datos_filtrados = datos_filtrados.copy()
    datos_filtrados.rename(columns={'precio_€/kWh': 'precio_euro/kWh'}, inplace=True)
    datos_filtrados.loc[:, 'potencia_contratada'] = datos_filtrados['potencia_contratada'].apply(transformar_valores)
    df_sorted = datos_filtrados.sort_values(by='precio_euro/kWh', ascending=True)

    return df_sorted


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

def transformar_valores(valor: str) -> str: # para que el json lo interprete bien
    if valor == '≤10':
        return 'menor o igual a 10'
    elif valor == '≤15':
        return '15'
    else:
        return valor
    

# Manejo de errores en la obtencion de parametros en la url
def validar_parametros(permanencia, precio, tipo_tarifa, potencia):
    errores = []

    # Validar permanencia: solo puede ser 0 o 1
    permanencia = str(permanencia)
    if permanencia not in ['0', '1']:
        errores.append("El parámetro 'permanencia' debe ser '0' o '1'.")

    # Validar precio: debe ser un float entre 0 y 1 (excluyendo 0 y 1)
    try:
        precio_float = float(precio)
        if not (0 < precio_float < 1):
            errores.append("El parámetro 'precio' debe ser un número entre 0 y 1, sin incluir los extremos.")
    except ValueError:
        errores.append("El parámetro 'precio' debe ser un número válido.")

    # Validar tipo_tarifa: solo puede ser 'fija' o 'variable', sin importar mayúsculas o minúsculas
    if tipo_tarifa.lower() not in ['fija', 'variable']:
        errores.append("El parámetro 'tipo_tarifa' debe ser 'fija' o 'variable'.")

    # Validar potencia: debe ser un número entre 1 y 20 (incluyendo ambos extremos)
    try:
        potencia_float = float(potencia)
        if not (1 <= potencia_float <= 20):
            errores.append("El parámetro 'potencia' debe ser un número entre 1 y 20, incluidos ambos extremos.")
    except ValueError:
        errores.append("El parámetro 'potencia' debe ser un número válido.")

    # Devolver errores concatenados si existen, o una cadena vacía si no hay errores
    return ' '.join(errores) if errores else ''