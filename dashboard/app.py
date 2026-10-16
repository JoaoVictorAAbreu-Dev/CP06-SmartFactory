import os

import requests
from flask import Flask, render_template

app = Flask(__name__)
API_URL = os.getenv("API_URL", "http://api:5000/dados")


@app.get("/")
def index():
    reading = None
    status_message = None
    try:
        response = requests.get(API_URL, timeout=3)
        if response.status_code == 503:
            status_message = "Aguardando dados do ESP32"
        else:
            response.raise_for_status()
            data = response.json()
            if data.get("estado") not in ("NORMAL", "ALERTA"):
                raise ValueError("Estado recebido inválido")
            reading = data
    except (requests.RequestException, ValueError):
        status_message = "Aguardando dados do ESP32 — API indisponível"
    return render_template("index.html", reading=reading, status_message=status_message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
