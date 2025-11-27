from flask import Flask, request
from redis import RedisError, Redis
from redis.cluster import RedisCluster, ClusterNode
from datetime import datetime
from keras.saving import load_model
from redis.sentinel import Sentinel
import os
import socket
import joblib
import numpy as np


# Tamaño de ventana para las predicciones y carga del modelo
WINDOW_SIZE = 24
model = load_model("models/modelo.keras")
scaler = joblib.load("models/scaler.pkl")


# Establecemos el umbral de error para clasificar anomalías
with open("models/threshold.txt", "r") as f:
    THRESHOLD = float(f.readlines(1)[0])



# --------------------REDIS-------------------------------------

# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# redis = Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)

# --------------------------------------------------------------



# --------------------REDIS SENTINEL----------------------------

# SENTINEL_HOST1 = os.getenv("SENTINEL_HOST1", "sentinel1")
# SENTINEL_HOST2 = os.getenv("SENTINEL_HOST2", "sentinel2")
# SENTINEL_HOST3 = os.getenv("SENTINEL_HOST3", "sentinel3")

# SENTINEL_PORT1 = int(os.getenv("SENTINEL_PORT1", 26379))
# SENTINEL_PORT2 = int(os.getenv("SENTINEL_PORT2", 26379))
# SENTINEL_PORT3 = int(os.getenv("SENTINEL_PORT3", 26379))

# sentinels_list = [(SENTINEL_HOST1, SENTINEL_PORT1),
#             (SENTINEL_HOST2, SENTINEL_PORT2),
#             (SENTINEL_HOST3, SENTINEL_PORT3)]

# sentinel = Sentinel(sentinels=sentinels_list, socket_timeout=0.1)

# master_info = sentinel.discover_master("mymaster")
# print(f"El maestro actual es {master_info}")

# redis = sentinel.master_for("mymaster", socket_timeout=0.1)

# --------------------------------------------------------------



# --------------------REDIS CLUSTER-----------------------------

h1 = os.getenv("REDIS_HOST1", "redis-node-1")
h2 = os.getenv("REDIS_HOST2", "redis-node-2")
h3 = os.getenv("REDIS_HOST3", "redis-node-3")

port = 6379

startup_nodes = [
    ClusterNode(h1, port),
    ClusterNode(h2, port),
    ClusterNode(h3, port)
]

redis = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True,
    skip_full_coverage_check=True,
    socket_timeout=5,
    socket_connect_timeout=5,
)


# --------------------------------------------------------------


redis.flushdb() 


# Instancia de la aplicación Flask 
FLASK_PORT = os.getenv("FLASK_PORT", 80)
app = Flask(__name__)



@app.route("/")
def hello():
    try:
        visits = redis.incr("counter")
    except RedisError as err:
        print(err)
        visits = "<i> Error: Hubo un problema con Redis, contador desactivado </i>"

    html = "<h3>Hello {hostname} </h3>" \
        "<b>Visits:</b> {visits}"
    
    return html.format(hostname=socket.gethostname(), visits=visits)


@app.route("/nuevo", methods=["GET"])
def nuevo():
    try:
        valor = float(request.args.get('dato'))
        redis.ts().add(key="values", timestamp="*", value=valor)
        
        return f"Nuevo valor introducido: {valor}"
    
    except ValueError as err:
        print(err)
        return "<i> dato debe ser un número! </i>"
    
    except RedisError as err:
        print(err)
        return "<h1> Error: Hubo un problema con Redis </h1>" \
        "<p>{err}</p>".format(err=err)
    
     

@app.route("/listar", methods=["GET"])
def listar():
    try:
        res = redis.ts().range("values", "-", "+")
        output = "<b> Hostname: </b> {hostname} <br/>"
        
        for r in res:
            timestamp = int(r[0]) / 1000
            value = r[1] 
            # Obtener el timestamp
            dt = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y, %H:%M:%S')
            output += f"</br>{dt} -------> {value}"

        return output.format(hostname=socket.gethostname())
    
    except RedisError as err:
        print(err)
        return "<h1> Error: Hubo un problema con Redis </h1>"\
            "<p>{err}</p>".format(err=err)


@app.route("/detectar", methods=["GET"])
def detectar():
    try:
        valor = float(request.args.get('dato'))
    except ValueError:
        return "<i> Error: dato debe ser un número </i>"
    
    # Añadimos el valor a la serie temporal
    redis.ts().add(key="values", timestamp='*', value=valor)

    try:
        size = redis.ts().info(key="values")["total_samples"]

        if size <= WINDOW_SIZE:
            
            return f"<i> No hay suficientes medidas: {size} medidas </i>"
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
                return f"<h1> Anomalía detectada! </h1>" \
                    f"Real: {valor}<br>" \
                    f"Predicción: {predicted_value:.2f}<br>" \
                    f"Error: {error:.2f}"
            else:
                return f"<h1>El valor es normal</h1>" \
                    f"Real: {valor}<br>" \
                    f"Predicción: {predicted_value:.2f}<br>" \
                    f"Error: {error:.2f}"
        
    except RedisError as err:
        print(err)
        return "<h1> Error: Hubo un problema con Redis </h1>"\
            "<p>{err}</p>".format(err=err)
    
    except Exception as err:
        print(err)
        return "<i> Ocurrió un error </i>"

def main():
    app.run(host="0.0.0.0", port=FLASK_PORT)

if __name__ == "__main__":
    main()