"""
tag_manager.py

Manages tag state and deadband comparisons for determining whether a new
value should be published over MQTT. Deadbands are loaded from the
database. Includes support for analog and discrete data types and 
stores the last known value for comparison.
"""

from src.utils.logger_module import print_error, get_log_level_num, log_trace


class TagManager:
    """
    Manages deadband filtering and tag value tracking for MQTT publishing.
    """

    def __init__(self, db):
        """
        Initialize the TagManager with a database connection and preload
        deadband settings.

        Args:
            db (sqlite3.Connection): Active database connection.
        """
        self.db = db
        self.last_values = {}  # {tag: last_value}
        self.deadbands = self._load_deadbands_from_db()

    def _load_deadbands_from_db(self):
        """
        Load deadband settings from the mqtt_topics table.

        Returns:
            dict: Dictionary of {topic: deadband} values.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT t.topic, t.deadband
                FROM mqtt_topics t
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            print_error("TagManager._load_deadbands_from_db", e)
            return {}

    def should_publish(self, tag, new_value, data_type):
        """
        Determine if a new value should be published based on deadband.

        Args:
            tag (str): Topic/tag name.
            new_value (any): The new value read from the device.
            data_type (int): SparkplugB data type ID.

        Returns:
            bool: True if value should be published.
        """
        try:
            if tag not in self.deadbands:
                if get_log_level_num() <= 5:
                    log_trace(f"No deadband found for {tag}, always publish")
                return True  # No deadband config, always publish

            deadband = self.deadbands[tag]
            last_value = self.last_values.get(tag)

            if last_value is None:
                self.last_values[tag] = new_value
                if get_log_level_num() <= 5:
                    log_trace(f"No last value found for {tag}, always publish")
                return True

            if data_type == 12:  # Boolean
                boolean_check = new_value != last_value
                if not boolean_check:
                    if get_log_level_num() <= 5:
                        log_trace(f"Deadband not met for topic: {tag}")
                        log_trace(f"Deadband amount: {deadband}")
                        log_trace(f"Last Value: {last_value}")
                        log_trace(f"New Value: {new_value}")
                return boolean_check
            else:  # Numeric deadband check
                if abs(new_value - last_value) >= deadband:
                    self.last_values[tag] = new_value
                    return True
                else:
                    if get_log_level_num() <= 5:
                        log_trace(f"Deadband not met for topic: {tag}")
                        log_trace(f"Deadband amount: {deadband}")
                        log_trace(f"Last Value: {last_value}")
                        log_trace(f"New Value: {new_value}")
                    return False
        except Exception as e:
            print_error("TagManager.should_publish", e)
            return True  # Default to publish on error

    def update_last_value(self, tag, value):
        """
        Manually update the last known value of a tag.

        Args:
            tag (str): Tag/topic name.
            value (any): New value to store.
        """
        try:
            self.last_values[tag] = value
        except Exception as e:
            print_error("TagManager.update_last_value", e)

    def reset(self):
        """
        Clear all stored last values, forcing future publishes.
        """
        try:
            self.last_values.clear()
        except Exception as e:
            print_error("TagManager.reset", e)
