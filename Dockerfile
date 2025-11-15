FROM python:3.12-slim

WORKDIR /app/models

COPY models/ /app/models/

WORKDIR /app

COPY src/ /app 
COPY requirements.txt /app

RUN pip install -r requirements.txt

EXPOSE 80

ENV REDIS_HOST=host.docker.internal

CMD ["python", "app.py"]