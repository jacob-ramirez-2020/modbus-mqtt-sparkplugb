"""
get_current_values.py

Provides topic-specific values for system, network, and simulated tags,
along with Sparkplug-compliant metadata like alias, datatype, engineering
units, and descriptions. Supports test files and logs errors via the
centralized logging module.
"""

import json
import os
import random

from src.utils.logger_module import print_error, log_info, log_warn
from src.utils.network_info import get_ip_address
from src.utils.system_info import (
    get_available_disk_space_mb,
    get_available_disk_space_percent,
    get_cpu_usage_percent,
    get_max_memory_bytes,
    get_memory_used_bytes,
    get_memory_utilization_percent,
    get_disk_utilization_percent,
    get_uptime_seconds,
)

topic_function_map = {
    "Device/Network/IP Address": get_ip_address,
    "Device/Uptime Seconds": get_uptime_seconds,
    "Device/Performance/CPU Usage": get_cpu_usage_percent,
    "Device/Performance/Available Disk Space (MB)": get_available_disk_space_mb,
    "Device/Performance/Available Disk Space (Percent)": get_available_disk_space_percent,
    "Device/Performance/Max Memory": get_max_memory_bytes,
    "Device/Performance/Memory Usage": get_memory_used_bytes,
    "Device/Performance/Memory Utilization": get_memory_utilization_percent,
    "Device/Performance/Disk Utilization": get_disk_utilization_percent,
    
}

def load_topic_handlers_from_db(db, export_json_path=None):
    """
    Load topic handler metadata from the mqtt_topics table using topic ID
    as alias, and optionally export the map as JSON.

    Args:
        export_json_path (str): Optional path to save alias map as JSON.

    Returns:
        dict: Dictionary of topic handlers keyed by topic name.
    """
    topic_handlers = {}
    used_aliases = set()
    alias_map_export = {}

    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, topic, data_type, units, desc FROM mqtt_topics
        """)

        for row in cursor.fetchall():
            topic_id, topic, data_type, units, desc = row

            handler = topic_function_map.get(topic)
            if handler is None:
                log_warn(f"[MQTT] No handler defined for topic: {topic}")
                continue

            if topic_id in used_aliases:
                log_warn(f"[MQTT] Duplicate alias ID detected: {topic_id}")
                continue
            used_aliases.add(topic_id)

            topic_handlers[topic] = {
                "handler": handler,
                "name": topic,
                "alias": topic_id,
                "datatype": data_type,
                "is_historical": False,
                "is_transient": False,
                "metadata": {
                    "desc": desc or "",
                    "engUnit": units or ""
                },
                "properties": {},
            }

            alias_map_export[topic_id] = {
                "topic": topic,
                "desc": desc or "",
                "units": units or "",
            }

        db.close()

        if export_json_path:
            with open(export_json_path, "w", encoding="utf-8") as f:
                json.dump(alias_map_export, f, indent=4)
            log_info(f"[MQTT] Alias map exported to {export_json_path}")

        log_info(f"[MQTT] Loaded {len(topic_handlers)} topic handlers.")

    except Exception as e:
        print_error("load_topic_handlers_from_db", e)

    return topic_handlers

def get_current_value(topic):
    """
    Retrieve the current value for a given topic.

    Args:
        topic (str): The topic name to evaluate.

    Returns:
        float | str | None: The computed and scaled value.
    """
    try:
        if topic.startswith("Tags/"):
            file_path = os.path.join(
                "test_files", topic.replace("Tags/", "")
            )
            with open(file_path, "r", encoding="utf-8") as file:
                return float(file.read())

        topic_data = topic_function_map.get(topic)
        if topic_data:
            return topic_data()

        return random.uniform(0, 100)

    except Exception as e:
        print_error("get_current_value", e)
        return None


# Counter to generate auto-aliases for unknown or user-added topics
# _auto_alias_counter = max([v["alias"] for v in topic_function_map.values()], default=100)

def get_topic_metadata(topic):
    """
    Retrieve Sparkplug-compliant metadata for a given topic.

    Args:
        topic (str): The topic name.

    Returns:
        dict: Metadata dictionary following Sparkplug specification.
    """
    global _auto_alias_counter
    data = topic_function_map.get(topic)

    if data:
        return {
            "name": data["name"],
            "alias": data["alias"],
            "datatype": data["datatype"],
            "is_historical": data["is_historical"],
            "is_transient": data["is_transient"],
            "metadata": data["metadata"],
            "properties": data["properties"],
        }

    # Handle unknown topic with simulated metadata and auto-alias
    _auto_alias_counter += 1
    return {
        "name": topic,
        "alias": _auto_alias_counter,
        "datatype": "Double",
        "is_historical": False,
        "is_transient": False,
        "metadata": {
            "desc": "Auto-generated topic",
        },
        "properties": {},
    }

def export_all_topic_metadata_to_json(path="exported_metadata.json"):
    """
    Export metadata for all known topics to a JSON file.

    Args:
        path (str): Path to the output JSON file.
    """
    try:
        metadata = {
            topic: get_topic_metadata(topic) for topic in topic_function_map.keys()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        log_info(f"Metadata exported to {path}")
    except Exception as e:
        print_error("export_all_topic_metadata_to_json", e)

def get_all_topic_metadata():
    """
    Get metadata for all topics currently known.

    Returns:
        dict: A dictionary of topic metadata keyed by topic name.
    """
    return {
        topic: get_topic_metadata(topic)
        for topic in topic_function_map.keys()
    }
