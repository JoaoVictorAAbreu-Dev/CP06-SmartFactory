#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHT_PIN 4
#define DHT_TYPE DHT22
#define LED_GREEN_PIN 18
#define LED_RED_PIN 19

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASSWORD = "";
const char *MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
const char *MQTT_TOPIC = "edge/2ano/turma-nao-informada/cp06/equipe-b9c1a2/dados";
const char *MQTT_CLIENT_ID = "cp06-esp32-equipe-b9c1a2";
const unsigned long PUBLISH_INTERVAL_MS = 5000;

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
unsigned long lastPublish = 0;

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" conectado");
}

void connectMqtt() {
  while (!mqtt.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (mqtt.connect(MQTT_CLIENT_ID)) {
      Serial.println(" conectado");
    } else {
      Serial.printf(" falhou (estado %d); nova tentativa em 2 s\n", mqtt.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  dht.begin();
  WiFi.mode(WIFI_STA);
  connectWiFi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();

  const unsigned long now = millis();
  if (now - lastPublish < PUBLISH_INTERVAL_MS) return;
  lastPublish = now;

  const float temperature = dht.readTemperature();
  const float humidity = dht.readHumidity();
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Falha na leitura do DHT22; amostra descartada");
    return;
  }

  // A decisão é local na borda: umidade não participa da regra de alerta.
  const bool alert = temperature > 35.0f;
  digitalWrite(LED_RED_PIN, alert ? HIGH : LOW);
  digitalWrite(LED_GREEN_PIN, alert ? LOW : HIGH);
  const char *state = alert ? "ALERTA" : "NORMAL";

  char payload[128];
  snprintf(payload, sizeof(payload), "{\"temperatura\":%.1f,\"umidade\":%.1f,\"estado\":\"%s\"}", temperature, humidity, state);
  const bool published = mqtt.publish(MQTT_TOPIC, payload);
  Serial.printf("T=%.1f C | U=%.1f %% | %s | MQTT %s\n", temperature, humidity, state, published ? "OK" : "falhou");
}
