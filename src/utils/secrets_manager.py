"""
    secrets_manager.py

    Manages loading and updating secure environment-based MQTT credentials.
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key
from src.utils.logger_module import print_error, log_info

# Key should be loaded from an env variable
FERNET_KEY = os.environ.get("FERNET_KEY")

fernet = Fernet(FERNET_KEY) if FERNET_KEY else None

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

def load_env():
    """Load environment variables from the .env file."""
    try:
        load_dotenv(dotenv_path=ENV_PATH)
    except Exception as e:
        print_error("load_env", e)

def get_secure_config():
    """Retrieve secure MQTT and broker credentials from environment.
    MQTT_USERNAME
    MQTT_PASSWORD
    MQTT_BROKER
    MQTT_PORT
    MQTT_TLS_MODE
    MQTT_TRANSPORT
    MQTT_CA_CERT=certs/ca.crt
    MQTT_CLIENT_CERT=certs/client.crt
    MQTT_CLIENT_KEY=certs/client.key
    MQTT_CLIENT_ID=modbus_publisher
    MQTT_GROUP_ID
    MQTT_NODE_ID
    MQTT_DEVICE_ID
    """
    try:
        return {
            "username": os.getenv("MQTT_USERNAME"),
            "password": os.getenv("MQTT_PASSWORD"),
            "broker": os.getenv("MQTT_BROKER"),
            "port": int(os.getenv("MQTT_PORT", 8883)),
            "tls_mode": os.getenv("MQTT_TLS_MODE"),
            "transport": os.getenv("MQTT_TRANSPORT"),
            "client_id": os.getenv("MQTT_CLIENT_ID"),
            "group_id": os.getenv("MQTT_GROUP_ID"),
            "node_id": os.getenv("MQTT_NODE_ID"),
        }
    except Exception as e:
        print_error("get_secure_config", e)
        return {}

def update_env_variable(key, value):
    """Update a key in the .env file."""
    try:
        set_key(ENV_PATH, key, value)
        log_info(f"Updated environment variable: {key}")
        return True
    except Exception as e:
        print_error("update_env_variable", e)
        return False

def encrypt_secret(plaintext: str) -> str:
    try:
        return fernet.encrypt(plaintext.encode()).decode()
    except Exception as e:
        print_error("encrypt_secret", e)
        return ""

def decrypt_secret(ciphertext: str) -> str:
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        print_error("decrypt_secret", e)
        return ""
