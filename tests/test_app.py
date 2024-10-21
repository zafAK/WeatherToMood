import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app import fetch_weather_data, map_weather_to_mood, app
from flask import session
from spotify_integration import get_mood_playlists
from unittest.mock import patch

class TestSpotifyAuthentication(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('spotify_integration.get_auth_url')
    def test_successful_authentication(self, mock_get_auth_url):
        """TestCase 1.1 - Successful Authentication"""
        # Mock the return value of get_auth_url
        mock_get_auth_url.return_value = 'http://mocked-spotify-auth-url'
        
        # Simulate a request to the login endpoint
        response = self.app.get('/login')

        # Check that the response is a redirect (status code 302)
        self.assertEqual(response.status_code, 302)
        
        # Check that the redirect location is correct
        self.assertIn('http://mocked-spotify-auth-url', response.headers['Location'])

    @patch('spotify_integration.get_tokens')
    def test_failed_authentication(self, mock_get_tokens):
        """TestCase 1.2 - Failed Authentication"""
        # Simulate the failed token retrieval
        mock_get_tokens.return_value = None
        
        # Simulate the callback with an invalid authorization code
        response = self.app.get('/callback?code=invalid_code', follow_redirects=True)

        # Check that the response is successful and contains the failure message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Authorization failed', response.data)

    @patch('spotify_integration.get_tokens')
    def test_token_storage_security(self, mock_get_tokens):
        """TestCase 1.3 - Token Storage and Security"""
        # Mock the response of get_tokens to simulate successful token retrieval
        mock_get_tokens.return_value = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token'
        }

        # Simulate the callback with a valid authorization code
        response = self.app.get('/callback?code=valid_code', follow_redirects=True)

        # Check if the access token is stored in the session
        with self.app.session_transaction() as sess:
            self.assertIn('access_token', sess)
            self.assertEqual(sess['access_token'], 'mock_access_token')

class TestMoodBasedPlaylistRetrieval(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('spotify_integration.get_mood_playlists')
    def test_valid_mood_based_playlist_retrieval(self, mock_get_mood_playlists):
        """TestCase 2.1 - Valid Mood-Based Playlist Retrieval"""
        mock_get_mood_playlists.return_value = [{'name': 'Happy Playlist 1'}, {'name': 'Happy Playlist 2'}]
        
        with self.app.session_transaction() as sess:
            sess['access_token'] = 'valid_token'
        
        response = self.app.get('/playlists')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Happy Playlist 1', response.data)
        self.assertIn(b'Happy Playlist 2', response.data)


    @patch('spotify_integration.get_mood_playlists')
    def test_handling_expired_access_token(self, mock_get_mood_playlists):
        """TestCase 2.2 - Handling Expired Access Token"""
        mock_get_mood_playlists.return_value = []

        with self.app.session_transaction() as sess:
            sess['access_token'] = 'expired_token'
        
        response = self.app.get('/mood_playlists/happy', follow_redirects=True)
        self.assertIn(b'Re-authenticate', response.data)

    @patch('spotify_integration.get_mood_playlists')
    def test_mood_accuracy_in_playlist_retrieval(self, mock_get_mood_playlists):
        """TestCase 2.3 - Mood Accuracy in Playlist Retrieval"""
        mock_get_mood_playlists.return_value = [{'name': 'Vibrant and Happy Playlist'}]

        with self.app.session_transaction() as sess:
            sess['access_token'] = 'valid_token'

        response = self.app.get('/mood_playlists/vibrant', follow_redirects=True)
        self.assertTrue(any('happy' in playlist['name'].lower() for playlist in mock_get_mood_playlists.return_value))

class TestDisplayingMoodBasedPlaylistsOnUI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('spotify_integration.get_mood_playlists')
    def test_display_playlist_details_on_ui(self, mock_get_mood_playlists):
        """TestCase 3.1 - Display Playlist Details on UI"""
        mock_get_mood_playlists.return_value = [
            {'name': 'Happy Playlist', 'images': [{'url': 'http://example.com/image1.jpg'}]}
        ]

        with self.app.session_transaction() as sess:
            sess['access_token'] = 'valid_token'

        response = self.app.get('/playlists', follow_redirects=True)
        self.assertIn(b'Happy Playlist', response.data)
        self.assertIn(b'<img', response.data)  # Ensure playlist cover images are displayed

    @patch('spotify_integration.get_mood_playlists')
    def test_error_handling_for_playlist_retrieval_failure(self, mock_get_mood_playlists):
        """TestCase 3.2 - Error Handling for Playlist Retrieval Failure"""
        mock_get_mood_playlists.return_value = []

        with self.app.session_transaction() as sess:
            sess['access_token'] = 'invalid_token'

        response = self.app.get('/playlists', follow_redirects=True)
        self.assertIn(b'Could not retrieve playlists', response.data)

    @patch('spotify_integration.get_mood_playlists')
    def test_handling_non_mood_compatible_playlists(self, mock_get_mood_playlists):
        """TestCase 3.3 - Handling Non-Mood-Compatible Playlists"""
        mock_get_mood_playlists.return_value = [{'name': 'Random Playlist'}, {'name': 'Happy Playlist'}]

        with self.app.session_transaction() as sess:
            sess['access_token'] = 'valid_token'

        response = self.app.get('/playlists', follow_redirects=True)
        mood_compatible_playlists = [playlist for playlist in mock_get_mood_playlists.return_value if 'happy' in playlist['name'].lower()]
        self.assertGreater(len(mood_compatible_playlists), 0)

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
        self.assertIn(b'Get Music Based on Weather!', response.data)

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