import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app import fetch_weather_data, map_weather_to_mood, app

class TestWeatherData(unittest.TestCase):
    def test_valid_city(self):
        weather_data = fetch_weather_data("New York")
        self.assertIsNotNone(weather_data)
        self.assertIn('main', weather_data)
    
    def test_invalid_city(self):
        weather_data = fetch_weather_data("InvalidCity")
        self.assertIsNone(weather_data)  # Expect None for invalid city

    def test_api_failure(self):
        city = "InvalidCity"
        weather_data = fetch_weather_data(city)
        self.assertIsNone(weather_data)  # Expect None for failed API calls

class TestMoodMapping(unittest.TestCase):
    def test_clear_weather(self):
        weather_data = {
            'main': {'temp': 35, 'humidity': 60},
            'weather': [{'main': 'Clear'}],
            'wind': {'speed': 3},
            'sys': {'sunrise': 1630569600, 'sunset': 1630612800},
            'visibility': 10000,
            'dt': 1630590000  # Current time during the day
        }
        mood = map_weather_to_mood(weather_data)
        self.assertEqual(mood, "Vibrant and Happy")
    
    def test_warm_and_relaxed_night(self):
        weather_data = {
            'main': {'temp': 35, 'humidity': 60},
            'weather': [{'main': 'Clear'}],
            'wind': {'speed': 3},
            'sys': {'sunrise': 1630569600, 'sunset': 1630612800},
            'visibility': 10000,
            'dt': 1630620000  # Current time during the night
        }
        mood = map_weather_to_mood(weather_data)
        self.assertEqual(mood, "Warm and Relaxed")
    
    def test_edge_case_weather(self):
        # Edge case: Normal temperature, high wind speed, rain, and low visibility
        weather_data = {
            'main': {'temp': 20, 'humidity': 70},
            'weather': [{'main': 'Rain'}],
            'wind': {'speed': 12},  # High wind speed (edge case)
            'sys': {'sunrise': 1630569600, 'sunset': 1630612800},
            'visibility': 1500,  # Low visibility (edge case)
            'dt': 1630590000  # Daytime
        }
        mood = map_weather_to_mood(weather_data)
        self.assertEqual(mood, "Mysterious")  # This mood is expected due to low visibility and rain

class TestUIIntegration(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_ui_loads_properly(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Get Weather', response.data)

    def test_valid_city_weather_display(self):
        response = self.app.post('/weather', data={'city': 'New York'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Weather in New York', response.data)
        self.assertIn(b'Mood:', response.data)

    def test_invalid_city_error_display(self):
        response = self.app.post('/weather', data={'city': 'InvalidCity'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Unable to retrieve weather data for InvalidCity', response.data)


if __name__ == '__main__':
    unittest.main()
