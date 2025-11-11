from sqlite3.dbapi2 import Timestamp
from flask import Flask, jsonify, request
from redis import Redis, RedisError
import os
import socket


# Connect to Redis
REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
print("REDIS_HOST: " + REDIS_HOST)
redis = Redis(host=REDIS_HOST, db=1, socket_connect_timeout=2, socket_timeout=2)

redis.flushdb()

# Create Flask application 
app = Flask(__name__)


@app.route("/")
def hello():
    try:
        visits = redis.incr("counter")
    except RedisError:
        visits = "<i>cannot connect to Redis, counter disabled</i>"

    html = "<h3>Hello {name}!</h3>" \
           "<b>Hostname:</b> {hostname}<br/>" \
           "<b>Visits:</b> {visits}"
    return html.format(name=os.getenv("NAME", "world"), hostname=socket.gethostname(), visits=visits)


@app.route("/nuevo", methods=["GET"])
def store_data():
    valor = request.args.get('dato')
    try:
        redis.ts().add(key="values", timestamp='*', value=valor)
    except RedisError:
        return "<i> Cannot connect to Redis! </i>"
        
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


if __name__ == "__main__":
    PORT = os.getenv('PORT', 8080)
    print("PORT: "+str(PORT))
    app.run(host='0.0.0.0', port=PORT)