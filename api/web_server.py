from flask import Flask, jsonify
from flask import Blueprint
from api.log_buffer_api import buffer_config_bp
from api.log_config_api import log_config_bp
from api.mqtt_config_api import mqtt_config_bp
from src.sql.database import get_db_buffer_metrics
from src.get_current_values import get_all_topic_metadata


log_config_bp = Blueprint("log_config_bp", __name__)
buffer_config_bp = Blueprint("buffer_config_api", __name__)

def create_app(sparkplug_client, db):
    app = Flask(__name__)
    app.register_blueprint(log_config_bp)
    app.register_blueprint(buffer_config_bp)
    app.register_blueprint(mqtt_config_bp)

    @app.route('/metrics')
    def metrics():
        sparkplug_metrics = sparkplug_client.get_metrics()
        sparkplug_metrics.update(get_db_buffer_metrics(db))
        return jsonify(sparkplug_metrics)
    
    @app.route("/topics/metadata", methods=["GET"])
    def topics_metadata():
        """
        Endpoint to return all Sparkplug-compliant topic metadata as JSON.
        """
        return jsonify(get_all_topic_metadata())

    return app
