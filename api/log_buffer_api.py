"""
API endpoint to adjust MQTT buffer size configuration.
"""

from flask import request, jsonify
from src.sql.database import MAX_BUFFER_SIZE_BYTES, set_max_buffer_size_limit
from src.utils.logger_module import print_error, log_trace, get_log_level_num
from api.blueprints.buffer_config_bp import buffer_config_bp


@buffer_config_bp.route("/api/buffer/max_size", methods=["POST"])
def update_max_buffer_size():
    """
    Update the buffer max size in bytes.

    JSON:
    {
        "max_bytes": 2097152
    }

    Returns:
        JSON response with success or error.
    """
    try:
        data = request.get_json()
        size = int(data.get("max_bytes", 0))
        if size <= 0:
            return jsonify({"error": "Invalid max_bytes value"}), 400

        set_max_buffer_size_limit(size)
        if get_log_level_num() <= 5:
            log_trace(f"Buffer max size updated to {size}")

        return jsonify({"message": "Buffer size updated"}), 200
    except Exception as e:
        print_error("update_max_buffer_size", e)
        return jsonify({"error": "Failed to update buffer size"}), 500

@buffer_config_bp.route("/api/buffer/config", methods=["GET"])
def get_buffer_config():
    """
    Return current buffer configuration.

    Returns:
        JSON with max buffer size.
    """
    try:
        return jsonify({
            "max_bytes": MAX_BUFFER_SIZE_BYTES
        })
    except Exception as e:
        print_error("get_buffer_config", e)
        return jsonify({"error": "Failed to fetch buffer config"}), 500
