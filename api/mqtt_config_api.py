"""
mqtt_config_api.py

Flask Blueprint to dynamically update MQTT security settings
(e.g., TLS mode, port, credentials) and reload the SparkplugClient
connection with the new configuration.
"""

import os
from flask import Blueprint, jsonify, request
from dotenv import set_key
from src.utils.logger_module import print_error, log_info
from src.mqtt.mqtt_client import get_sparkplug_client_instance
from src.utils.secrets_manager import (
    get_secure_config,
    update_env_variable
)

mqtt_config_bp = Blueprint("mqtt_config_api", __name__)

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


@mqtt_config_bp.route("/api/mqtt/status", methods=["GET"])
def get_mqtt_env_status():
    return jsonify(get_secure_config())

@mqtt_config_bp.route("/api/mqtt/security", methods=["POST"])
def update_mqtt_security():
    """
    Update MQTT connection settings dynamically from a POST payload.

    JSON payload should include:
    {
        "protocol": "tcp" | "tls",
        "port": 1883 | 8883,
        "tls_mode": "none" | "tls_insecure" | "tls_with_ca" | "tls_with_cert",
        "username": "user",
        "password": "pass",
    }

    Returns:
        JSON success or error message.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Missing payload"}), 400

        # Validate and apply .env updates
        updates = {
            "MQTT_PROTOCOL": data.get("protocol", "tcp"),
            "MQTT_PORT": str(data.get("port", 1883)),
            "MQTT_TLS_MODE": data.get("tls_mode", "none"),
            "MQTT_USERNAME": data.get("username", ""),
            "MQTT_PASSWORD": data.get("password", "")
        }

        for key, value in updates.items():
            set_key(ENV_FILE, key, value)

        # Reload SparkplugClient connection with new settings
        client = get_sparkplug_client_instance()
        client.reload_connection()

        log_info(f"[MQTT] Security config updated: {updates}")
        return jsonify({"message": "MQTT security configuration updated"}), 200

    except Exception as e:
        print_error("update_mqtt_security", e)
        return jsonify({"error": "Failed to update MQTT config"}), 500

@mqtt_config_bp.route("/api/mqtt/update", methods=["POST"])
def update_mqtt_env():
    """
    Update MQTT-related environment variable.

    JSON Payload:
    {
        "key": "MQTT_USERNAME",
        "value": "newuser"
    }
    """
    try:
        data = request.get_json()
        key = data.get("key")
        value = data.get("value")

        # Optional: Validate only known safe keys
        allowed_keys = {
            "MQTT_USERNAME", "MQTT_PASSWORD", "MQTT_BROKER",
            "MQTT_PORT", "MQTT_CLIENT_ID", "MQTT_TLS_MODE"
        }
        if key not in allowed_keys:
            return jsonify({"error": "Unauthorized key"}), 400

        update_env_variable(key, value)

        # Auto-reload MQTT client after config change
        client = get_sparkplug_client_instance()
        if client:
            client.reload_connection()

        return jsonify({"message": f"{key} updated and client reloaded."})
    except Exception as e:
        from src.utils.logger_module import print_error
        print_error("update_mqtt_env", e)
        return jsonify({"error": "Failed to update MQTT setting"}), 500