
import json
import requests

from langchain_core.tools import tool


@tool
def get_weather_forecast(city: str, forecast_days: int = 7) -> str:
    """
    Get current weather and daily forecast for a city
    using the Open-Meteo weather API.
    """

    try:
        if not 1 <= forecast_days <= 7:
            return json.dumps({
                "status": "error",
                "message": "forecast_days must be between 1 and 7."
            }, indent=2)

        # Step 1: Find city coordinates.
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_response = requests.get(
            geo_url,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )

        geo_response.raise_for_status()
        geo_data = geo_response.json()

        locations = geo_data.get("results", [])

        if not locations:
            return json.dumps({
                "status": "error",
                "message": f"Location not found: {city}"
            }, indent=2)

        location = locations[0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        # Step 2: Retrieve current weather and daily forecast.
        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_response = requests.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m"
                ],
                "daily": [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max"
                ],
                "forecast_days": forecast_days,
                "timezone": "auto"
            },
            timeout=20
        )

        weather_response.raise_for_status()
        weather_data = weather_response.json()

        return json.dumps({
            "status": "success",
            "city": location.get("name"),
            "country": location.get("country"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_data.get("timezone"),
            "forecast_days": forecast_days,
            "current_weather": weather_data.get("current"),
            "daily_forecast": weather_data.get("daily"),
            "units": {
                "current": weather_data.get("current_units"),
                "daily": weather_data.get("daily_units")
            },
            "notice": (
                "Weather information is retrieved from Open-Meteo. "
                "Forecast availability depends on the requested dates "
                "and the API forecast horizon."
            )
        }, indent=2)

    except requests.exceptions.Timeout:
        return json.dumps({
            "status": "error",
            "message": "Weather service timed out. Please try again."
        }, indent=2)

    except requests.exceptions.RequestException as error:
        return json.dumps({
            "status": "error",
            "message": f"Weather API request failed: {error}"
        }, indent=2)

    except (KeyError, ValueError, TypeError) as error:
        return json.dumps({
            "status": "error",
            "message": f"Error processing weather data: {error}"
        }, indent=2)
