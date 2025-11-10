from sqlite3.dbapi2 import Timestamp
from flask import Flask, jsonify, request
from redis import Redis, RedisError
import os
import socket


# Connect to Redis
REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
print("REDIS_HOST: " + REDIS_HOST)
redis = Redis(host=REDIS_HOST, db=1, socket_connect_timeout=2, socket_timeout=2)


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


@app.route("/nuevo/<valor>")
def store_data(valor):
    redis.ts().add(key="values", timestamp='*', value=valor)
    return "hola"
        
@app.route("/listar")
def listar():
    res = redis.ts().range("values", "-", "+")
    output = ""
    for i in res:
        output += str(i[1]) + "\n"
    return output

if __name__ == "__main__":
    PORT = os.getenv('PORT', 8080)
    print("PORT: "+str(PORT))
    app.run(host='0.0.0.0', port=PORT)