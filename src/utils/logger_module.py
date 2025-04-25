"""
Centralized logging module for application-wide use.

Features:
- Logs to rotating files in the log_files directory.
- Configurable max file size and number of backup files.
- Supports logging levels: FATAL, ERROR, WARN, INFO, DEBUG, TRACE.
- Includes detailed error tracing with line numbers using print_error().
- Simultaneously logs to console and file.

CRITICAL/FATAL: 50 (Very severe errors — program may abort)
ERROR: 40 (Errors that prevent part of the program from running)
WARNING/WARN: 30 (Unexpected situations that aren’t critical)
INFO: 20 (General events (e.g., startup, shutdown)
DEBUG: 10 (Diagnostic details, mainly for developers)
TRACE: 5 (Ultra-fine logging for step-by-step internals)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
import traceback
import sys

# === Configuration ===
LOG_DIR = "log_files"
LOG_FILE_BASE = "log"
MAX_BYTES = 1 * 1024 * 1024  # 1MB
BACKUP_COUNT = 5
LOG_LEVEL = logging.INFO

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# === Logger Setup ===
logger = logging.getLogger("AppLogger")
logger.setLevel(LOG_LEVEL)

# Formatter that includes timestamp, level, and message
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Rotating file handler
log_path = os.path.join(LOG_DIR, f"{LOG_FILE_BASE}.log")
file_handler = RotatingFileHandler(
    log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream to console too
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def log_trace(msg):
    """
    Log a TRACE level message (custom level below DEBUG).

    Args:
        msg (str): The message to log.
    """
    if logger.isEnabledFor(TRACE_LEVEL_NUM):
        logger.log(TRACE_LEVEL_NUM, msg)

def set_log_level(level_name):
    """
    Set the global log level by string.

    Args:
        level_name (str): One of 'FATAL', 'ERROR', 'WARN',
                          'INFO', 'DEBUG', 'TRACE'.
    """
    level_map = {
        "FATAL": logging.FATAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "TRACE": TRACE_LEVEL_NUM,
    }

    level = level_map.get(level_name.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def get_log_level():
    """
    Retrieve the current global log level as a human-readable string.

    Returns:
        str: Log level name (e.g., 'INFO', 'DEBUG').
    """
    level_map_reverse = {
        logging.FATAL: "FATAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARN",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
        TRACE_LEVEL_NUM: "TRACE"
    }
    return level_map_reverse.get(logger.level, "INFO")

def get_log_level_num() -> int:
    """
    Returns the current logger level as an integer.
    
    Returns:
        int: Numeric logging level 
            - 50 for CRITICAL/FATAL
            - 40 for ERROR
            - 30 for WARNING/WARN
            - 20 for INFO
            - 10 for DEBUG
            - 5 for TRACE
    """
    return logger.level

def set_max_log_file_size(bytes_size):
    """
    Set the maximum size for a log file before rotating.

    Args:
        bytes_size (int): Size in bytes.
    """
    global MAX_BYTES
    MAX_BYTES = bytes_size
    _reconfigure_handler()


def set_max_log_files(count):
    """
    Set the maximum number of rotated log files to keep.

    Args:
        count (int): Maximum number of log files.
    """
    global BACKUP_COUNT
    BACKUP_COUNT = count
    _reconfigure_handler()


def _reconfigure_handler():
    """
    Reapply rotating handler settings after changing size/count.
    """
    logger.handlers = []
    file_handler = RotatingFileHandler(
        log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def print_error(function_name, exception):
    """
    Log detailed traceback including filename and line number.

    Args:
        function_name (str): Function where the error occurred.
        exception (Exception): The exception instance.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)
    filename, lineno, _, _ = tb[-1]
    logger.error(
        f"[{function_name}] Exception at {filename}, "
        f"line {lineno}: {exception}"
    )
    logger.error("Traceback:")
    logger.error("".join(traceback.format_exception(*sys.exc_info())))


def log_debug(msg):
    """
    Log a DEBUG level message.

    Args:
        msg (str): The message to log.
    """
    logger.debug(msg)


def log_info(msg):
    """
    Log an INFO level message.

    Args:
        msg (str): The message to log.
    """
    logger.info(msg)


def log_warn(msg):
    """
    Log a WARN level message.

    Args:
        msg (str): The message to log.
    """
    logger.warning(msg)


def log_error(msg):
    """
    Log an ERROR level message.

    Args:
        msg (str): The message to log.
    """
    logger.error(msg)


def log_fatal(msg):
    """
    Log a FATAL level message.

    Args:
        msg (str): The message to log.
    """
    logger.fatal(msg)


# Expose the logger itself if needed
get_logger = lambda: logger
