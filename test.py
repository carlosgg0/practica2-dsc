from time import sleep
import requests
import random

BASE_URL = "http://localhost:4000/"
N = 100

while True:
    try: 
        val = random.random()
        print("Introduciendo", val, "...")
        r = requests.get(BASE_URL + f"/nuevo?dato={val}")
        sleep(1)
    except ConnectionError:
        print("Hubo un error")
        exit(-1)
    except KeyboardInterrupt:
        print("\nSe ha interrumpido el programa")
        exit(0)
