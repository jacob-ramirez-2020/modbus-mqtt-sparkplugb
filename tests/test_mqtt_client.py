import unittest
from unittest.mock import MagicMock, patch, call
from src.mqtt.mqtt_client import SparkplugClient


class TestSparkplugClient(unittest.TestCase):
    def setUp(self):
        # Patch dependencies
        patcher_config = patch("src.mqtt_client.load_config", return_value={
            "broker": "test-broker",
            "port": 1883,
            "client_id": "test-client",
            "username": "user",
            "password": "pass",
            "group_id": "test-group",
            "node_id": "test-node"
        })
        patcher_mqtt = patch("src.mqtt_client.mqtt.Client")
        patcher_latency = patch("src.mqtt_client.SparkplugClient.get_tcp_latency", return_value=42)

        self.addCleanup(patcher_config.stop)
        self.addCleanup(patcher_mqtt.stop)
        self.addCleanup(patcher_latency.stop)

        self.mock_config = patcher_config.start()
        self.mock_mqtt = patcher_mqtt.start()
        self.mock_latency = patcher_latency.start()

        self.mock_db = MagicMock()
        self.client = SparkplugClient(self.mock_db)

    def test_initial_connection_state(self):
        self.assertFalse(self.client.is_connected)
        self.assertEqual(self.client.messages_sent, 0)

    def test_authentication_is_set(self):
        self.client.client.username_pw_set.assert_called_once_with("user", "pass")

    def test_publish_increments_messages_sent(self):
        self.client.publish("topic", b"payload")
        self.assertEqual(self.client.messages_sent, 1)
        self.client.client.publish.assert_called_once()

    def test_get_group_and_node_id(self):
        self.assertEqual(self.client.get_group_id(), "test-group")
        self.assertEqual(self.client.get_node_id(), "test-node")

    def test_get_metrics_contains_expected_keys(self):
        metrics = self.client.get_metrics()
        for key in [
            "connected", "last_connection_time", "messages_sent",
            "reconnect_count", "latency_ms", "uptime_seconds"
        ]:
            self.assertIn(key, metrics)

    def test_socket_check_returns_false_if_disconnected(self):
        self.client.client._sock = None
        self.assertFalse(self.client.is_socket_connected())


if __name__ == "__main__":
    unittest.main()
