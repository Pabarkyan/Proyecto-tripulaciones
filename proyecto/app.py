from flask import Flask, request, redirect, url_for, session, jsonify
from functions import user_information, filter_data

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesaria para manejar sesiones

# Ruta Home básica
@app.route('/')
def home():
    return 'Bienvenido a CholloLuz'

# Ruta 'information' que acepta parámetros a través de la URL (GET)
@app.route('/information')
def information():
    # Obtener los parámetros de la URL
    permanencia = request.args.get('permanencia')
    precio = request.args.get('precio')
    tipo_tarifa = request.args.get('tipo_tarifa')
    potencia = request.args.get('potencia')

    # Verificar si todos los parámetros están presentes
    if not all([permanencia, precio, tipo_tarifa, potencia]):
        return 'Faltan parámetros. Debes proporcionar permanencia, precio, tipo_tarifa y potencia.', 400

    # Guardar los parámetros en la sesión para no exponerlos en la URL de la página redirigida
    session['permanencia'] = permanencia
    session['precio'] = precio
    session['tipo_tarifa'] = tipo_tarifa
    session['potencia'] = potencia

    # Redirigir a la ruta '/resultado' sin los parámetros en la URL
    return redirect(url_for('resultado'))

# Ruta de destino de la redirección (GET)
@app.route('/resultado')
def resultado():
    # Obtener los parámetros almacenados en la sesión
    permanencia = int(session.get('permanencia'))
    precio = float(session.get('precio'))
    tipo_tarifa = str(session.get('tipo_tarifa'))
    potencia = float(session.get('potencia'))

    # Verificar que los datos estén en la sesión
    if not all([permanencia, precio, tipo_tarifa, potencia]):
        return 'No se encontraron los parámetros necesarios en la sesión.', 400
    
    user_info = user_information(precio=precio, tarifa=tipo_tarifa, potencia=potencia, permanencia=permanencia)
    results = filter_data(user_info=user_info)

    results_json = results.to_dict(orient='records')

    return jsonify(results_json) 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
