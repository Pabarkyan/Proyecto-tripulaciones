import pandas as pd
import pickle

datos_medias = pd.read_csv('data/tarifas_limpias.csv')

# los valores de tarifa pueden ser 'fijo' y 'variable'
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



def W_clarifications(potencia: float):
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

def fee_clasifications(tarifa):
    tarifa_bool = False

    if tarifa == 'variable':
        tarifa_bool = True
    else:
        tarifa_bool = False

    return tarifa_bool # el valor es 0.0 o 1.0


# convertir los datos del user en df para meterlo en el modelo de kmeans

# precio: valor entre 0 y 1
# tarifa: valores: 'fijo' o 'variable'
# potencia: entre 0 y 20
# permanencia: 0 o 1
def user_information(precio, tarifa, potencia, permanencia):
    information = pd.DataFrame()
    information['precio_€/kWh'] = [precio]

    prices = price_types(fee_clasifications(tarifa)) # ya que tarifa tiene que ser un bool no un variable o fija
    information = pd.concat([information, prices], axis=1)

    information['permanencia'] = [float(permanencia)] # los datos tienen que ser identicos a la entrada del modelo

    information['tipo_tarifa_variable'] = [float(fee_clasifications(tarifa))]

    tarifa_potencia = W_clarifications(potencia)
    information = pd.concat([information, tarifa_potencia], axis=1)

    return information



# aplicamos el modelo para ver en que cluster esta los datos del usuario
def cluster_clasification(user_info: pd.DataFrame):
    with open('data/modelo_kmeans_scaler.pkl', 'rb') as f:
        data = pickle.load(f)
        scaler = data['scaler']
        kmeans = data['kmeans']

    user_info_scaled = scaler.transform(user_info)
    cluster_asignado = kmeans.predict(user_info_scaled) 
    return cluster_asignado


# filtramos los datos con el cluster obtenido, con los datos (X)
def filter_data(cluster):
