"""
main.py

Entry point for starting the MQTT SparkplugB publisher application.
Initializes the MQTT client, database, publisher, and Flask web UI.
Handles clean shutdown on Ctrl+C or SIGTERM, and logs key lifecycle events.
"""

import os
import signal
import sys
import threading
import time
from dotenv import load_dotenv
from threading import Thread

from src.mqtt.mqtt_client import SparkplugClient
from src.mqtt.publisher import Publisher
from src.sql.database import init_db, flush_buffer
from src.utils.system_info import get_firmware_version
from api.web_server import create_app
from src.mqtt.mqtt_client import SparkplugClient, set_sparkplug_client_instance
from src.utils.logger_module import (
    set_log_level,
    set_max_log_file_size,
    set_max_log_files,
    print_error,
    log_info,
    get_log_level_num,
    log_trace
)


def run_web_server(app):
    """
    Start the Flask web server.

    Args:
        app (Flask): Configured Flask app instance.
    """
    try:
        app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
    except Exception as e:
        print_error("run_web_server", e)


if __name__ == "__main__":
    log_info(get_firmware_version())
    load_dotenv()  # This will load variables from .env into os.environ

    # Initialize components
    db = init_db()
    mqtt = SparkplugClient(db)
    publisher = Publisher(db, mqtt)
    set_sparkplug_client_instance(mqtt)


    # Logging configuration
    set_log_level("INFO")
    set_max_log_file_size(2 * 1024 * 1024)  # 2 MB
    set_max_log_files(10)

    # Start Flask app in background
    try:
        flask_app = create_app(mqtt, db)
        web_thread = Thread(target=run_web_server, args=(flask_app,))
        web_thread.daemon = True
        web_thread.start()
    except Exception as e:
        print_error("Flask Init", e)

    try:
        mqtt.connect()
        mqtt.publish_birth()
        if get_log_level_num() <= 5:
            log_trace("Finish Birth")
        time.sleep(2)
        mqtt.publish_device_birth()
        time.sleep(1)
        flush_buffer(mqtt.db, mqtt)
        mqtt._start_reconnect_watchdog()
        publisher.start_buffer_flusher(mqtt)
    except Exception as e:
        print_error("MQTT Init", e)

    # Graceful shutdown support
    stop_event = threading.Event()

    def cleanup():
        """Cleanup all resources during shutdown."""
        log_info("[System] Cleaning up...")
        try:
            if get_log_level_num() <= 20:
                log_info("[MQTT] Stopping client loop and disconnecting...")
            mqtt.disconnect()
        except Exception as e:
            print_error("mqtt.disconnect", e)

        try:
            if get_log_level_num() <= 20:
                log_info("[DB] Closing database (if applicable)...")
            db.close()
        except Exception as e:
            print_error("db.close", e)

        log_info("[System] Shutdown complete.")

    def handle_signal(sig, frame):
        """
        Handle termination signals like Ctrl+C or SIGTERM.

        Args:
            sig: Signal number
            frame: Current stack frame
        """
        if get_log_level_num() <= 20:
            log_info("\n[System] Caught termination signal, shutting down...")
        stop_event.set()
        mqtt.publish_death()
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        if get_log_level_num() <= 20:
            log_info("\n[System] Ctrl+C pressed. Exiting...")
        mqtt.publish_death()
        if get_log_level_num() <= 5:
            log_trace("Finish publishing death certificate.")
        stop_event.set()
        cleanup()
        sys.exit(0)
