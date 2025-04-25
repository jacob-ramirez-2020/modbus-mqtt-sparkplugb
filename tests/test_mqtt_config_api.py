# File: tests/test_mqtt_config_api.py

import unittest
from unittest.mock import patch
from flask import Flask
from api.mqtt_config_api import mqtt_config_bp


class TestMQTTSecurityAPI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(mqtt_config_bp)
        self.client = app.test_client()

    @patch("api.mqtt_config_api.get_sparkplug_client_instance")
    def test_update_mqtt_security_valid(self, mock_client):
        mock_instance = mock_client.return_value
        mock_instance.reload_connection.return_value = None

        response = self.client.post("/api/mqtt/security", json={
            "protocol": "tls",
            "port": 8883,
            "tls_mode": "tls_insecure",
            "username": "test",
            "password": "secret"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response.get_json()["message"])

    def test_update_mqtt_security_invalid_payload(self):
        response = self.client.post("/api/mqtt/security", json={})
        self.assertEqual(response.status_code, 200)  # should still work with defaults
    
    @patch("api.mqtt_config_api.get_sparkplug_client_instance")
    @patch("api.mqtt_config_api.safe_env_write")
    def test_post_valid_env_key(self, mock_env_write, mock_get_client):
        mock_client = unittest.mock.Mock()
        mock_get_client.return_value = mock_client

        response = self.client.post("/api/mqtt/env", json={
            "key": "MQTT_USERNAME",
            "value": "testuser"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("MQTT_USERNAME updated", response.get_json()["message"])
        mock_env_write.assert_called_once_with("MQTT_USERNAME", "testuser")
        mock_client.reload_connection.assert_called_once()

    def test_post_invalid_env_key(self):
        response = self.client.post("/api/mqtt/env", json={
            "key": "INVALID_KEY",
            "value": "value"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid key", response.get_json()["error"])

    def test_post_missing_params(self):
        response = self.client.post("/api/mqtt/env", json={"key": "MQTT_USERNAME"})
        self.assertEqual(response.status_code, 400)

    @patch("api.mqtt_config_api.os.environ.get", side_effect=lambda k, d=None: "test" if k.startswith("MQTT_") else d)
    def test_get_env_config(self, _):
        response = self.client.get("/api/mqtt/env")
        self.assertEqual(response.status_code, 200)
        self.assertIn("MQTT_USERNAME", response.get_json())


unittest.main(argv=[""], exit=False)

if __name__ == "__main__":
    unittest.main()
