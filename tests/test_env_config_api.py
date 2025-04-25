import unittest
from flask import Flask
from api.env_config_api import env_config_bp

class TestEnvConfigAPI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(env_config_bp)
        self.client = app.test_client()

    def test_get_all_env_vars(self):
        res = self.client.get("/api/env/all")
        self.assertEqual(res.status_code, 200)
        self.assertIn("MQTT_USERNAME", res.get_json())

    def test_update_env_var_allowed(self):
        res = self.client.post("/api/env/update", json={
            "key": "MQTT_USERNAME",
            "value": "testuser"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("updated", res.get_json()["message"].lower())

    def test_update_env_var_rejects_disallowed(self):
        res = self.client.post("/api/env/update", json={
            "key": "DISALLOWED_KEY",
            "value": "value"
        })
        self.assertEqual(res.status_code, 400)

    def test_update_env_var_missing_key(self):
        res = self.client.post("/api/env/update", json={"value": "v"})
        self.assertEqual(res.status_code, 400)

    def test_update_env_var_missing_value(self):
        res = self.client.post("/api/env/update", json={"key": "MQTT_PORT"})
        self.assertEqual(res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
