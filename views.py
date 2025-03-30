from django.shortcuts import render
import requests
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from datetime import datetime, timedelta
import pytz
import os
import threading

API_KEY = '945fad9b1a3b2b31409031a5c6b9ada3'
BASE_URL = 'https://api.openweathermap.org/data/2.5/'

# Global model initialization
models_initialized = False
init_lock = threading.Lock()

def initialize_models():
    global models_initialized
    with init_lock:
        if not models_initialized:
            try:
                csv_path = os.path.join('C:\\Users\\maste\\ai ml\\Google project\\weather.csv')
                df = pd.read_csv(csv_path)
                df = df.dropna().drop_duplicates()
                df.rename(columns={"MinTemp": "temp_min"}, inplace=True)

                # Prepare data
                compass = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                wind_encoder = LabelEncoder().fit(compass)
                df['WindGustDir'] = wind_encoder.transform(df['WindGustDir'])
                df['RainTomorrow'] = LabelEncoder().fit_transform(df['RainTomorrow'])

                # Train models
                X = df[['temp_min', 'MaxTemp', 'WindGustSpeed', 'WindGustDir', 'Humidity', 'Pressure', 'Temp']]
                y = df['RainTomorrow']
                global rain_model, temp_model, hum_model
                rain_model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X, y)

                # Temperature model
                X_temp, y_temp = [], []
                for i in range(len(df)-1):
                    X_temp.append(df['Temp'].iloc[i])
                    y_temp.append(df['Temp'].iloc[i+1])
                temp_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(np.array(X_temp).reshape(-1, 1), y_temp)

                # Humidity model
                X_hum, y_hum = [], []
                for i in range(len(df)-1):
                    X_hum.append(df['Humidity'].iloc[i])
                    y_hum.append(df['Humidity'].iloc[i+1])
                hum_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(np.array(X_hum).reshape(-1, 1), y_hum)

                models_initialized = True
                print("Models initialized successfully")
                
            except Exception as e:
                print(f"Initialization error: {str(e)}")

initialize_models()

def get_current_weather(city):
    try:
        url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'main' not in data or 'temp' not in data['main']:
            return {'error': 'Invalid API response'}
            
        return {
            'city': data.get('name', 'Unknown'),
            'current_temp': round(data['main']['temp']),
            'humidity': round(data['main'].get('humidity', 0)),
            'temp_min': round(data['main'].get('temp_min', 0)),
            'temp_max': round(data['main'].get('temp_max', 0)),
            'feels_like': round(data['main'].get('feels_like', 0)),
            'description': data.get('weather', [{}])[0].get('description', 'Unknown').lower(),
            'country': data.get('sys', {}).get('country', 'Unknown'),
            'wind': data.get('wind', {}).get('speed', 0),
            'pressure': data.get('main', {}).get('pressure', 0),
            'visibility': data.get('visibility', 0)
        }
        
    except Exception as e:
        return {'error': f"Error: {str(e)}"}

def predict_future(model, current_value):
    try:
        predictions = [float(current_value)]
        for _ in range(4):  # Predict 4 values for 4 time slots
            next_val = model.predict([[predictions[-1]]])[0]
            predictions.append(round(float(next_val), 1))
        return predictions[1:]
    except:
        return [current_value]*4

def weather_view(request):
    context = {
        'error': None,
        'times': [],
        'temps': [],
        'hums': [],
        'weather_class': 'clear'
    }
    
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if not city:
            context['error'] = "Please enter a city name"
            return render(request, 'weather.html', context)
        
        current_weather = get_current_weather(city)
        if 'error' in current_weather:
            context['error'] = current_weather['error']
            return render(request, 'weather.html', context)
        
        try:
            # Generate predictions
            current_temp = current_weather['current_temp']
            future_temp = predict_future(temp_model, current_temp)
            future_humidity = predict_future(hum_model, current_weather['humidity'])
            
            # Prepare time labels
            tz = pytz.timezone('Asia/Karachi')
            now = datetime.now(tz)
            times = [(now + timedelta(hours=i+1)).strftime("%H:00") for i in range(4)]
            
            context.update({
                'weather_class': current_weather['description'].replace(' ', '-'),
                'location': city,
                'current_temp': current_temp,
                'temp_min': current_weather['temp_min'],
                'temp_max': current_weather['temp_max'],
                'feels_like': current_weather['feels_like'],
                'humidity': current_weather['humidity'],
                'description': current_weather['description'].title(),
                'city_name': current_weather['city'],
                'country': current_weather['country'],
                'wind': current_weather['wind'],
                'pressure': current_weather['pressure'],
                'visibility': current_weather['visibility'],
                'times': times,
                'temps': future_temp,
                'hums': future_humidity
            })
            
        except Exception as e:
            context['error'] = f"Processing error: {str(e)}"

    return render(request, 'weather.html', context)