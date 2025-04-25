"""
cert_upload_api.py

Blueprint for securely uploading MQTT certificate files.
Stores files to /certs and supports reload via SparkplugClient.
"""

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from src.utils.logger_module import print_error, log_info

cert_upload_bp = Blueprint("cert_upload", __name__)
ALLOWED_EXTENSIONS = {"crt", "pem", "key"}
CERT_DIR = os.path.join(os.getcwd(), "certs")

os.makedirs(CERT_DIR, exist_ok=True)

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@cert_upload_bp.route("/api/certs/upload", methods=["POST"])
def upload_certs():
    """
    Upload one or more TLS certificate files (.crt, .key, .pem).
    Saves them to /certs and triggers SparkplugClient reload.
    """
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files part in request"}), 400

        files = request.files.getlist("files")
        saved = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(CERT_DIR, filename)
                file.save(filepath)
                saved.append(filename)

        if not saved:
            return jsonify({"error": "No valid certificate files uploaded"}), 400

        # Trigger Sparkplug reload (via dependency injection later)
        if hasattr(request, "mqtt_client"):
            request.mqtt_client.reload_cert()

        log_info(f"Certificates uploaded: {saved}")
        return jsonify({"message": "Certificates uploaded", "files": saved}), 200

    except Exception as e:
        print_error("upload_certs", e)
        return jsonify({"error": "Certificate upload failed"}), 500
