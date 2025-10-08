import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def get_forecast(lat, lng, days=5):
    """Récupère les prévisions météo marines horaires depuis Open-Meteo avec la librairie officielle."""
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": [
            "wave_height", "wave_direction", "wave_period",
            "wind_wave_height", "wind_wave_direction", "wind_wave_period"
        ],
        "forecast_days": days,
        "timezone": "Europe/Lisbon"
    }
    print(f"[DEBUG] Appel Open-Meteo : {params}")
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        hourly = response.Hourly()
        hourly_wave_height = hourly.Variables(0).ValuesAsNumpy()
        hourly_wave_direction = hourly.Variables(1).ValuesAsNumpy()
        hourly_wave_period = hourly.Variables(2).ValuesAsNumpy()
        hourly_wind_wave_height = hourly.Variables(3).ValuesAsNumpy()
        hourly_wind_wave_direction = hourly.Variables(4).ValuesAsNumpy()
        hourly_wind_wave_period = hourly.Variables(5).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )}
        hourly_data["wave_height"] = hourly_wave_height
        hourly_data["wave_direction"] = hourly_wave_direction
        hourly_data["wave_period"] = hourly_wave_period
        hourly_data["wind_wave_height"] = hourly_wind_wave_height
        hourly_data["wind_wave_direction"] = hourly_wind_wave_direction
        hourly_data["wind_wave_period"] = hourly_wind_wave_period

        return pd.DataFrame(data=hourly_data)
    except Exception as e:
        print(f"[ERROR] Erreur Open-Meteo : {e}")
        raise
