import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

def test_api_key(api_key: str) -> bool:
    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": "Imola", "limit": 1, "appid": api_key}
        r = requests.get(url, params=params, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def get_city_suggestions(query: str, owm_api_key: str) -> List[str]:
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {'q': query, 'limit': 5, 'appid': owm_api_key}
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 200:
        data = r.json()
        return [f"{item['name']}, {item['country']}" for item in data]
    return []

def geocode_city(city: str, owm_api_key: str) -> Tuple[Optional[float], Optional[float]]:
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {'q': city, 'limit': 1, 'appid': owm_api_key}
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 200 and r.json():
        j = r.json()[0]
        return j['lat'], j['lon']
    return None, None

def get_historical_weather_data(lat: float, lon: float, start_date, end_date, owm_api_key: str) -> Optional[list]:
    """Daily aggregates (mean temp/humidity) from OWM historical endpoint (paid)."""
    weather_data = []
    date = start_date
    while date <= end_date:
        timestamp = int(datetime.combine(date, datetime.min.time()).timestamp())
        url = "http://history.openweathermap.org/data/2.5/history/city"
        params = {
            'lat': lat, 'lon': lon, 'type': 'hour',
            'start': timestamp, 'end': timestamp + 86400,
            'units': 'metric', 'appid': owm_api_key
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            temps, hums = [], []
            for item in data.get('list', []):
                temps.append(item['main']['temp'])
                hums.append(item['main']['humidity'])
            if temps and hums:
                weather_data.append({
                    'date': date,
                    'temperature': sum(temps)/len(temps),
                    'humidity': sum(hums)/len(hums)
                })
        except Exception:
            return None
        date += timedelta(days=1)
    return weather_data

def get_future_weather_exog(lat: float, lon: float, owm_api_key: str, horizon_days: int = 7) -> Optional[list]:
    """Aggregate 5-day/3-hour forecast to daily means for exogenous variables."""
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {'lat': lat, 'lon': lon, 'appid': owm_api_key, 'units': 'metric'}
    r = requests.get(url, params=params, timeout=20)
    if r.status_code != 200:
        return None
    data = r.json().get('list', [])
    buckets = {}
    for item in data:
        dt = datetime.fromtimestamp(item['dt'])
        key = dt.date()
        buckets.setdefault(key, {'temps': [], 'hums': []})
        buckets[key]['temps'].append(item['main']['temp'])
        buckets[key]['hums'].append(item['main']['humidity'])
    rows = []
    for d in sorted(buckets.keys())[:horizon_days]:
        rows.append({
            'date': d,
            'temperature': sum(buckets[d]['temps'])/len(buckets[d]['temps']),
            'humidity': sum(buckets[d]['hums'])/len(buckets[d]['hums']),
        })
    return rows or None
