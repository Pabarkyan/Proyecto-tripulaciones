from flask import Flask, render_template, redirect, url_for, request
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return '<h1>Home</h1>'


@app.route("/tarifa_user", methods=['POST'])
def calculo():

    if request.method == 'POST':   # Con este condicional se redirigen directamente los datos desde la página
                                   # y se evita que las variables consumo y potencia tomen valores distintos a los esperados
        try:
            consumo = float(request.form['cons_ref'])
            potencia = float(request.form['cont_pot'])

        except ValueError as VE:
            return render_template("index.html", mensaje = "Vuelva a interntarlo e introduce números válidos y punto en lugar de coma")

    factura = calcular(consumo, potencia)

    global lista_tarif  # Se define global para que la siguiente página, /resultados, pueda leer esta información sin problema
    lista_tarif = []

    for index, key in enumerate(factura):
        lista_tarif.append(Tarifa_estable(index + 1, factura[key]))

    global cons_medio, pot_media
    cons_medio = round(100*((consumo/300) - 1), 1)
    pot_media = round(100*((potencia/4.6) - 1), 1)

    # Hemos definido el consumo energético promedio como 300 KWh y la potencia contratada media como 4.6 kW
    # Con esta función calculamos el porcentaje en que nuestro cliente supera o no alcanza esta media

    return redirect(url_for('resultados'))

def calcular(consumo, potencia):
    global precios_energia      # Se define global para que se puedan calcular tarifas en otros ámbitos de la aplicación
    precios_energia = sc.tarifa()   # Esto es un diccionario que contiene los precios del KWh

    # He automatizado los datos sobre el consumo, pero no los de la potencia contratada. Esto es porque además de ser un dato
    # más dificil de obtener con scraping en algunas páginas, también es un dato más estático que el precio de la energía en
    # término de consumo.

    factura = calcular_tarifa(consumo, potencia)

    return factura


def calcular_tarifa(consumo, potencia):
        global factura
        try:
            factura = {
                'Naturgy': round(consumo*precios_energia['Naturgy'] + 3*potencia, 2),
                'Iberdrola': round(consumo*precios_energia['Iberdrola'] + 3.3*potencia, 2),
                'Endesa': round(consumo*precios_energia['Endesa'] + 3.9*potencia, 2),
                'Repsol': round(consumo*precios_energia['Repsol'] + 4.8*potencia, 2),
                'EDP': round(consumo*precios_energia['EDP'] + 3.4*potencia, 2)
            }
        except NameError as NE:
            return render_template("index.html", mensaje="Ha surgido un error desconocido, vuelva a introducir los datos")

        return factura


@app.route("/resultados")
def resultados():
    return render_template("results.html", lista_tarifas=lista_tarif)


@app.route("/stats")   # Código para introducir datos en la BBDD, aunque ya tiene bastantes registros incluidos así que no debería ser necesario
def stats():
    clientes = []
    for i in range(0,100):
        potencia = r.gauss(4.6,2)
        consumo = r.gauss(300,120)  # El consumo medio no
        calcular_tarifa(consumo, potencia)
        clientes.append(Cliente(factura['Naturgy'], factura['Iberdrola'], factura['Endesa'], factura['Repsol'], factura['EDP']))
        db.sesion.add(clientes[i])

    db.sesion.commit()

    return redirect(url_for('stats_2'))


@app.route("/stats_2")
def stats_2():

    client_data = pd.read_sql_table("info_clientes", 'sqlite:///database/datos.db')
    media_clientes = client_data.mean().to_list()
    # A través de pandas creo una lista con los precios promedio de cada compañía. En este caso sólo calculo la media,
    # el único parámetro estadístico que puede tener cierto interés para el usuario final, pero podría calcular cualquiera
    # de las muchas posibilidades que ofrece pandas y mostrarlo en la web

    precio = []

    for i in range(0, 5):
        precio.append(round(100*((lista_tarif[i].KWh/media_clientes[i + 1]) - 1), 2))
        # Va de 1 a 6 porque el elemento 0 de media_clientes corresponde al id de la base de datos


    # Toda la información que se mostrará en la página final se encapsula en este diccionario, que luego se pasa al html
    # por medio del render_template

    medias = {
        "Consumo": cons_medio,
        "Potencia": pot_media,
        "Precio": precio
    }
    return render_template("stats.html", means=medias, lista_tarifas=lista_tarif)

if __name__ == "__main__":
    app.run(debug=True)
    db.Base.metadata.create_all(db.engine)

    



