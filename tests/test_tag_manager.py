import unittest
from unittest.mock import MagicMock
from src.mqtt.tag_manager import TagManager


class TestTagManager(unittest.TestCase):
    def setUp(self):
        # Create a mock database connection and cursor
        self.mock_cursor = MagicMock()
        self.mock_cursor.fetchall.return_value = [
            ("Tag/Analog", 5.0),
            ("Tag/Boolean", 0),
        ]
        self.mock_db = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor

        self.manager = TagManager(self.mock_db)

    def test_should_publish_first_time(self):
        result = self.manager.should_publish("Tag/Analog", 10.0, 1)
        self.assertTrue(result)

    def test_should_publish_numeric_deadband_exceeded(self):
        self.manager.last_values["Tag/Analog"] = 10.0
        result = self.manager.should_publish("Tag/Analog", 20.1, 1)
        self.assertTrue(result)

    def test_should_not_publish_numeric_within_deadband(self):
        self.manager.last_values["Tag/Analog"] = 10.0
        result = self.manager.should_publish("Tag/Analog", 12.0, 1)
        self.assertFalse(result)

    def test_should_publish_boolean_changed(self):
        self.manager.last_values["Tag/Boolean"] = False
        result = self.manager.should_publish("Tag/Boolean", True, 12)
        self.assertTrue(result)

    def test_should_not_publish_boolean_same(self):
        self.manager.last_values["Tag/Boolean"] = True
        result = self.manager.should_publish("Tag/Boolean", True, 12)
        self.assertFalse(result)

    def test_update_last_value(self):
        self.manager.update_last_value("Tag/Test", 42)
        self.assertEqual(self.manager.last_values["Tag/Test"], 42)

    def test_reset(self):
        self.manager.last_values["Tag/Test"] = 100
        self.manager.reset()
        self.assertEqual(self.manager.last_values, {})


if __name__ == "__main__":
    unittest.main()
