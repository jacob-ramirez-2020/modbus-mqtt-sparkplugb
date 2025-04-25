"""
log_config_api.py

Flask API routes for log configuration and inspection.

Supports:
- Updating max file size and max file count
- Changing log level
- Downloading and tailing log files
- Listing available log files
"""

import os
from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from api.blueprints.log_config_bp import log_config_bp
from src.utils.logger_module import (
    MAX_BYTES,
    BACKUP_COUNT,
    LOG_DIR,
    LOG_FILE_BASE,
    set_max_log_file_size,
    set_max_log_files,
    set_log_level,
    print_error,
    get_log_level,
    get_log_level_num,
    log_trace,
)


@log_config_bp.route("/api/logs/max_size", methods=["POST"])
def update_max_log_size():
    """
    Set the maximum size (in bytes) for a log file before rotation.

    JSON payload:
    {
        "bytes_size": 2097152
    }

    Returns:
        JSON: Success or error message.
    """
    try:
        data = request.get_json()
        size = int(data.get("bytes_size", 0))

        if size <= 0:
            return jsonify({"error": "Invalid bytes_size"}), 400

        set_max_log_file_size(size)

        if get_log_level_num() <= 5:
            log_trace(f"Max log file size updated: {size}")

        return jsonify({"message": "Max log file size updated"}), 200

    except Exception as e:
        print_error("update_max_log_size", e)
        return jsonify({"error": "Failed to update max log size"}), 500


@log_config_bp.route("/api/logs/max_files", methods=["POST"])
def update_max_log_files():
    """
    Set the maximum number of rotated log files to keep.

    JSON payload:
    {
        "count": 10
    }

    Returns:
        JSON: Success or error message.
    """
    try:
        data = request.get_json()
        count = int(data.get("count", 0))

        if count <= 0:
            return jsonify({"error": "Invalid count value"}), 400

        set_max_log_files(count)

        if get_log_level_num() <= 5:
            log_trace(f"Max log file count updated: {count}")

        return jsonify({"message": "Max log file count updated"}), 200

    except Exception as e:
        print_error("update_max_log_files", e)
        return jsonify({"error": "Failed to update max log files"}), 500

@log_config_bp.route("/api/logs/level", methods=["POST"])
def set_log_level_endpoint():
    """
    Update the log level dynamically.

    JSON payload:
    {
        "level": "INFO"
    }
    """
    try:
        data = request.get_json()
        level = data.get("level", "").upper()
        if level not in ["FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"]:
            return jsonify({"error": "Invalid log level"}), 400

        set_log_level(level)
        if get_log_level_num() <= 5:
            log_trace(f"Log level updated: {level}")
        return jsonify({"message": "Log level updated"}), 200
    except Exception as e:
        print_error("set_log_level_endpoint", e)
        return jsonify({"error": "Failed to update log level"}), 500

@log_config_bp.route("/api/logs/config", methods=["GET"])
def get_log_config():
    """
    Get the current logging configuration.

    Returns:
        JSON:
        {
            "log_level": "DEBUG",
            "max_bytes": 2097152,
            "max_files": 10
        }
    """
    try:
        return jsonify(
            {
                "log_level": get_log_level(),
                "max_bytes": MAX_BYTES,
                "max_files": BACKUP_COUNT,
            }
        )
    except Exception as e:
        print_error("get_log_config", e)
        return jsonify({"error": "Failed to fetch log config"}), 500

@log_config_bp.route("/api/logs/tail", methods=["GET"])
def get_log_tail():
    """
    Return the last N lines of the latest log file.

    Query Params:
        lines (int): Number of lines to return (default: 50)

    Returns:
        JSON with the log lines or error
    """
    try:
        lines = int(request.args.get("lines", 50))
        log_path = os.path.join(LOG_DIR, f"{LOG_FILE_BASE}.log")

        if not os.path.exists(log_path):
            return jsonify({"error": "Log file not found"}), 404

        with open(log_path, "r", encoding='utf-8') as f:
            all_lines = f.readlines()[-lines:]

        return jsonify({"lines": all_lines})

    except Exception as e:
        print_error("get_log_tail", e)
        return jsonify({"error": "Failed to read log tail"}), 500

@log_config_bp.route("/api/logs/files", methods=["GET"])
def list_log_files():
    """
    List all log files in the log directory.

    Returns:
        JSON array of filenames.
    """
    try:
        if not os.path.exists(LOG_DIR):
            return jsonify([])

        files = sorted([
            f for f in os.listdir(LOG_DIR)
            if f.endswith(".log")
        ])
        return jsonify(files)

    except Exception as e:
        print_error("list_log_files", e)
        return jsonify({"error": "Failed to list log files"}), 500

@log_config_bp.route("/api/logs/download/<filename>", methods=["GET"])
def download_log_file(filename):
    """
    Download a specific log file from the log_files directory.

    Args:
        filename (str): Name of the log file to download.

    Returns:
        File download response or 404 if not found.
    """
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(LOG_DIR, safe_filename)

        if not os.path.isfile(file_path):
            return jsonify({"error": "Log file not found"}), 404

        return send_from_directory(
            LOG_DIR,
            safe_filename,
            as_attachment=True,
            mimetype="text/plain"
        )
    except Exception as e:
        print_error("download_log_file", e)
        return jsonify({"error": "Failed to download file"}), 500
