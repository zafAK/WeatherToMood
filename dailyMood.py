import requests
from flask import Flask, jsonify
from collections import Counter
from spotify_integration import get_user_recent_tracks, get_candidate_songs, refresh_token

# Function to determine mood based on valence and energy
def determine_song_mood(valence, energy):
    """
    Determines the mood of a song based on its valence and energy values.
    """
    if valence >= 0.7 and energy >= 0.7:
        return "Happy"
    elif valence < 0.4 and energy >= 0.6:
        return "Energetic"
    elif valence < 0.4 and energy < 0.4:
        return "Sad"
    elif valence >= 0.4 and energy >= 0.4:
        return "Calm"
    else:
        return "Neutral"

# Function to generate the daily mood summary
def generate_daily_mood_summary(access_token):
    listening_history = get_user_recent_tracks(access_token)

    if not listening_history:
        return {"mood_label": "Neutral", "summary": "No listening history available for today."}

    mood_counts = Counter()
    for track in listening_history:
        valence = track['audio_features']['valence']
        energy = track['audio_features']['energy']
        mood = determine_song_mood(valence, energy)
        mood_counts[mood] += 1

    predominant_mood = mood_counts.most_common(1)[0][0]
    summary = f"Today's predominant mood based on your listening history is '{predominant_mood}'."

    return {
        "mood_label": predominant_mood,
        "summary": summary
    }

def get_top_songs_for_mood(listening_history, mood):

    mood_scores = []
    for track in listening_history:
        valence = track['audio_features']['valence']
        energy = track['audio_features']['energy']
        track_mood = determine_song_mood(valence, energy)
        if track_mood == mood:
            mood_scores.append((track['name'], valence + energy))  # Example scoring

    mood_scores.sort(key=lambda x: x[1], reverse=True)
    return [track for track, _ in mood_scores[:3]]

def analyze_mood_trend(mood_history):
    mood_counts = Counter(mood_history)
    total_days = len(mood_history)
    trend = {mood: (count / total_days) * 100 for mood, count in mood_counts.items()}
    return trend