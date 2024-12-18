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
SCOPE = "user-read-recently-played user-read-private user-read-email playlist-read-private"
STATE = "spotify_auth"

# Step 1: Get Spotify authorization URL
def get_auth_url():
    auth_url = f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={REDIRECT_URI}&state={STATE}"
    return auth_url

# Step 2: Exchange authorization code for access and refresh tokens
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

    # Handle potential errors in token response
    if response.status_code != 200:
        print(f"Failed to get tokens: {response.status_code} - {response.text}")
        return None
    return response.json()

# Step 3: Save access and refresh tokens in session
def save_tokens(tokens):
    # Check if the tokens are valid
    if tokens and 'access_token' in tokens:
        session['access_token'] = tokens.get('access_token')
        session['refresh_token'] = tokens.get('refresh_token')
        session.modified = True
    else:
        raise ValueError("Failed to save tokens. Invalid tokens received.")

# Step 4: Fetch user playlists
def get_user_playlists():
    access_token = session.get('access_token')

    # If no access token, redirect to login
    if not access_token:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/me/playlists", headers=headers)

    # Handle response errors
    if response.status_code != 200:
        print(f"Failed to fetch playlists: {response.status_code} - {response.text}")
        return []

    return response.json().get('items', [])

# Step 5: Fetch playlists based on mood
def get_mood_playlists(mood):
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        f"{SPOTIFY_API_URL}/search",
        headers=headers,
        params={
            "q": mood,
            "type": "playlist",
            "limit": 5
        }
    )

    if response.status_code == 401:  # Token expired, handle it by re-authenticating or refreshing the token
        refresh_token = session.get('refresh_token')
        if refresh_token:
            # Add token refresh logic
            refresh_response = requests.post(SPOTIFY_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            })
            if refresh_response.status_code == 200:
                tokens = refresh_response.json()
                session['access_token'] = tokens.get('access_token')
                # Retry the original request with the new token
                headers['Authorization'] = f"Bearer {tokens['access_token']}"
                response = requests.get(
                    f"{SPOTIFY_API_URL}/search",
                    headers=headers,
                    params={"q": mood, "type": "playlist", "limit": 5}
                )
            else:
                print("Failed to refresh token")
                return []
        else:
            return redirect(url_for('login'))

    if response.status_code == 200:
        return response.json().get('playlists', {}).get('items', [])
    else:
        print(f"Failed to retrieve playlists: {response.status_code}")
        return []

# Function to get the last 20 songs listened by the user
def get_user_recent_tracks(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{SPOTIFY_API_URL}/me/player/recently-played?limit=20', headers=headers)

    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print(f"Failed to retrieve tracks: {response.status_code}")
        return []

# Function to get candidate songs for a mood
def get_candidate_songs(mood, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    query = mood
    response = requests.get(f'{SPOTIFY_API_URL}/search?q={query}&type=track&limit=50', headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve candidate songs: {response.status_code}")
        return []

    # Retrieve the list of tracks
    tracks = response.json().get('tracks', {}).get('items', [])
    if not tracks:
        return []

    # Extract track IDs for audio features
    track_ids = [track['id'] for track in tracks]
    audio_features = get_audio_features_for_tracks(track_ids, access_token)

    # Attach audio features to each track
    for track in tracks:
        track_id = track['id']
        track['audio_features'] = audio_features.get(track_id, {})

    return tracks

def get_audio_features_for_tracks(track_ids, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SPOTIFY_API_URL}/audio-features"
    response = requests.get(url, headers=headers, params={"ids": ",".join(track_ids)})

    if response.status_code == 200:
        return {feature['id']: feature for feature in response.json().get('audio_features', [])}
    else:
        print("Failed to retrieve audio features.")
        return {}
    
def get_audio_features_for_tracks(track_ids, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SPOTIFY_API_URL}/audio-features"
    response = requests.get(url, headers=headers, params={"ids": ",".join(track_ids)})

    if response.status_code == 200:
        return {feature['id']: feature for feature in response.json().get('audio_features', [])}
    else:
        print("Failed to retrieve audio features.")
        return {}

def get_user_recent_tracks_with_features():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    user_history = get_user_recent_tracks(access_token)
    track_ids = [track['track']['id'] for track in user_history]
    features = get_audio_features_for_tracks(track_ids, access_token)

    # Attach features to each track
    for track in user_history:
        track_id = track['track']['id']
        track['audio_features'] = features.get(track_id, {})

    return user_history



def refresh_token():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('login'))  # If no refresh token, user needs to log in again

    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)
    
    # Handle response errors
    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(new_tokens)  # Save new tokens in session
        return True
    else:
        print(f"Failed to refresh token: {response.status_code} - {response.text}")
        return False
