from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
from api.blueprints.upload_cert_bp import cert_upload_bp
from src.utils.logger_module import print_error, log_info

CERT_FOLDER = "certs"
ALLOWED_EXTENSIONS = {"crt", "pem", "key"}

os.makedirs(CERT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@cert_upload_bp.route("/api/certs/upload", methods=["POST"])
def upload_cert():
    try:
        file = request.files["file"]
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        path = os.path.join(CERT_FOLDER, filename)
        file.save(path)

        log_info(f"Uploaded cert: {filename}")
        return jsonify({"message": "Uploaded successfully"}), 200
    except Exception as e:
        print_error("upload_cert", e)
        return jsonify({"error": "Upload failed"}), 500
