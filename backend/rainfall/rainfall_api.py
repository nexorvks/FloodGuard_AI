
import requests

import time

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_rainfall_batch(districts):

    if not districts:
        return []

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()

    # ERA5-Land data is generally available with a delay.
    end_date = today - timedelta(days=5)

    params = {
        "latitude": ",".join(
            str(d["latitude"]) for d in districts
        ),
        "longitude": ",".join(
            str(d["longitude"]) for d in districts
        ),
        "start_date": f"{today.year}-01-01",
        "end_date": end_date.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
        "models": "era5"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    results = response.json()

    if isinstance(results, dict):
        results = [results]

    output = []

    for district, weather in zip(districts, results):

        daily = weather.get("daily", {})
        rainfall_values = daily.get("precipitation_sum", [])

        total_rainfall = round(
            sum(value for value in rainfall_values if value is not None),
            2
        )

        output.append({
            **district,
            "rainfall_mm": total_rainfall,
            "data_from": f"{today.year}-01-01",
            "data_through": end_date.isoformat(),
            "daily": [
                {
                    "date": date,
                    "rainfall_mm": rainfall
                }
                for date, rainfall in zip(
                    daily.get("time", []),
                    rainfall_values
                )
            ]
        })

    return output


def fetch_all_rainfall(districts, batch_size=10):
    output = []

    for start in range(0, len(districts), batch_size):
        batch = districts[start:start + batch_size]

        for attempt in range(5):
            try:
                output.extend(fetch_rainfall_batch(batch))
                break

            except requests.exceptions.HTTPError as error:
                if error.response is None or error.response.status_code != 429:
                    raise

                wait = int(error.response.headers.get("Retry-After", 10))
                print(f"Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)

        else:
            raise Exception("Open-Meteo rate limit exceeded after retries.")

        time.sleep(2)

    return output