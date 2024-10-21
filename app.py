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
    
    if not weather_data:
        return render_template('error.html', city=city, error="Weather data not available.")
    
    mood = map_weather_to_mood(weather_data)
    
    # Fetch mood-based playlists only if the user is logged in
    mood_playlists = None
    if 'access_token' in session:
        mood_playlists = get_mood_playlists(mood)
    
    return render_template('index.html', city=city, weather=weather_data, mood=mood, playlists=mood_playlists)

@app.route('/login')
def login():
    return redirect(get_auth_url())

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    if not auth_code:
        return "Authorization failed. No code provided."

    tokens = get_tokens(auth_code)
    if tokens is None or 'access_token' not in tokens:
        return "Authorization failed. Invalid tokens."

    save_tokens(tokens)
    return redirect(url_for('index'))

@app.route('/playlists')
def playlists():
    if 'access_token' not in session:
        return redirect(url_for('login'))

    playlists = get_user_playlists()
    return render_template('playlists.html', playlists=playlists)

# Function to fetch weather data (no changes needed)
def fetch_weather_data(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
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
