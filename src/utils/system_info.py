"""
system_info.py

Provides functions for system-level metadata and diagnostics including:
- Hardware and OS details
- Firmware version and build date
- CPU, memory, disk usage
- System uptime and boot time
- GPS or IP-based location fallback

Includes error handling via print_error from logger_module.
"""

import os
import platform
import time
from pathlib import Path

import geocoder
import psutil
import pynmea2
import serial

from src.utils.logger_module import print_error


VERSION_FILE = Path(__file__).parent / "VERSION"
VERSION_DATE = Path(__file__).parent / "VERSION_DATE"

uname = platform.uname()


def get_hardware_make():
    """
    Get the hardware manufacturer or host name (fallback on non-Windows).

    Returns:
        str: Manufacturer name or fallback hostname.
    """
    if platform.system() == "Windows":
        try:
            import pythoncom
            import wmi

            pythoncom.CoInitialize()
            c = wmi.WMI()
            for system in c.Win32_ComputerSystem():
                return system.Manufacturer
        except Exception as e:
            print_error("get_hardware_make", e)
            return f"Unknown (WMI error: {e})"
    else:
        try:
            return platform.uname().node
        except Exception as e:
            print_error("get_hardware_make", e)
            return "Unknown"


def get_os():
    """
    Returns the operating system name.

    Returns:
        str: OS name (e.g., 'Linux', 'Windows').
    """
    try:
        return uname.system
    except Exception as e:
        print_error("get_os", e)
        return "Unknown"


def get_os_version():
    """
    Returns the OS version string.

    Returns:
        str: Version string.
    """
    try:
        return uname.version
    except Exception as e:
        print_error("get_os_version", e)
        return "Unknown"


def get_location():
    """
    Attempt to get GPS location, falling back to IP-based geolocation.

    Returns:
        dict: Location information with source, lat, long, timestamp.
    """
    gps_ports = [
        "/dev/ttyUSB1",
        "/dev/ttyUSB2",
        "/dev/ttyS0",
        "/dev/serial0",
    ]
    timestamp = int(time.time() * 1000)

    for port in gps_ports:
        if os.path.exists(port):
            try:
                with serial.Serial(port, baudrate=9600, timeout=2) as ser:
                    for _ in range(20):
                        line = ser.readline().decode(
                            "ascii", errors="replace"
                        ).strip()
                        if line.startswith("$GPGGA") or line.startswith(
                            "$GPRMC"
                        ):
                            try:
                                msg = pynmea2.parse(line)
                                lat = msg.latitude
                                lon = msg.longitude
                                if lat and lon:
                                    return {
                                        "Source": "GPS",
                                        "Lat": lat,
                                        "Long": lon,
                                        "Valid": "true",
                                        "Timestamp": timestamp,
                                    }
                            except pynmea2.nmea.ParseError:
                                continue
            except Exception as e:
                print_error("get_location (serial)", e)
                continue

    try:
        g = geocoder.ip("me")
        if g.ok and g.latlng:
            return {
                "Source": "IP",
                "Lat": g.latlng[0],
                "Long": g.latlng[1],
                "Valid": "true",
                "Timestamp": timestamp,
            }
    except Exception as e:
        print_error("get_location (ip fallback)", e)

    return {
        "Source": "IP",
        "Lat": 0,
        "Long": 0,
        "Valid": "false",
        "Timestamp": timestamp,
    }


def get_firmware_version():
    """
    Read firmware version from VERSION file.

    Returns:
        str: Version string or fallback.
    """
    try:
        return VERSION_FILE.read_text().strip()
    except Exception as e:
        print_error("get_firmware_version", e)
        return "Unknown Version"


def get_date_of_firmware():
    """
    Read firmware build date from VERSION_DATE.

    Returns:
        int | str: Unix timestamp in ms or fallback.
    """
    try:
        return int(VERSION_DATE.read_text().strip()) * 1000
    except Exception as e:
        print_error("get_date_of_firmware", e)
        return "Unknown Firmware Date"


def get_boot_time():
    """
    Return the system boot time in milliseconds.

    Returns:
        int: Boot time (epoch ms).
    """
    try:
        return int(psutil.boot_time()) * 1000
    except Exception as e:
        print_error("get_boot_time", e)
        return 0


def get_uptime_seconds():
    """
    Return uptime in seconds since boot.

    Returns:
        int: Uptime in seconds.
    """
    try:
        return int(time.time() - psutil.boot_time())
    except Exception as e:
        print_error("get_uptime_seconds", e)
        return 0


def get_available_disk_space_mb(path="/"):
    """
    Return available disk space in MB.

    Args:
        path (str): Filesystem path to check.

    Returns:
        float: MB of free disk space.
    """
    try:
        usage = psutil.disk_usage(path)
        return usage.free / (1024 * 1024)
    except Exception as e:
        print_error("get_available_disk_space_mb", e)
        return 0.0


def get_available_disk_space_percent(path="/"):
    """
    Return free disk space as a fraction (0.0 to 1.0).

    Args:
        path (str): Filesystem path to check.

    Returns:
        float: Fraction of free space.
    """
    try:
        usage = psutil.disk_usage(path)
        return (100.0 - usage.percent) / 100.0
    except Exception as e:
        print_error("get_available_disk_space_percent", e)
        return 0.0


def get_cpu_usage_percent():
    """
    Return CPU usage as a fraction (0.0 to 1.0).

    Returns:
        float: CPU usage.
    """
    try:
        return psutil.cpu_percent(interval=1) / 100.0
    except Exception as e:
        print_error("get_cpu_usage_percent", e)
        return 0.0


def get_max_memory_bytes():
    """
    Return total physical memory in bytes.

    Returns:
        int: Max memory.
    """
    try:
        return psutil.virtual_memory().total
    except Exception as e:
        print_error("get_max_memory_bytes", e)
        return 0


def get_memory_used_bytes():
    """
    Return used physical memory in bytes.

    Returns:
        int: Used memory.
    """
    try:
        return psutil.virtual_memory().used
    except Exception as e:
        print_error("get_memory_used_bytes", e)
        return 0


def get_memory_utilization_percent():
    """
    Return memory utilization as a fraction (0.0 to 1.0).

    Returns:
        float: Used memory percent.
    """
    try:
        return psutil.virtual_memory().percent / 100.0
    except Exception as e:
        print_error("get_memory_utilization_percent", e)
        return 0.0


def get_disk_utilization_percent(path="/"):
    """
    Return disk usage as a fraction (0.0 to 1.0).

    Args:
        path (str): Filesystem path to check.

    Returns:
        float: Used space percent.
    """
    try:
        return psutil.disk_usage(path).percent / 100.0
    except Exception as e:
        print_error("get_disk_utilization_percent", e)
        return 0.0
