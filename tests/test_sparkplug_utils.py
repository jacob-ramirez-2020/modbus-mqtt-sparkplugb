import unittest
from unittest.mock import patch, MagicMock
from src.mqtt.sparkplug_utils import create_birth_payload


class TestSparkplugUtils(unittest.TestCase):
    @patch("src.sparkplug_utils.get_all_topics")
    @patch("src.sparkplug_utils.get_current_value")
    @patch("src.sparkplug_utils.get_location")
    @patch("src.sparkplug_utils.get_mac_address")
    @patch("src.sparkplug_utils.get_date_of_firmware")
    @patch("src.sparkplug_utils.get_firmware_version")
    @patch("src.sparkplug_utils.get_boot_time")
    @patch("src.sparkplug_utils.get_os_version")
    @patch("src.sparkplug_utils.get_os")
    @patch("src.sparkplug_utils.get_hardware_make")
    @patch("src.sparkplug_utils.sparkplug")
    def test_create_birth_payload_success(
        self,
        mock_sparkplug,
        mock_get_hardware_make,
        mock_get_os,
        mock_get_os_version,
        mock_get_boot_time,
        mock_get_firmware_version,
        mock_get_date_of_firmware,
        mock_get_mac_address,
        mock_get_location,
        mock_get_current_value,
        mock_get_all_topics,
    ):
        # Setup return values
        mock_payload = MagicMock()
        mock_sparkplug.getNodeBirthPayload.return_value = mock_payload
        mock_sparkplug.addMetric.return_value = MagicMock()

        mock_get_hardware_make.return_value = "TestVendor"
        mock_get_os.return_value = "Linux"
        mock_get_os_version.return_value = "1.0"
        mock_get_boot_time.return_value = 1234567890
        mock_get_firmware_version.return_value = "v1.2.3"
        mock_get_date_of_firmware.return_value = 1234567890123
        mock_get_mac_address.return_value = "00:11:22:33:44:55"
        mock_get_location.return_value = {
            "Lat": 12.34,
            "Long": 56.78,
            "Source": "GPS",
            "Valid": "true",
            "Timestamp": 1234567890123,
        }
        mock_get_current_value.return_value = 99.9
        mock_get_all_topics.return_value = [
            {"topic": "Tags/Test", "data_type": 1}
        ]

        mock_payload.SerializeToString.return_value = b"mock_serialized"

        db = MagicMock()
        result = create_birth_payload(db)

        # Assertions
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, b"mock_serialized")
        mock_sparkplug.getNodeBirthPayload.assert_called_once()
        self.assertGreater(mock_sparkplug.addMetric.call_count, 5)
        mock_payload.SerializeToString.assert_called_once()


if __name__ == "__main__":
    unittest.main()
