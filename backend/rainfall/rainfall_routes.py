
from pathlib import Path
from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["Rainfall"])

BASE_DIR = Path(__file__).resolve().parents[2]

CSV_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "rainfall"
    / "rainfall_districtwise_daily_imd.csv"
)


def normalize(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("&", "and")
        .replace("-", " ")
        .split()
    )


@lru_cache(maxsize=1)
def get_rainfall_data():

    df = pd.read_csv(CSV_PATH)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Daily Actual"] = pd.to_numeric(
        df["Daily Actual"], errors="coerce"
    )

    df = df[
        (df["Date"].dt.year == 2026)
        & df["Daily Actual"].notna()
    ].copy()

    if df.empty:
        raise ValueError("No 2026 rainfall records found.")

    # Aggregate daily rainfall by district and state
    grouped = (
        df.groupby(["State", "District"], as_index=False)
        .agg(
            rainfall_mm=("Daily Actual", "sum"),
            last_updated=("Date", "max")
        )
    )

    records = []

    for _, row in grouped.iterrows():
        records.append({
            "state": str(row["State"]).strip(),
            "district": str(row["District"]).strip().replace("_", " "),
            "rainfall_mm": round(float(row["rainfall_mm"]), 2),
            "data_through": row["last_updated"].strftime("%Y-%m-%d")
        })

    return records, {
        "data_from": df["Date"].min().strftime("%Y-%m-%d"),
        "data_through": df["Date"].max().strftime("%Y-%m-%d"),
        "year": 2026
    }


@router.get("/rainfall/annual")
def annual_rainfall():

    try:
        records, metadata = get_rainfall_data()

        highest = max(
            records,
            key=lambda item: item["rainfall_mm"],
            default=None
        )

        average = (
            sum(r["rainfall_mm"] for r in records) / len(records)
            if records else 0
        )

        return {
            **metadata,
            "total_districts": len(records),
            "average_rainfall_mm": round(average, 2),
            "highest_rainfall": highest,
            "districts": records
        }

    except Exception as error:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
