from flask import Flask, render_template, request
import requests

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
        return render_template('weather.html', city=city, weather=weather_data)
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
    
if __name__ == '__main__':
    app.run(debug=True)
