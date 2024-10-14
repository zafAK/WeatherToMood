from flask import Flask, render_template, request, redirect, session, url_for
import requests
import os
from datetime import datetime
from spotify_integration import get_auth_url, get_tokens, save_tokens, get_user_playlists, get_mood_playlists

app = Flask(__name__)
app.secret_key = os.urandom(24)

API_KEY = '9115764ccc5b2d7dc29ea05ef54582a4'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form['city']
    weather_data = fetch_weather_data(city)
    mood = map_weather_to_mood(weather_data)
    # Fetch mood-based playlists from Spotify
    mood_playlists = get_mood_playlists(mood)
    
    if weather_data:
        # Render the mood-based playlists on a separate template
        return render_template('index.html', city=city, weather=weather_data, mood=mood, playlists=mood_playlists)
    # elif(weather_data[3]):
    #     return f"<h3>Could not retrieve playlists for mood: {mood}</h3>"
    else:
        return render_template('error.html', city=city)

@app.route('/login')
def login():
    return redirect(get_auth_url())

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    if auth_code:
        tokens = get_tokens(auth_code)
        save_tokens(tokens)
        return redirect(url_for('index'))
    else:
        return "Authorization failed."

@app.route('/playlists')
def playlists():
    playlists = get_user_playlists()
    playlist_html = '<h2>Your Spotify Playlists</h2>'
    for playlist in playlists:
        playlist_html += f"<p>{playlist['name']}</p>"
    return playlist_html


def fetch_weather_data(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)

    if response.status_code != 200:
        return None

    print(f"Request URL: {url}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Data: {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        return None

def map_weather_to_mood(weather_data):
    temp = weather_data['main']['temp']
    weather_condition = weather_data['weather'][0]['main'].lower()
    wind_speed = weather_data['wind']['speed']
    humidity = weather_data['main']['humidity']
    visibility = weather_data.get('visibility', 10000) / 1000
    sunrise = weather_data['sys']['sunrise']
    sunset = weather_data['sys']['sunset']
    current_time = weather_data['dt']

    day_period = 'day' if sunrise <= current_time <= sunset else 'night'

    if temp > 30 and 'clear' in weather_condition and day_period == 'day':
        return "Vibrant and Happy"
    elif temp > 30 and 'clear' in weather_condition and day_period == 'night':
        return "Warm and Relaxed"
    elif temp > 25 and 'rain' in weather_condition:
        return "Cozy"
    elif temp < 10 and 'rain' in weather_condition:
        return "Sad"
    elif temp < 0 and 'snow' in weather_condition:
        return "Peaceful"
    elif 10 <= temp <= 25 and 'clouds' in weather_condition and wind_speed < 5:
        return "Thoughtful"
    elif wind_speed > 10 and humidity > 80:
        return "Restless"
    elif visibility < 2:
        return "Mysterious"
    elif 'thunderstorm' in weather_condition:
        return "Intense"
    elif day_period == 'night' and visibility < 2:
        return "Dark and Brooding"
    else:
        return "Balanced and Calm"

if __name__ == '__main__':
    app.run(debug=True)
