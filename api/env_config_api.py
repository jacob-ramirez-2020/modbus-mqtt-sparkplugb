"""
env_config_api.py

Flask blueprint to get or update secure environment (.env) config.
"""

from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os

from src.utils.logger_module import print_error, log_info
from src.mqtt.mqtt_client import get_sparkplug_client_instance

env_config_bp = Blueprint("env_config_bp", __name__)

ENV_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".env"
)

ALLOWED_KEYS = {
    "MQTT_USERNAME",
    "MQTT_PASSWORD",
    "MQTT_BROKER",
    "MQTT_PORT",
    "MQTT_TLS_MODE"
}

def _read_env_file():
    env_vars = {}
    try:
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, "r", encoding='utf-8') as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        env_vars[k] = v
    except Exception as e:
        print_error("_read_env_file", e)
    return env_vars

def _write_env_file(updated_vars):
    try:
        current_vars = _read_env_file()
        current_vars.update(updated_vars)
        with open(ENV_FILE_PATH, "w", encoding='utf-8') as f:
            for k, v in current_vars.items():
                f.write(f"{k}={v}\\n")
        load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
        return True
    except Exception as e:
        print_error("_write_env_file", e)
        return False

@env_config_bp.route("/api/env/update", methods=["POST"])
def update_env_var():
    try:
        data = request.get_json()
        key = data.get("key")
        value = data.get("value")

        if not key or not value:
            return jsonify({"error": "Missing key or value"}), 400

        if key not in ALLOWED_KEYS:
            return jsonify({"error": f"Key '{key}' is not allowed"}), 400

        if _write_env_file({key: value}):
            log_info(f"[ENV] Updated: {key}")

            mqtt = get_sparkplug_client_instance()
            if mqtt:
                mqtt.reload_connection()

            return jsonify({"message": f"{key} updated"}), 200
        else:
            return jsonify({"error": "Failed to update .env"}), 500
    except Exception as e:
        print_error("update_env_var", e)
        return jsonify({"error": "Unexpected error"}), 500

@env_config_bp.route("/api/env/all", methods=["GET"])
def get_all_env_vars():
    try:
        env = _read_env_file()
        result = {}
        for k, v in env.items():
            if "PASSWORD" in k or "SECRET" in k or "KEY" in k:
                result[k] = "****"
            else:
                result[k] = v
        return jsonify(result), 200
    except Exception as e:
        print_error("get_all_env_vars", e)
        return jsonify({"error": "Failed to fetch env vars"}), 500
