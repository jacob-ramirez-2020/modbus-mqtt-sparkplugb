"""
publisher.py

This module defines the Publisher class responsible for polling values,
evaluating deadbands, publishing MQTT messages using SparkplugB, and
buffering messages to a database in case of connection failure.
"""

import threading
import time
from datetime import datetime

from src.utils.logger_module import log_info, print_error, get_log_level_num, log_trace, log_error

from src.get_current_values import get_current_value
from src.mqtt.sparkplug_utils import create_data_payload
from src.sql.database import buffer_message
from src.mqtt.tag_manager import TagManager


class Publisher:
    """
    Handles publishing of SparkplugB data to an MQTT broker and
    buffering messages during failures.
    """

    def __init__(self, db, mqtt_client):
        """
        Initialize Publisher with database and MQTT client.

        Args:
            db (sqlite3.Connection): Database connection.
            mqtt_client: Configured MQTT client with Sparkplug settings.
        """
        self.db = db
        self.client = mqtt_client
        self.tag_manager = TagManager(db)

    def publish_all(self, mqtt):
        """
        Poll current values, check deadbands, publish to MQTT, and
        buffer on failure.

        Args:
            mqtt: Object that handles MQTT methods and config.
        """
        try:
            if datetime.now().strftime("%M") == "00":
                mqtt.publish_location()
                if get_log_level_num() <= 5:
                    log_trace("Publish Location")

            cursor = self.db.cursor()
            cursor.execute(
                "SELECT t.topic, t.deadband, t.data_type, t.units, t.desc FROM mqtt_topics t"
            )

            for topic, deadband, data_type, units, desc in cursor.fetchall():
                new_val = get_current_value(topic)

                if self.tag_manager.should_publish(
                    topic, new_val, data_type
                ):
                    payload = create_data_payload(
                        topic, new_val, data_type, units, desc
                    )
                    try:
                        full_topic = (
                            f"spBv1.0/{self.client.cfg['group_id']}/"
                            f"NDATA/{self.client.cfg['node_id']}"
                        )
                        self.client.publish(full_topic, payload)
                        self.client.messages_sent += 1
                    except Exception as e:
                        log_error(f"Buffered Message:, {str(full_topic)} {str(payload)}")
                        buffer_message(
                            self.db, full_topic, payload, 0, False
                        )
                        print_error("Publisher.publish_all", e)

        except Exception as e:
            print_error("Publisher.publish_all", e)

    def start_buffer_flusher(self, mqtt, interval=5):
        """
        Start a background thread that periodically flushes the buffer
        by calling publish_all.

        Args:
            interval (int): Time in seconds between publish attempts.
        """
        def flusher():
            if get_log_level_num() <= 20:
                log_info("[Publisher] Starting buffer flusher thread.")
            while True:
                self.publish_all(mqtt)
                if get_log_level_num() <= 5:
                    log_trace(f"[Publisher] Flush interval: 5s")
                time.sleep(5)

        threading.Thread(target=flusher, daemon=True).start()
