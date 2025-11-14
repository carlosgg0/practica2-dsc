from flask import Flask, request
from redis import Redis, RedisError
from datetime import datetime
import os
import socket


FLASK_PORT = os.getenv("FLASK_PORT", 80)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost") 


# Conexión con Redis
redis = Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)
redis.flushdb()

# Instancia de la aplicación Flask 
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


def main():
    app.run(host="0.0.0.0", port=FLASK_PORT)

if __name__ == "__main__":
    main()