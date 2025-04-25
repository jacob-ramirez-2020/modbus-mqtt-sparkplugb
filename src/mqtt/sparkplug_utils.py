"""
sparkplug_utils.py

Utility functions for building Sparkplug-compliant MQTT payloads
for NBIRTH, DBIRTH, NDEATH, DDEATH, metric data, and location.

Includes support for static metadata and live values retrieved
from the system and network interfaces. Also supports Sparkplug
alias auto-generation and metadata compliant with the Sparkplug
B specification from Eclipse Tahu.
"""

import sys
sys.path.insert(0, "client_libraries")
sys.path.insert(0, "utils")

import sparkplug_b as sparkplug
from src.get_current_values import get_current_value
from src.sql.database import get_all_topics
from src.utils.system_info import (
    get_firmware_version,
    get_boot_time,
    get_date_of_firmware,
    get_location,
    get_hardware_make,
    get_os,
    get_os_version,
)
from src.utils.network_info import get_mac_address
from src.utils.logger_module import print_error

def create_birth_payload(db):
    """
    Construct and serialize a Sparkplug NBIRTH payload.

    Args:
        db: SQLite connection

    Returns:
        bytes: Serialized payload
    """
    try:
        payload = sparkplug.getNodeBirthPayload()

        sparkplug.addMetric(
            payload,
            "Node Control/Next Server",
            0,
            sparkplug.MetricDataType.Boolean,
            False,
        )
        sparkplug.addMetric(
            payload,
            "Node Control/Rebirth",
            1,
            sparkplug.MetricDataType.Boolean,
            False,
        )
        sparkplug.addMetric(
            payload,
            "Node Control/Reboot",
            2,
            sparkplug.MetricDataType.Boolean,
            False,
        )

        sparkplug.addMetric(
            payload,
            "Properties/Hardware Make",
            None,
            sparkplug.MetricDataType.String,
            get_hardware_make(),
        )
        sparkplug.addMetric(
            payload,
            "Properties/OS",
            None,
            sparkplug.MetricDataType.String,
            get_os(),
        )
        sparkplug.addMetric(
            payload,
            "Properties/OS Version",
            None,
            sparkplug.MetricDataType.String,
            get_os_version(),
        )
        sparkplug.addMetric(
            payload,
            "Device/Boot Time",
            None,
            sparkplug.MetricDataType.DateTime,
            get_boot_time(),
        )
        sparkplug.addMetric(
            payload,
            "Device/Firmware/Version",
            None,
            sparkplug.MetricDataType.String,
            get_firmware_version(),
        )
        sparkplug.addMetric(
            payload,
            "Device/Firmware/Last Updated",
            None,
            sparkplug.MetricDataType.DateTime,
            get_date_of_firmware(),
        )
        sparkplug.addMetric(
            payload,
            "Device/Network/Mac Address",
            None,
            sparkplug.MetricDataType.String,
            get_mac_address(),
        )

        location_info = get_location()
        for key, data_type in [
            ("Lat", sparkplug.MetricDataType.Float),
            ("Long", sparkplug.MetricDataType.Float),
            ("Source", sparkplug.MetricDataType.String),
            ("Valid", sparkplug.MetricDataType.String),
            ("Timestamp", sparkplug.MetricDataType.DateTime),
        ]:
            sparkplug.addMetric(
                payload,
                f"Device/Location/{key}",
                None,
                data_type,
                location_info[key],
            )

        for alias, results in enumerate(get_all_topics(db), start=10):
            topic = results["topic"]
            value = get_current_value(topic)
            units = results["units"]
            desc = results["desc"]

            metric = sparkplug.addMetric(
                payload,
                topic,
                alias,
                results["data_type"],
                value,
            )
            metric.properties.keys.extend(["engUnit"])
            property_value = metric.properties.values.add()
            property_value.type = sparkplug.ParameterDataType.String
            property_value.string_value = units
            
            metric.properties.keys.extend(["desc"])
            property_value = metric.properties.values.add()
            property_value.type = sparkplug.ParameterDataType.String
            property_value.string_value = desc
            
            
            # metric.metadata.description = desc

        return payload.SerializeToString()
    except Exception as e:
        print_error("create_birth_payload", e)
        return b""

def create_death_payload():
    """Create and serialize NDEATH payload."""
    try:
        payload = sparkplug.getNodeDeathPayload()
        sparkplug.addMetric(
            payload,
            "Device Online",
            None,
            sparkplug.MetricDataType.Boolean,
            False,
        )
        return payload.SerializeToString()
    except Exception as e:
        print_error("create_death_payload", e)
        return b""

def create_device_birth_payload(db):
    """Create and serialize DBIRTH payload."""
    try:
        payload = sparkplug.getDeviceBirthPayload()
        sparkplug.addMetric(
            payload,
            "Device Online",
            None,
            sparkplug.MetricDataType.Boolean,
            True,
        )
        return payload.SerializeToString()
    except Exception as e:
        print_error("create_device_birth_payload", e)
        return b""

def create_device_death_payload():
    """Create and serialize DDEATH payload."""
    try:
        payload = sparkplug.getDeviceBirthPayload()
        sparkplug.addMetric(
            payload,
            "Device Online",
            None,
            sparkplug.MetricDataType.Boolean,
            False,
        )
        return payload.SerializeToString()
    except Exception as e:
        print_error("create_device_death_payload", e)
        return b""

def create_data_payload(tag_name, value, data_type, units="", desc="", is_historical=False):
    """
    Create serialized DDATA payload for a single tag update.

    Args:
        tag_name (str): Tag/topic name
        value: Value to publish
        data_type: Sparkplug datatype enum
        is_historical (bool): Whether the data is historical

    Returns:
        bytes: Serialized Sparkplug payload
    """
    try:
        payload = sparkplug.getDdataPayload()
        metric = sparkplug.addMetric(
            payload, tag_name, None, data_type, value
        )
        metric.is_historical = is_historical
        
        metric.properties.keys.extend(["engUnit"])
        property_value = metric.properties.values.add()
        property_value.type = sparkplug.ParameterDataType.String
        property_value.string_value = units
        
        metric.properties.keys.extend(["desc"])
        property_value = metric.properties.values.add()
        property_value.type = sparkplug.ParameterDataType.String
        property_value.string_value = desc
        
        return payload.SerializeToString()
    except Exception as e:
        print_error("create_data_payload", e)
        return b""

def get_death_payload():
    """Return empty Sparkplug NDEATH payload object."""
    try:
        return sparkplug.getNodeDeathPayload()
    except Exception as e:
        print_error("get_death_payload", e)
        return sparkplug.Payload()

def create_location_payload():
    """Create Sparkplug DDATA payload containing device location."""
    try:
        payload = sparkplug.getDdataPayload()
        location_info = get_location()
        for key, data_type in [
            ("Lat", sparkplug.MetricDataType.Float),
            ("Long", sparkplug.MetricDataType.Float),
            ("Source", sparkplug.MetricDataType.String),
            ("Valid", sparkplug.MetricDataType.String),
            ("Timestamp", sparkplug.MetricDataType.DateTime),
        ]:
            sparkplug.addMetric(
                payload,
                f"Device/Location/{key}",
                None,
                data_type,
                location_info[key],
            )
        return payload.SerializeToString()
    except Exception as e:
        print_error("create_location_payload", e)
        return b""
