"""
database.py

Database utility functions for MQTT message buffering, topic tracking, and
configuration loading.

Includes buffer retention policy enforcement when max size is reached.

This module provides:
- Initialize and close SQLite connections.
- Insert MQTT messages into a buffer.
- Flush buffered messages to an MQTT broker.
- Retrieve available MQTT topics from the database.
- Report buffer metrics for monitoring purposes.
- Load MQTT and system configuration settings from the database.
"""

import os
import sqlite3
from dotenv import load_dotenv
from src.utils.logger_module import log_warn, print_error, log_trace, get_log_level_num, log_info

# === Buffer Retention Config ===
MAX_BUFFER_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

def init_db():
    """
    Initialize and return a connection to the SQLite database.

    Returns:
        sqlite3.Connection: Database connection object.
    """
    try:
        db_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            ),
            "data",
            "config.db"
        )
        return sqlite3.connect(db_path, check_same_thread=False)
    except Exception as e:
        print_error("init_db", e)


def close(conn):
    """
    Close the given SQLite database connection.

    Args:
        conn (sqlite3.Connection): Connection to close.
    """
    try:
        if conn:
            conn.close()
            if get_log_level_num() <= 5:
                log_trace("Database connection closed.")
    except Exception as e:
        print_error("close", e)


def buffer_message(db, topic, payload, qos, retain):
    """
    Insert an MQTT message into the buffer for later transmission.

    Args:
        db (sqlite3.Connection): Database connection.
        topic (str): MQTT topic.
        payload (bytes): Message payload.
        qos (int): Quality of Service level.
        retain (bool): Retain flag.
    """
    try:
        cursor = db.cursor()

        # Calculate total size
        cursor.execute("SELECT SUM(LENGTH(payload)) FROM mqtt_buffer")
        current_size = cursor.fetchone()[0] or 0
        incoming_size = len(payload)

        if current_size + incoming_size > MAX_BUFFER_SIZE_BYTES:
            # Drop oldest rows until there's room
            while current_size + incoming_size > MAX_BUFFER_SIZE_BYTES:
                cursor.execute("SELECT id, LENGTH(payload) FROM mqtt_buffer ORDER BY timestamp ASC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    cursor.execute("DELETE FROM mqtt_buffer WHERE id = ?", (row[0],))
                    current_size -= row[1]
                    if get_log_level_num() <= 30:
                        log_warn("Buffer full. Dropped oldest message.")
                else:
                    break

        cursor.execute(
            "INSERT INTO mqtt_buffer (topic, payload, qos, retain, "
            "timestamp) VALUES (?, ?, ?, ?, datetime('now'))",
            (topic, payload, qos, retain),
        )
        db.commit()

        if get_log_level_num() <= 5:
            log_trace(f"Buffered message topic: {topic}")

    except Exception as e:
        print_error("buffer_message", e)


def flush_buffer(db, mqtt_client):
    """
    Publish all buffered MQTT messages and clear the buffer.

    Args:
        db (sqlite3.Connection): Database connection.
        mqtt_client: MQTT client instance for publishing.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM mqtt_buffer ORDER BY timestamp ASC"
        )
        rows = cursor.fetchall()
        for row in rows:
            topic, payload, qos, retain = (
                row[1],
                row[2],
                row[3],
                row[4],
            )
            mqtt_client.publish(
                topic, payload, qos, retain, is_historical=True
            )
        cursor.execute("DELETE FROM mqtt_buffer")
        db.commit()
        if get_log_level_num() <= 5:
            log_trace("Finish flush_buffer()")
    except Exception as e:
        print_error("flush_buffer", e)


def get_all_topics(db):
    """
    Retrieve all MQTT topics and their data types from the database.

    Args:
        db (sqlite3.Connection): Database connection.

    Returns:
        list: List of dictionaries with topic and data_type keys.
    """
    try:
        cursor = db.cursor()
        cursor.execute("SELECT t.topic, t.data_type, t.units, t.desc FROM mqtt_topics t")
        rows = cursor.fetchall()
        values = [{"topic": row[0], "data_type": row[1], "units": row[2], "desc": row[3]} for row in rows]
        return values
    except Exception as e:
        print_error("get_all_topics", e)
        return []


def get_db_buffer_metrics(db):
    """
    Retrieve buffer metrics such as message count and oldest timestamp.

    Args:
        db (sqlite3.Connection): Database connection.

    Returns:
        dict: Buffer metrics.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT COUNT(*), 
                   SUM(LENGTH(payload)), 
                   MIN(timestamp)
            FROM mqtt_buffer
            """
        )
        count, size_bytes, oldest_ts = cursor.fetchone()

        metrics = {
            "buffer_size_bytes": size_bytes if size_bytes else 0,
            "buffer_message_count": count,
            "buffer_dropped_messages": 0,
            "buffer_oldest_timestamp": oldest_ts if oldest_ts else "",
        }
        if get_log_level_num() <= 5:
            log_trace(str(metrics))
        return metrics
    except Exception as e:
        print_error("get_db_buffer_metrics", e)
        return {}


def set_max_buffer_size_limit(size_bytes):
    """
    Update the maximum buffer size in bytes.

    Args:
        size_bytes (int): New max size in bytes.
    """
    global MAX_BUFFER_SIZE_BYTES
    MAX_BUFFER_SIZE_BYTES = size_bytes
    if get_log_level_num() <= 5:
        log_trace(f"MAX_BUFFER_SIZE_BYTES set to {size_bytes}")


def load_config(db=None):
    """
    Load MQTT and system config from environment variables (.env).

    Args:
        db (sqlite3.Connection, optional): Not used anymore.

    Returns:
        dict: Config dictionary with MQTT connection parameters.
    """
    try:
        load_dotenv()  # Loads from .env if not already loaded

        return {
            "broker": os.environ.get("MQTT_BROKER", "localhost"),
            "port": int(os.environ.get("MQTT_PORT", 1883)),
            "client_id": os.environ.get("MQTT_CLIENT_ID", "MyClient"),
            "username": os.environ.get("MQTT_USERNAME"),
            "password": os.environ.get("MQTT_PASSWORD"),
            "group_id": os.environ.get("MQTT_GROUP_ID", "MyGroup"),
            "node_id": os.environ.get("MQTT_NODE_ID", "MyNode"),
            "device_id": os.environ.get("MQTT_DEVICE_ID", "dev1"),
            "tls_mode": os.environ.get("MQTT_TLS_MODE", "none"),
        }
    except Exception as e:
        print_error("load_config", e)
        return {}

