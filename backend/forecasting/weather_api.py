import requests

from typing import List

API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast_batch(districts: List[dict]) -> list:

    if not districts:
        return []

    params = {
        "latitude": ",".join(
            str(d["latitude"]) for d in districts
        ),
        "longitude": ",".join(
            str(d["longitude"]) for d in districts
        ),
        "daily": (
            "precipitation_sum,"
            "precipitation_probability_max"
        ),
        "forecast_days": 15,
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    # Open-Meteo returns a list for multiple coordinates.
    if isinstance(result, dict):
        result = [result]

    forecasts = []

    for district, weather in zip(districts, result):

        daily = weather.get("daily", {})

        forecasts.append({
            "district": district["district"],
            "state": district["state"],
            "district_code": district["district_code"],
            "latitude": district["latitude"],
            "longitude": district["longitude"],
            "forecast": [
                {
                    "date": date,
                    "rainfall_mm": rainfall or 0,
                    "rain_probability": probability or 0
                }
                for date, rainfall, probability in zip(
                    daily.get("time", []),
                    daily.get("precipitation_sum", []),
                    daily.get(
                        "precipitation_probability_max", []
                    )
                )
            ]
        })

    return forecasts


def fetch_all_district_forecasts(
    districts: List[dict],
    batch_size: int = 40
) -> list:

    all_forecasts = []

    for start in range(0, len(districts), batch_size):

        batch = districts[start:start + batch_size]

        forecasts = fetch_forecast_batch(batch)

        all_forecasts.extend(forecasts)

    return all_forecasts