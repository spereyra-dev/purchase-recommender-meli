"""Run flask app."""

from flask import Flask, request, jsonify
import json
import urllib.parse
import requests
import openai

app = Flask(__name__)

def buscar_productos(query):
    encoded_query = urllib.parse.quote(query)
    print(encoded_query)
    url = f"http://api.mercadolibre.com/sites/MLU/search?q={encoded_query}"
    response = requests.get(url)
    return json.loads(response.text)["results"]


def generar_recomendacion(input_text,apiKey):
    openai.api_key = apiKey
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "Pretend that you are an ecommerce helper and can identify user needs based on a prompt given by them. You have to evaluate their needs and give back an array of specific products to search on your website. return ONLY a list of ideas, in a python array format, and with a temperature hyperparamether of 0.1. don't write any text before or after the array"
            },
            {
                "role": "user",
                "content": input_text
            }
        ],
        "temperature": 0.0
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {apiKey}",
        },
        json=body,
        timeout=360,
    )
    data = response.json()
    print(data) 
    return data['choices'][0]['message']['content']
    


@app.route('/recomendaciones', methods=['POST'])
def obtener_recomendaciones():
    input_text = request.json['input_text']
    apiKey = request.json['api_key']
    recomendacion = generar_recomendacion(input_text,apiKey)
    resultados = []
    for k, recomend in enumerate(eval(recomendacion)):
        productos = buscar_productos(recomendacion[k])
        if any(producto.get('title') and producto.get('price') and producto.get('permalink') for producto in productos):
            resultado = {
                "categoria": recomend.capitalize(),
                "productos": []
            }
            for producto in productos[:5]:
                title = producto.get('title') or producto.get(
                    'buy_box_winner', {}).get('title')
                price = producto.get('price') or producto.get(
                    'buy_box_winner', {}).get('price')
                permalink = producto.get('permalink') or producto.get(
                    'buy_box_winner', {}).get('permalink')
                free_shipping = producto.get('shipping', {}).get('free_shipping') or producto.get(
                    'buy_box_winner', {}).get('shipping', {}).get('free_shipping', 'Desconocido')
                if title and price and permalink:
                    producto_dict = {
                        "nombre": title,
                        "precio": price,
                        "envio_gratuito": free_shipping,
                        "enlace": permalink
                    }
                    resultado["productos"].append(producto_dict)
            resultados.append(resultado)
    response = {
        "input_text": input_text,
        "content": {
            "resultados": resultados
        }
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run()
