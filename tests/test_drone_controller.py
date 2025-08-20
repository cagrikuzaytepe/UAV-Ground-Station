import unittest
from unittest.mock import MagicMock, patch
import time

# Assuming drone_controller.py is in src/core/
from src.core.drone_controller import DroneController

class TestDroneController(unittest.TestCase):

    @patch('src.core.drone_controller.connect')
    def setUp(self, mock_connect):
        # Mock the drone connection object
        self.mock_vehicle = MagicMock()
        mock_connect.return_value = self.mock_vehicle
        self.controller = DroneController()
        self.connection_string = "tcp:127.0.0.1:5760"

    def test_connect(self):
        self.controller.connect(self.connection_string)
        self.mock_vehicle.wait_ready.assert_called_once_with(True, timeout=60)
        self.assertTrue(self.controller.is_connected)

    def test_arm(self):
        self.controller.connect(self.connection_string)
        self.controller.arm()
        self.mock_vehicle.armed = True
        self.assertTrue(self.mock_vehicle.armed)

    def test_takeoff(self):
        self.controller.connect(self.connection_string)
        self.controller.arm()
        altitude = 10
        self.controller.takeoff(altitude)
        self.mock_vehicle.simple_takeoff.assert_called_once_with(altitude)
        # Simulate reaching target altitude
        self.mock_vehicle.location.global_relative_frame.alt = altitude
        self.mock_vehicle.mode.name = 'GUIDED'

    def test_land(self):
        self.controller.connect(self.connection_string)
        self.controller.land()
        self.mock_vehicle.mode.name = 'LAND'
        self.assertEqual(self.mock_vehicle.mode.name, 'LAND')

    def test_goto(self):
        self.controller.connect(self.connection_string)
        self.controller.arm()
        self.mock_vehicle.mode.name = 'GUIDED'
        target_location = MagicMock()
        target_location.lat = 34.0
        target_location.lon = -118.0
        target_location.alt = 50
        self.controller.goto(target_location.lat, target_location.lon, target_location.alt)
        self.mock_vehicle.simple_goto.assert_called_once()

    def test_set_mode(self):
        self.controller.connect(self.connection_string)
        mode = 'RTL'
        self.controller.set_mode(mode)
        self.mock_vehicle.mode = MagicMock(name=mode)
        self.assertEqual(self.mock_vehicle.mode.name, mode)

    def test_get_telemetry(self):
        self.controller.connect(self.connection_string)
        # Set mock telemetry data
        self.mock_vehicle.location.global_relative_frame.lat = 34.0
        self.mock_vehicle.location.global_relative_frame.lon = -118.0
        self.mock_vehicle.location.global_relative_frame.alt = 50.0
        self.mock_vehicle.groundspeed = 5.0
        self.mock_vehicle.airspeed = 5.0
        self.mock_vehicle.heading = 90
        self.mock_vehicle.battery.voltage = 12.5
        self.mock_vehicle.battery.current = 10.0
        self.mock_vehicle.battery.level = 80

        telemetry = self.controller.get_telemetry()

        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry['latitude'], 34.0)
        self.assertEqual(telemetry['longitude'], -118.0)
        self.assertEqual(telemetry['altitude'], 50.0)
        self.assertEqual(telemetry['groundspeed'], 5.0)
        self.assertEqual(telemetry['airspeed'], 5.0)
        self.assertEqual(telemetry['heading'], 90)
        self.assertEqual(telemetry['battery_voltage'], 12.5)
        self.assertEqual(telemetry['battery_current'], 10.0)
        self.assertEqual(telemetry['battery_level'], 80)

if __name__ == '__main__':
    unittest.main()