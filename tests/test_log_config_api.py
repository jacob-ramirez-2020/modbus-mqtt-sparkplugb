import unittest
from unittest.mock import patch, mock_open
from flask import Flask
from api.blueprints.log_config_bp import log_config_bp
from api.blueprints.buffer_config_bp import buffer_config_bp



class TestLogConfigAPI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(log_config_bp)
        self.client = app.test_client()

    @patch("api.log_config_api.set_max_log_file_size")
    def test_update_max_log_size_valid(self, mock_set_size):
        response = self.client.post(
            "/api/logs/max_size", json={"bytes_size": 1048576}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_max_log_size_invalid(self):
        response = self.client.post("/api/logs/max_size", json={"bytes_size": -1})
        self.assertEqual(response.status_code, 400)

    @patch("api.log_config_api.set_max_log_files")
    def test_update_max_log_files_valid(self, mock_set_count):
        response = self.client.post("/api/logs/max_files", json={"count": 10})
        self.assertEqual(response.status_code, 200)

    def test_update_max_log_files_invalid(self):
        response = self.client.post("/api/logs/max_files", json={"count": 0})
        self.assertEqual(response.status_code, 400)

    @patch("api.log_config_api.set_log_level")
    def test_set_log_level_valid(self, mock_set_level):
        response = self.client.post("/api/logs/level", json={"level": "DEBUG"})
        self.assertEqual(response.status_code, 200)

    def test_set_log_level_invalid(self):
        response = self.client.post("/api/logs/level", json={"level": "INVALID"})
        self.assertEqual(response.status_code, 400)

    @patch("api.log_config_api.get_log_level", return_value="DEBUG")
    @patch("api.log_config_api.MAX_BYTES", 1024)
    @patch("api.log_config_api.BACKUP_COUNT", 5)
    def test_get_log_config(self, mock_get_log_level):
        response = self.client.get("/api/logs/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["log_level"], "DEBUG")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="line1\\nline2\\n")
    def test_get_log_tail(self, mock_file, mock_exists):
        response = self.client.get("/api/logs/tail?lines=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("lines", response.get_json())

    @patch("os.listdir", return_value=["log.log", "log2.log"])
    @patch("os.path.exists", return_value=True)
    def test_list_log_files(self, mock_exists, mock_listdir):
        response = self.client.get("/api/logs/files")
        self.assertEqual(response.status_code, 200)
        self.assertIn("log.log", response.get_json())

    @patch("os.path.isfile", return_value=True)
    @patch("api.log_config_api.send_from_directory")
    def test_download_log_file(self, mock_send, mock_isfile):
        mock_send.return_value = "file contents"
        response = self.client.get("/api/logs/download/log.log")
        self.assertEqual(response.status_code, 200)

    @patch("os.path.isfile", return_value=False)
    def test_download_log_file_not_found(self, mock_isfile):
        response = self.client.get("/api/logs/download/invalid.log")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
