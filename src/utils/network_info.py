"""
network_utils.py

This module provides utility functions for network identification,
specifically retrieving the device's IP address and MAC address.
It uses socket and uuid standard libraries, and logs any errors
encountered using the shared logging module (print_error).
"""

import socket
import uuid
from src.utils.logger_module import print_error


def get_ip_address():
    """
    Retrieve the local IP address of the device.

    Returns:
        str: IP address, or '127.0.0.1' if unable to determine.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to external address (no traffic sent)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print_error("get_ip_address", e)
        return "127.0.0.1"


def get_mac_address():
    """
    Retrieve the MAC address of the device.

    Returns:
        str: MAC address in colon-separated format.
    """
    try:
        mac = uuid.getnode()
        return ":".join(
            f"{(mac >> ele) & 0xff:02x}" for ele in range(40, -1, -8)
        )
    except Exception as e:
        print_error("get_mac_address", e)
        return "00:00:00:00:00:00"
