import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.cert_upload_api import cert_upload_bp

class TestCertUploadAPI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(cert_upload_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("api.cert_upload_api.request")
    def test_upload_valid_files(self, mock_request):
        mock_file = MagicMock()
        mock_file.filename = "client.crt"
        mock_file.save = MagicMock()

        mock_request.files = {"files": [mock_file]}
        mock_request.files.getlist = lambda x: [mock_file]
        mock_request.mqtt_client = MagicMock()

        response = self.client.post("/api/certs/upload")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Certificates uploaded", response.get_data(as_text=True))

    @patch("api.cert_upload_api.request")
    def test_upload_invalid_file_type(self, mock_request):
        mock_file = MagicMock()
        mock_file.filename = "malicious.exe"

        mock_request.files = {"files": [mock_file]}
        mock_request.files.getlist = lambda x: [mock_file]

        response = self.client.post("/api/certs/upload")
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
