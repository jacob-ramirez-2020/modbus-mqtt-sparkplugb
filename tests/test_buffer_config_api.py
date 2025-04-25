import unittest
from unittest.mock import patch
from flask import Flask
from api.blueprints.log_config_bp import log_config_bp
from api.blueprints.buffer_config_bp import buffer_config_bp


class TestBufferConfigAPI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(buffer_config_bp)
        self.client = app.test_client()

    @patch("api.log_buffer_api.set_max_buffer_size_limit")
    def test_update_max_buffer_size_valid(self, mock_set_limit):
        response = self.client.post(
            "/api/buffer/max_size", json={"max_bytes": 2097152}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response.get_json()["message"])

    def test_update_max_buffer_size_invalid(self):
        response = self.client.post(
            "/api/buffer/max_size", json={"max_bytes": -10}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    @patch("api.log_buffer_api.MAX_BUFFER_SIZE_BYTES", 2097152)
    def test_get_buffer_config(self):
        response = self.client.get("/api/buffer/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["max_bytes"], 2097152)


if __name__ == "__main__":
    unittest.main()
