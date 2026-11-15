
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from backend.routes import load_districts
from backend.rainfall.rainfall_api import fetch_all_rainfall

router = APIRouter(prefix="/api", tags=["Rainfall"])


@lru_cache(maxsize=1)
def get_rainfall_data():

    gdf = load_districts().copy()

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

    return fetch_all_rainfall(districts)


@router.get("/rainfall/annual")
def annual_rainfall():

    try:
        records = get_rainfall_data()

        highest = max(
            records,
            key=lambda item: item["rainfall_mm"],
            default=None
        )

        return {
            "year": 2026,
            "total_districts": len(records),
            "data_through": (
                records[0]["data_through"] if records else None
            ),
            "highest_rainfall": highest,
            "districts": records
        }


    except Exception as error:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(error))
