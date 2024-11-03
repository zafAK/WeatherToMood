import requests
from flask import session, redirect, url_for
from spotify_integration import get_user_recent_tracks, get_candidate_songs, refresh_token

SPOTIFY_API_URL = "https://api.spotify.com/v1"

# Adjust weights based on mood (no duplicate mood mapping function here, just weight adjustment)
def adjust_weights_for_mood(mood):
    mood_weights = {
        'Vibrant and Happy': {'energy': 0.8, 'valence': 0.9, 'danceability': 0.7},
        'Warm and Relaxed': {'acousticness': 0.9, 'valence': 0.7, 'energy': 0.6},
        'Cozy': {'acousticness': 0.8, 'valence': 0.7, 'energy': 0.5},
        'Sad': {'acousticness': 0.7, 'valence': 0.3, 'energy': 0.4},
        'Peaceful': {'instrumentalness': 0.8, 'acousticness': 0.9}
    }
    return mood_weights.get(mood, {'energy': 0.5, 'valence': 0.5, 'danceability': 0.5})


def extract_audio_features(user_history):
    feature_totals = {'energy': 0, 'valence': 0, 'danceability': 0, 'acousticness': 0}
    count = 0
    
    for track in user_history:
        features = track.get('audio_features', {})
        if features:
            count += 1
            for key in feature_totals:
                feature_totals[key] += features.get(key, 0)

    if count == 0:
        return {key: 0 for key in feature_totals}
    
    return {key: value / count for key, value in feature_totals.items()}

# Calculate similarity score between user profile and candidate songs
def calculate_similarity(user_features, candidate_song_features, mood_weights):
    similarity_score = 0
    for feature, weight in mood_weights.items():
        user_value = user_features.get(feature, 0)
        candidate_value = candidate_song_features.get(feature, 0)
        similarity_score += weight * (1 - abs(user_value - candidate_value))
    return similarity_score / sum(mood_weights.values())


def get_or_create_playlist(mood, access_token):
    # Step 1: Check if playlist already exists
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/me/playlists", headers=headers)

    if response.status_code == 200:
        playlists = response.json().get('items', [])
        for playlist in playlists:
            if playlist['name'] == mood:
                return playlist['id']  # Return existing playlist ID

    # Step 2: Create playlist if not found
    data = {
        "name": mood,
        "description": f"A playlist for the {mood} mood",
        "public": False
    }
    response = requests.post(f"{SPOTIFY_API_URL}/users/me/playlists", headers=headers, json=data)
    if response.status_code == 201:
        return response.json().get('id')  # Return new playlist ID
    else:
        print("Failed to create playlist:", response.status_code, response.text)
        return None

def generate_playlist_for_mood(user_history, mood, access_token):
    mood_weights = adjust_weights_for_mood(mood)
    user_features = extract_audio_features(user_history)
    candidate_songs = get_candidate_songs(mood, access_token)

    # Score each candidate track
    scored_tracks = []
    for track in candidate_songs:
        track_features = track.get('audio_features', {})
        if track_features:
            similarity = calculate_similarity(user_features, track_features, mood_weights)
            scored_tracks.append((track, similarity))

    
    # Sort by similarity score
    scored_tracks.sort(key=lambda x: x[1])
    recommended_songs = [track for track, _ in scored_tracks[:20]]

    playlist_id = get_or_create_playlist(mood, access_token)
    if playlist_id:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        data = {"uris": [f"spotify:track:{track_id}" for track_id in recommended_songs]}
        response = requests.post(f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks", headers=headers, json=data)

        if response.status_code == 201:
            print("Tracks added to playlist")
        else:
            print("Failed to add tracks:", response.status_code, response.text)

    return recommended_songs





