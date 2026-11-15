
from functools import lru_cache

import geopandas as gpd

from fastapi import APIRouter, HTTPException

from backend.routes import load_districts
from backend.forecasting.weather_api import (
    fetch_all_district_forecasts
)

router = APIRouter(prefix="/api", tags=["15-Day Forecast"])


@lru_cache(maxsize=1)
def load_all_forecasts():

    gdf = load_districts().copy()

    # Calculate representative points in a projected CRS.
    projected = gdf.to_crs("EPSG:6933")
    points = projected.geometry.representative_point()
    points = points.to_crs("EPSG:4326")

    districts = []

    for index, row in gdf.iterrows():

        point = points.loc[index]

        districts.append({
            "district": str(row["district"]),
            "state": str(row["state"]),
            "district_code": str(row["district_code"]),
            "latitude": float(point.y),
            "longitude": float(point.x)
        })

    return fetch_all_district_forecasts(districts)


@router.get("/forecast/15-day")
def get_15_day_forecast():

    try:
        forecasts = load_all_forecasts()

        return {
            "total_districts": len(forecasts),
            "forecast_days": 15,
            "source": "Open-Meteo",
            "forecasts": forecasts
        }

    except Exception as error:

        print("Forecast API error:", repr(error))

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve rainfall forecasts."
        )
