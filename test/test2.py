from time import sleep
import requests
import random

BASE_URL = "http://"

# Introducir localhost o la IP deseada
address = input("Introduzca la dirección IP del equipo: ")

while True:
    try: 
        val = random.gauss(71.24, 8)
        print("Introduciendo", val, "...")
        r = requests.get(BASE_URL + address + f"/detectar?dato={val}")
        print(r.content)
        sleep(1)
    except ConnectionError:
        print("Hubo un error")
        exit(-1)
    except KeyboardInterrupt:
        print("\nSe ha interrumpido el programa")
        exit(0)
