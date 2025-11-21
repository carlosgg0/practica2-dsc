# Instrucciones de Uso

## Configuración del entorno de Python

Si se desea, se pueden instalar las dependencias necesarias para ejecutar los scripts de tests:

```console
pip install requirements.txt
````

## Ejecución de la parte 1

Para el despliegue de la parte 1 de la práctica, se debe descomentar la línea que hace referencia a la imagen de dicha parte en el fichero `compose.yaml`. La configuración de grafana es exactamente la misma que la que se proporciona en el campus virtual.

Los comandos para el despliegue mediante docker swarm serían los siguientes:

```console
docker swarm init
docker stack deploy -c compose.yaml up
```

Si se desea se puede automatizar la inserción de datos mediante el fichero `test1.py`.

## Ejecución de la parte 2

La ejecución de la parte 2 es análoga a la anterior, pero se debe referenciar en el fichero `compose.yaml` (descomentar la linea donde se hace referencia a dicha imagen).

## Ejecución de la parte 3

La ejecución de la parte 3 se puede hacer gracias al fichero `docker-compose-sentinel.yaml`.

```console
docker compose -f docker-compose-sentinel.yaml up
```

