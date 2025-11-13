from flask import Flask, request
import joblib
from redis import Redis, RedisError
import os
import socket
import keras
from keras.models import Sequential
from keras.saving import load_model
import numpy as np
import pandas as pd


WINDOW_SIZE = 24
PORT = os.getenv("PORT", 80)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

with open("threshold.txt", "r") as f:
    THRESHOLD = float(f.readlines(1)[0]) 


# Connect to redis
redis = Redis(host=REDIS_HOST, db=1, socket_connect_timeout=2, socket_timeout=2)
redis.flushdb()

# Create Flask application 
app = Flask(__name__)

# Load the model and the scaler
model = load_model("modelo.keras")
scaler = joblib.load("scaler.pkl")

@app.route("/")
def hello():
    try:
        visits = redis.incr("counter")
    except RedisError:
        visits = "<i>cannot connect to Redis, counter disabled</i>"

    html = "<h3>Hello {name}!</h3>" \
        "<b>Hostname:</b> {hostname}<br/>" \
        "<b>Visits:</b> {visits}"
    
    return html.format(name="world", hostname=socket.gethostname(), visits=visits)


@app.route("/nuevo", methods=["GET"])
def store_data():
    valor = request.args.get('dato')
    try:
        redis.ts().add(key="values", timestamp='*', value=valor)
    except RedisError:
        return "<i> Cannot connect to Redis </i>"
        
    return "<h1>Nuevo valor introducido</h1>" 
        
        
@app.route("/listar")
def listar():
    try:
        res = redis.ts().range("values", "-", "+")

        output = "<b> Hostname: </b> {hostname} <br/>"
        for i in res:
            output += str(i[1]) + "<br/>"

        return output.format(hostname=socket.gethostname())
    
    except RedisError as err:
        print(err)
        return "<i> There's no data to display! </i>"


@app.route("/detectar", methods=["GET"])
def detectar():
    try:
        # Comprobamos que dato sea un valor numérico
        valor = float(request.args.get('dato'))
    except ValueError:
        return "<i> Error: dato must be a number </i>"
    
    # Añadimos el valor a la serie temporal
    redis.ts().add(key="values", timestamp='*', value=valor)

    try:
        size = redis.ts().info(key="values")["total_samples"]
        
        if size <= WINDOW_SIZE:
            
            return f"<i> There are not enough measures! {size} measures </i>"
        else:  
            # Consultamos las últimas WINDOW_SIZE mediciones para dar una predicción
            # Nótese que no cogemos el último valor, pues este es el valor real a predecir
            data = redis.ts().revrange("values", "-", "+", count=WINDOW_SIZE + 1)[:-1] 
            data.reverse()
            
            measures = np.array([float(val[1]) for val in data])

            # Aplicamos un escalado de los datos
            measures_scaled = scaler.transform(measures.reshape(-1, 1))

            prediction_input = measures_scaled.reshape(1, WINDOW_SIZE, 1)
            
            # Realizamos la predicción teniendo en cuenta las medidas
            prediction_scaled = model.predict(prediction_input)
            predicted_value = scaler.inverse_transform(prediction_scaled)[0][0]

            # Calculamos el error cometido para ver si es una anomalía
            error = abs(valor - predicted_value)
            
            if error > THRESHOLD:
                return f"<h1> ANOMALY DETECTED! </h1>" \
                    f"Actual: {valor}<br>" \
                    f"Predicted: {predicted_value:.2f}<br>" \
                    f"Error: {error:.2f}"
            else:
                return f"<h1>Value is Normal</h1>" \
                    f"Actual: {valor}<br>" \
                    f"Predicted: {predicted_value:.2f}<br>" \
                    f"Error: {error:.2f}"
        
    except RedisError as e:
        print(e)
        return "<i> Something went bad with Redis, please try again </i>"
    except Exception as e:
        print(e.with_traceback())
        return "<i> An error ocurred </i>"

def main():
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()