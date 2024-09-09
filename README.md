# Chollo-Luz

_El siguiente repo consiste en un comparador de la tarifa de la luz de un usuario con las de un mercado, ofreciendole solo las mejores opciones, mediante una API en Flask_

## Descripción 🚀
 
Este proyecto consta de una API en Flask donde en una url el usuario añade informacion sobre su tarifa de la luz (permanencia, tipo de tarifa, precio, potencia contratada) y le redirige a una página de resultados monstrandoles todos los resultados que supongan una mejora en el precio. Los resultados han sido clasificados mediante un modelo Kmeans que clasifica por categorías las tarifas del dataset y le muestra al usuario todas las tarifas que pertenezcan a su tipo de grupo y filtra por las mas baratas.

# Instalación 📋

_Que cosas necesitas para instalar el software y como instalarlas_

## 1. Clona este repositorio

''
`git clone https://github.com/Pabarkyan/Proyecto-tripulaciones.git`

`cd [nombre del repo]`
''

## 2. Crear y activar el entorno virtual

`python -m venv venv`

`source venv/bin/activate`  # O `venv\Scripts\activate` en Windows`

`pip install -r requirements.txt`

## 3. Ejecutar la API

`cd proyecto`

`python app.py`


## Authors (github usernames):
    🐙 Pabarkyan
    🐙 earribasds
    🐙 sharkinvestor 
    🐙 ShirleiO 

### Valores de la url 'information':

_Ejemplo: information?permanencia=1&precio=0.23&tipo_tarifa=fija&potencia=14_

##### Condiciones:
    - Permanencia: solo puede tomar el valor 0 o 1
    - precio: valores entre 0 y 1 sin incluir
    - tipo_tarifa: 'fija' o 'variable' (no es sensible a mayusculas)
    - potencia: valores entre 1 y 20, ambos inclusive
