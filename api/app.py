import json
import math
import os
import threading

import paho.mqtt.client as mqtt
from flask import Flask, jsonify

app = Flask(__name__)
app.config["LATEST_READING"] = None
_reading_lock = threading.Lock()

BROKER_HOST = os.getenv("MQTT_BROKER", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "edge/2ano/2CCPH/cp06/equipe-b9c1a2/dados")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "cp06-api-equipe-b9c1a2")


def classify_state(temperature):
    return "ALERTA" if temperature > 35.0 else "NORMAL"


def parse_reading(payload):
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("A mensagem MQTT deve ser um objeto JSON")
    required_fields = {"temperatura", "umidade", "estado"}
    if not required_fields.issubset(data):
        raise ValueError("Mensagem MQTT deve conter temperatura, umidade e estado")
    temperature = float(data["temperatura"])
    humidity = float(data["umidade"])
    state = data["estado"]
    if not math.isfinite(temperature) or not math.isfinite(humidity):
        raise ValueError("Medições devem ser números finitos")
    if not 0 <= humidity <= 100:
        raise ValueError("Umidade fora do intervalo de 0 a 100")
    if not isinstance(state, str) or state not in ("NORMAL", "ALERTA"):
        raise ValueError("Estado deve ser NORMAL ou ALERTA")
    expected_state = classify_state(temperature)
    if state != expected_state:
        raise ValueError("Estado recebido não corresponde à temperatura")
    return {
        "temperatura": temperature,
        "umidade": humidity,
        "estado": state,
    }


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(MQTT_TOPIC, qos=0)
        app.logger.info("Inscrito no tópico MQTT %s", MQTT_TOPIC)
    else:
        app.logger.error("Falha ao conectar ao MQTT: %s", reason_code)


def on_message(client, userdata, message):
    try:
        reading = parse_reading(message.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        app.logger.warning("Mensagem MQTT inválida descartada: %s", exc)
        return
    with _reading_lock:
        app.config["LATEST_READING"] = reading


@app.get("/dados")
def get_dados():
    with _reading_lock:
        reading = app.config.get("LATEST_READING")
    if reading is None:
        return jsonify(mensagem="Aguardando dados do ESP32"), 503
    return jsonify(reading), 200


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect_async(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    return client


if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000)
