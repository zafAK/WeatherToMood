from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = '9115764ccc5b2d7dc29ea05ef54582a4'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form['city']
    weather_data = fetch_weather_data(city)
    
    if weather_data:
        mood = map_weather_to_mood(weather_data)
        return render_template('weather.html', city=city, weather=weather_data, mood=mood)
    else:
        return render_template('error.html', city=city)

def fetch_weather_data(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    
    print(f"Request URL: {url}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Data: {response.text}")  # To see the raw data returned by the API

    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def map_weather_to_mood(weather_data):
    """
    mood mapping from weather conditions.
    """
    temp = weather_data['main']['temp']
    weather_condition = weather_data['weather'][0]['main'].lower()
    wind_speed = weather_data['wind']['speed']
    humidity = weather_data['main']['humidity']
    visibility = weather_data.get('visibility', 10000) / 1000  # Convert to km
    sunrise = weather_data['sys']['sunrise']
    sunset = weather_data['sys']['sunset']
    current_time = weather_data['dt']
    
    # Convert times to datetime objects
    sunrise_time = datetime.utcfromtimestamp(sunrise)
    sunset_time = datetime.utcfromtimestamp(sunset)
    current_time = datetime.utcfromtimestamp(current_time)

    # Determine if it's day or night
    if sunrise_time <= current_time <= sunset_time:
        day_period = 'day'
    else:
        day_period = 'night'

    # Mood mapping based on detailed conditions
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
