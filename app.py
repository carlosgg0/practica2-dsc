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

# Connect to redis
redis = Redis(host=REDIS_HOST, db=1, socket_connect_timeout=2, socket_timeout=2)
redis.flushdb()

# Create Flask application 
app = Flask(__name__)

# Load the model and the scaler
model = load_model("modelo.keras")
scaler = joblib.load("scaler.pkl")

# The array in which we will store exactly WINDOW_SIZE measurements
# to make predictions
measures = []


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
    valor = request.args.get('dato')
    try:
        redis.ts().add(key="values", timestamp='*', value=valor)
    except RedisError:
        return "<i> Something went bad, please try again </i>"
    
    size = redis.ts().info(key="values")["total_samples"]
    last_timestamp = redis.ts().get(key="values")[0]
    
    print("Size:", size)
    print("Last timestamp:", last_timestamp)

    if size <= WINDOW_SIZE:
        measures = np.append(measures, valor)
        return "<i> There are not enough measures! </i>"
    else:  
        measures = measures[-WINDOW_SIZE : ]
        print(measures.shape)
        prediction = model.predict(measures)
        return str(prediction)
    

def main():
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()