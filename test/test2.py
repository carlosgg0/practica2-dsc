from time import sleep
import requests
import random

BASE_URL = "http://localhost/"
N = 100

while True:
    try: 
        val = random.gauss(71.24, 8)
        print("Introduciendo", val, "...")
        r = requests.get(BASE_URL + f"/detectar?dato={val}")
        print(r.content)
        sleep(1)
    except ConnectionError:
        print("Hubo un error")
        exit(-1)
    except KeyboardInterrupt:
        print("\nSe ha interrumpido el programa")
        exit(0)
