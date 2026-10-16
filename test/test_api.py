import json
import unittest

from api.app import app, classify_state, on_message, parse_reading


class ReadingLogicTests(unittest.TestCase):
    def test_temperature_above_35_is_alert(self):
        self.assertEqual(classify_state(35.01), "ALERTA")

    def test_temperature_exactly_35_is_normal(self):
        self.assertEqual(classify_state(35), "NORMAL")

    def test_valid_reading_is_normalized_and_consistent_state_preserved(self):
        reading = parse_reading(json.dumps({"temperatura": 36, "umidade": 58, "estado": "ALERTA"}))
        self.assertEqual(reading, {"temperatura": 36.0, "umidade": 58.0, "estado": "ALERTA"})

    def test_invalid_reading_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_reading('{"temperatura": "quente", "umidade": 50, "estado": "NORMAL"}')

    def test_missing_state_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_reading('{"temperatura": 30, "umidade": 50}')

    def test_state_conflicting_with_temperature_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_reading('{"temperatura": 36, "umidade": 50, "estado": "NORMAL"}')


class ApiEndpointTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["LATEST_READING"] = None
        self.client = app.test_client()

    def test_returns_503_before_first_reading(self):
        response = self.client.get("/dados")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"mensagem": "Aguardando dados do ESP32"})

    def test_returns_latest_reading(self):
        app.config["LATEST_READING"] = {"temperatura": 29.5, "umidade": 61.0, "estado": "NORMAL"}
        response = self.client.get("/dados")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["estado"], "NORMAL")
        self.assertIsInstance(response.get_json()["temperatura"], (float, int))

    def test_mqtt_message_updates_latest_reading(self):
        class Message:
            payload = b'{"temperatura": 36, "umidade": 50, "estado": "ALERTA"}'

        on_message(None, None, Message())
        self.assertEqual(self.client.get("/dados").get_json()["estado"], "ALERTA")

    def test_invalid_mqtt_message_does_not_replace_latest_reading(self):
        original = {"temperatura": 29.5, "umidade": 61.0, "estado": "NORMAL"}
        app.config["LATEST_READING"] = original

        class Message:
            payload = b'{"temperatura": 39, "umidade": 45, "estado": "NORMAL"}'

        on_message(None, None, Message())
        self.assertEqual(self.client.get("/dados").get_json(), original)


if __name__ == "__main__":
    unittest.main()
