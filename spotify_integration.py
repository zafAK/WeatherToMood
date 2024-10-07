# spotify_integration.py

import os
import requests
from flask import session, redirect, url_for

# Spotify API configuration
CLIENT_ID = 'aa15a3d54b0f47f8ac487de29a313b1c'
CLIENT_SECRET = 'c5d6424aad2a4c7eb72c261cccb4eb53'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"
SCOPE = "user-read-private user-read-email playlist-read-private"
STATE = "spotify_auth"

def get_auth_url():
    auth_url = f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={REDIRECT_URI}&state={STATE}"
    return auth_url

def get_tokens(auth_code):
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(SPOTIFY_TOKEN_URL, data=token_data, headers=headers)
    return response.json()

def save_tokens(tokens):
    session['access_token'] = tokens.get('access_token')
    session['refresh_token'] = tokens.get('refresh_token')


#PLACE HOLDING THESE FUNCTIONS FOR NEXT USER STORY TOO
def get_user_playlists():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/me/playlists", headers=headers)
    return response.json().get('items', [])

# Function to fetch playlists by mood
def get_mood_playlists(mood):
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/browse/categories/{mood}/playlists", headers=headers)
    return response.json().get('playlists', {}).get('items', [])
