import requests
import random

BASE_URL = "http://localhost:4000/"
N = 100
rand_nums = [random.random() for _ in range(N)]

for val in rand_nums:
    try:
        r = requests.get(BASE_URL + f"/nuevo?dato={val}")
    except ConnectionError:
        print("Hubo un error")
        exit(-1)

print("Todos los datos han sido introducidos correctamente!")