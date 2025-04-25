import unittest
from unittest.mock import MagicMock
from src import database  # Adjust if your import path differs


class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor

    def test_buffer_message_executes_and_commits(self):
        database.buffer_message(self.mock_db, "topic/test", b"payload", 1, False)
        self.mock_db.execute.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_flush_buffer_deletes_after_publish(self):
        self.mock_cursor.fetchall.return_value = [
            (1, "topic/1", b"data", 0, 0, "2024-01-01 00:00:00")
        ]
        mock_client = MagicMock()
        database.flush_buffer(self.mock_db, mock_client)
        mock_client.publish.assert_called_once()
        self.mock_cursor.execute.assert_any_call("DELETE FROM mqtt_buffer")
        self.mock_db.commit.assert_called()

    def test_get_all_topics_returns_expected_structure(self):
        self.mock_cursor.fetchall.return_value = [("topic/1", "Float")]
        result = database.get_all_topics(self.mock_db)
        self.assertEqual(result, [{"topic": "topic/1", "data_type": "Float"}])

    def test_get_db_buffer_metrics_returns_dict(self):
        self.mock_cursor.fetchone.return_value = (5, 2048, "2024-01-01 00:00:00")
        result = database.get_db_buffer_metrics(self.mock_db)
        self.assertEqual(result["buffer_message_count"], 5)
        self.assertEqual(result["buffer_size_bytes"], 2048)
        self.assertEqual(result["buffer_oldest_timestamp"], "2024-01-01 00:00:00")

    def test_load_config_returns_expected_keys(self):
        self.mock_cursor.fetchone.side_effect = [
            (
                1,
                "broker",
                1883,
                "client_id",
                "user",
                "pass",
                "group",
                "node",
                "device",
            ),
            ("system_setting",),
        ]
        config = database.load_config(self.mock_db)
        expected_keys = {
            "broker",
            "port",
            "client_id",
            "username",
            "password",
            "group_id",
            "node_id",
            "device_id",
        }
        self.assertTrue(expected_keys.issubset(config.keys()))


if __name__ == "__main__":
    unittest.main()
