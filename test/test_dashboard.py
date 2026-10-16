import unittest
from unittest.mock import Mock, patch

from dashboard.app import app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("dashboard.app.requests.get")
    def test_api_503_displays_waiting_without_fake_measurements(self, get):
        get.return_value = Mock(status_code=503)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aguardando dados do ESP32", response.get_data(as_text=True))
        self.assertNotIn("0.0 °C", response.get_data(as_text=True))

    @patch("dashboard.app.requests.get")
    def test_dashboard_renders_api_measurements_and_state(self, get):
        result = Mock(status_code=200)
        result.json.return_value = {"temperatura": 36.2, "umidade": 55.0, "estado": "ALERTA"}
        get.return_value = result
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("36.2", html)
        self.assertIn("55.0", html)
        self.assertIn("ALERTA", html)

    @patch("dashboard.app.requests.get")
    def test_api_unavailable_displays_waiting_state(self, get):
        import requests
        get.side_effect = requests.ConnectionError("offline")
        response = self.client.get("/")
        self.assertIn("Aguardando dados", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
