
import json
import joblib
import numpy as np
import pandas as pd
import geopandas as gpd

from pathlib import Path
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.schemas import PredictionRequest, PredictionResponse


router = APIRouter(prefix="/api")

# ----------------------------------
# PROJECT PATHS
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MODEL_DIR = BASE_DIR / "backend" / "models"

MODEL_PATH = MODEL_DIR / "floodguard_model.joblib"
FEATURES_PATH = MODEL_DIR / "model_features.joblib"

DATASET_PATH = (
    DATA_DIR / "raw" / "geo" / "LGD_Districts.parquet"
)

FLOOD_DIR = DATA_DIR / "raw" / "floods"

RAINFALL_PATH = (
    DATA_DIR / "raw" / "rainfall" /
    "rainfall_districtwise_daily_imd.csv"
)

DFSI_PATH = FLOOD_DIR / "DFSI.csv"

GEOMETRY_TOLERANCE = 0.005


# ----------------------------------
# COMMON HELPERS
# ----------------------------------

def normalize(value):
    value = str(value).strip().lower()
    value = value.replace("&", "and")
    value = " ".join(value.split())

    aliases = {
        "shimoga": "shivamogga",
        "mysore": "mysuru",
        "chikmagalur": "chikkamagaluru",
        "bellary": "ballari",
        "gulbarga": "kalaburagi",
        "bijapur": "vijayapura",
        "belgaum": "belagavi",
        "tumkur": "tumakuru",
        "chikballapur": "chikkaballapura",
        "ranga reddy": "rangareddy"
    }

    return aliases.get(value, value)


def normalize_code(value):

    return str(value).strip().replace(".0", "")


def clean_records(df):

    records = (
        df.astype(object)
        .where(pd.notna(df), None)
        .to_dict("records")
    )

    return records


# ----------------------------------
# LOAD TRAINED ML MODEL
# ----------------------------------

@lru_cache(maxsize=1)
def load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Feature file not found: {FEATURES_PATH}"
        )

    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)

    return model, features


# ----------------------------------
# SINGLE DISTRICT PREDICTION API
# ----------------------------------

@router.post(
    "/predict",
    response_model=PredictionResponse
)
def predict(req: PredictionRequest):

    try:

        model, features = load_model()

        input_values = {

            "Daily Actual": req.daily_actual,
            "Daily Normal": req.daily_normal,

            "Weekly \nActual": req.weekly_actual,
            "Weekly Normal": req.weekly_normal,

            "Cumulative Actual": req.cumulative_actual,
            "Cumulative Normal": req.cumulative_normal,

            "Monthly Acutual": req.monthly_actual,
            "Monthly Normal": req.monthly_normal,

            "dfsi_score": req.dfsi_score
        }

        missing_features = [
            feature for feature in features
            if feature not in input_values
        ]

        if missing_features:
            raise ValueError(
                f"Missing model features: {missing_features}"
            )

        input_df = pd.DataFrame(
            [[input_values[feature] for feature in features]],
            columns=features
        )

        prediction = model.predict(input_df)[0]

        probability = None

        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(input_df)[0]

            predicted_index = list(model.classes_).index(
                prediction
            )

            probability = float(
                probabilities[predicted_index]
            )

        return {
            "risk_level": str(prediction).lower(),
            "probability": probability
        }

    except Exception as error:

        print("Prediction error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to generate flood risk prediction."
        )


# ----------------------------------
# LOAD DISTRICT-WISE RISK PREDICTIONS
# ----------------------------------

@lru_cache(maxsize=1)
def load_risk_predictions():

    if not RAINFALL_PATH.exists():
        raise FileNotFoundError(
            f"Rainfall file not found: {RAINFALL_PATH}"
        )

    if not DFSI_PATH.exists():
        raise FileNotFoundError(
            f"DFSI file not found: {DFSI_PATH}"
        )

    rainfall = pd.read_csv(RAINFALL_PATH)

    dfsi = pd.read_csv(DFSI_PATH)

    # Rainfall columns used during model training
    rainfall_columns = [
        "Daily Actual",
        "Daily Normal",
        "Weekly \nActual",
        "Weekly Normal",
        "Cumulative Actual",
        "Cumulative Normal",
        "Monthly Acutual",
        "Monthly Normal"
    ]

    required_rainfall_columns = [
        "District",
        "State"
    ] + rainfall_columns

    missing_columns = [
        column for column in required_rainfall_columns
        if column not in rainfall.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing rainfall columns: {missing_columns}"
        )

    # Normalize rainfall district and state names
    rainfall["_district_key"] = (
        rainfall["District"].apply(normalize)
    )

    rainfall["_state_key"] = (
        rainfall["State"].apply(normalize)
    )

    # Convert rainfall columns to numerical values
    for column in rainfall_columns:

        rainfall[column] = pd.to_numeric(
            rainfall[column],
            errors="coerce"
        )

    # Aggregate rainfall values by district and state
    rainfall_features = (
        rainfall.groupby(
            ["_district_key", "_state_key"],
            as_index=False
        )[rainfall_columns]
        .mean()
    )

    # ----------------------------------
    # PREPARE DFSI DATA
    # ----------------------------------

    district_column = dfsi.columns[0]

    dfsi = dfsi.rename(
        columns={
            district_column: "District",
            "State_Name": "State",
            "DFSI": "dfsi_score"
        }
    )

    required_dfsi_columns = [
        "District",
        "State",
        "dfsi_score"
    ]

    missing_dfsi = [
        column for column in required_dfsi_columns
        if column not in dfsi.columns
    ]

    if missing_dfsi:
        raise ValueError(
            f"Missing DFSI columns: {missing_dfsi}"
        )

    dfsi["_district_key"] = (
        dfsi["District"].apply(normalize)
    )

    dfsi["_state_key"] = (
        dfsi["State"].apply(normalize)
    )

    dfsi["dfsi_score"] = pd.to_numeric(
        dfsi["dfsi_score"],
        errors="coerce"
    )

    dfsi_features = dfsi[
        [
            "_district_key",
            "_state_key",
            "dfsi_score"
        ]
    ].drop_duplicates(
        subset=["_district_key", "_state_key"]
    )

    # ----------------------------------
    # MERGE RAINFALL AND DFSI
    # ----------------------------------

    features_df = rainfall_features.merge(
        dfsi_features,
        on=["_district_key", "_state_key"],
        how="inner"
    )

    if features_df.empty:
        raise ValueError(
            "No matching districts found between rainfall and DFSI data."
        )

    model, model_features = load_model()

    missing_model_features = [
        feature for feature in model_features
        if feature not in features_df.columns
    ]

    if missing_model_features:
        raise ValueError(
            f"Missing model features: {missing_model_features}"
        )

    # Maintain exact training feature order
    X = features_df[model_features].copy()

    # Generate predictions
    predictions = model.predict(X)

    # Get predicted class probabilities
    if hasattr(model, "predict_proba"):

        all_probabilities = model.predict_proba(X)

        class_indices = {
            str(label): index
            for index, label in enumerate(model.classes_)
        }

        probabilities = [
            float(
                all_probabilities[row_index][
                    class_indices[str(prediction)]
                ]
            )
            for row_index, prediction in enumerate(predictions)
        ]

    else:

        probabilities = [None] * len(predictions)

    features_df["risk_level"] = [
        str(value).title()
        for value in predictions
    ]

    features_df["risk_probability"] = probabilities

    # Create district + state lookup
    prediction_lookup = {}

    for _, row in features_df.iterrows():

        key = (
            row["_district_key"],
            row["_state_key"]
        )

        probability = row["risk_probability"]

        prediction_lookup[key] = {
            "risk_level": row["risk_level"],
            "risk_probability": (
                float(probability)
                if pd.notna(probability)
                else None
            )
        }

    print(
        "District predictions generated:",
        len(prediction_lookup)
    )

    return prediction_lookup


# ----------------------------------
# LOAD DISTRICT GEOGRAPHICAL DATA
# ----------------------------------

@lru_cache(maxsize=1)
def load_districts():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"District dataset not found: {DATASET_PATH}"
        )

    gdf = gpd.read_parquet(DATASET_PATH)

    gdf = gdf.to_crs("EPSG:4326")

    gdf = gdf[
        [
            "dtname",
            "stname",
            "dist_lgd",
            "state_lgd",
            "geometry"
        ]
    ].copy()

    gdf = gdf.rename(
        columns={
            "dtname": "district",
            "stname": "state",
            "dist_lgd": "district_code",
            "state_lgd": "state_code"
        }
    )

    # Simplify geometries for faster map loading
    gdf["geometry"] = gdf["geometry"].simplify(
        GEOMETRY_TOLERANCE,
        preserve_topology=True
    )

    # Default risk values
    gdf["risk_level"] = "No data"
    gdf["risk_probability"] = None

    # Generate district predictions
    predictions = load_risk_predictions()

    # Match district predictions with geographical data
    for index, row in gdf.iterrows():

        key = (
            normalize(row["district"]),
            normalize(row["state"])
        )

        result = predictions.get(key)

        if result:

            gdf.at[index, "risk_level"] = (
                result["risk_level"]
            )

            gdf.at[index, "risk_probability"] = (
                result["risk_probability"]
            )

    print(
        "Districts loaded:",
        len(gdf)
    )

    print(
        "Districts with predictions:",
        (gdf["risk_level"] != "No data").sum()
    )

    return gdf


# ----------------------------------
# CACHE COMPLETE GEOJSON RESPONSE
# ----------------------------------

@lru_cache(maxsize=1)
def load_district_geojson():

    gdf = load_districts()

    geojson_data = gdf.to_json(drop_id=True)

    return JSONResponse(
        content=json.loads(geojson_data)
    )


# ----------------------------------
# INDIA DISTRICT RISK MAP API
# ----------------------------------

@router.get("/risk-map")
def risk_map():

    try:

        return load_district_geojson()

    except Exception as error:

        print("District map error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to load district risk map."
        )


# ----------------------------------
# LOAD HISTORICAL FLOODED AREA DATA
# ----------------------------------

@lru_cache(maxsize=1)
def load_area_data():

    path = FLOOD_DIR / "District_FloodedArea.csv"

    df = pd.read_csv(path)

    df["_normalized_name"] = (
        df["Dist_Name"].apply(normalize)
    )

    return df


# ----------------------------------
# LOAD HISTORICAL FLOOD IMPACT DATA
# ----------------------------------

@lru_cache(maxsize=1)
def load_impact_data():

    path = FLOOD_DIR / "District_FloodImpact.csv"

    df = pd.read_csv(path)

    df["_normalized_name"] = (
        df["Dist_Name"].apply(normalize)
    )

    return df


# ----------------------------------
# LOAD FLOOD INVENTORY DATA
# ----------------------------------

@lru_cache(maxsize=1)
def load_inventory_data():

    path = FLOOD_DIR / "India_Flood_Inventory_v3.csv"

    df = pd.read_csv(path)

    # Process LGD district codes
    df["_lgd_codes"] = (
        df["District_LGD_Codes"]
        .fillna("")
        .astype(str)
        .apply(
            lambda value: {
                normalize_code(code)
                for code in value.split(",")
                if normalize_code(code)
            }
        )
    )

    # Process district names
    df["_normalized_districts"] = (
        df["Districts"]
        .fillna("")
        .astype(str)
        .apply(normalize)
    )

    return df


# ----------------------------------
# DISTRICT HISTORICAL FLOOD API
# ----------------------------------

@router.get("/district/{district_code}/history")
def district_history(
    district_code: str,
    district_name: str = ""
):

    try:

        area_df = load_area_data()

        impact_df = load_impact_data()

        inventory_df = load_inventory_data()

        normalized_name = normalize(district_name)

        target_code = normalize_code(district_code)

        # Historical flooded area
        if normalized_name:

            area_match = area_df[
                area_df["_normalized_name"] == normalized_name
            ]

        else:

            area_match = area_df.iloc[0:0]

        # Historical flood impact
        if normalized_name:

            impact_match = impact_df[
                impact_df["_normalized_name"] == normalized_name
            ]

        else:

            impact_match = impact_df.iloc[0:0]

        # Match inventory using LGD codes
        code_match = inventory_df["_lgd_codes"].apply(
            lambda codes: target_code in codes
        )

        # District name fallback
        if normalized_name:

            name_match = inventory_df[
                "_normalized_districts"
            ].apply(
                lambda value: normalized_name in value
            )

        else:

            name_match = pd.Series(
                False,
                index=inventory_df.index
            )

        events = inventory_df[
            code_match | name_match
        ].copy()

        event_columns = [
            "UEI",
            "Start Date",
            "End Date",
            "Duration(Days)",
            "Main Cause",
            "Districts",
            "State",
            "Severity",
            "Area Affected",
            "Human fatality",
            "Human injured",
            "Human Displaced"
        ]

        available_columns = [
            column for column in event_columns
            if column in events.columns
        ]

        events = events[available_columns]

        return {
            "district": district_name,
            "district_code": district_code,

            "flooded_area": clean_records(
                area_match.drop(
                    columns=["_normalized_name"],
                    errors="ignore"
                )
            ),

            "flood_impact": clean_records(
                impact_match.drop(
                    columns=["_normalized_name"],
                    errors="ignore"
                )
            ),

            "historical_events": clean_records(events),

            "total_historical_events": len(events)
        }

    except Exception as error:

        print(
            "District history error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load district historical data."
        )


# ----------------------------------
# HISTORICAL DATA API
# ----------------------------------

@router.get("/history")
def history():

    return {
        "rainfall": [],
        "floods": []
    }


# ----------------------------------
# SAFETY GUIDELINES API
# ----------------------------------

@router.get("/safety")
def safety():

    return {
        "before": [
            "Know your area's flood risk",
            "Prepare an emergency kit"
        ],

        "during": [
            "Move to higher ground",
            "Avoid walking or driving through flood water"
        ],

        "after": [
            "Return home only when authorities say it is safe"
        ]
    }

# ----------------------------------
# MODEL PREDICTION COVERAGE
# ----------------------------------

@router.get("/risk-coverage")
def risk_coverage():

    try:
        gdf = load_districts()

        matched = gdf[gdf["risk_level"] != "No data"]
        unmatched = gdf[gdf["risk_level"] == "No data"]

        return {
            "total_districts": len(gdf),
            "predicted_districts": len(matched),
            "unmatched_districts": len(unmatched),
            "coverage_percentage": round(
                len(matched) / len(gdf) * 100, 2
            ),
            "unmatched": [
                {
                    "district": row["district"],
                    "state": row["state"]
                }
                for _, row in unmatched.iterrows()
            ]
        }

    except Exception as error:
        print("Risk coverage error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to calculate prediction coverage."
        )

@router.get("/risk-debug")
def risk_debug():

    rainfall = pd.read_csv(RAINFALL_PATH)
    dfsi = pd.read_csv(DFSI_PATH)

    rainfall_keys = set(
        zip(
            rainfall["District"].apply(normalize),
            rainfall["State"].apply(normalize)
        )
    )

    district_column = dfsi.columns[0]

    dfsi = dfsi.rename(columns={
        district_column: "District"
    })

    dfsi_keys = set(
        zip(
            dfsi["District"].apply(normalize),
            dfsi["State_Name"].apply(normalize)
        )
    )

    common = rainfall_keys & dfsi_keys

    return {
        "rainfall_unique_districts": len(rainfall_keys),
        "dfsi_unique_districts": len(dfsi_keys),
        "matching_districts": len(common),
        "rainfall_only_count": len(rainfall_keys - dfsi_keys),
        "dfsi_only_count": len(dfsi_keys - rainfall_keys),
        "rainfall_only_examples": list(rainfall_keys - dfsi_keys)[:30],
        "dfsi_only_examples": list(dfsi_keys - rainfall_keys)[:30]
    }

@router.get("/risk-debug-details")
def risk_debug_details():

    gdf = load_districts()

    rainfall = pd.read_csv(RAINFALL_PATH)
    dfsi = pd.read_csv(DFSI_PATH)

    rainfall_keys = set(zip(
        rainfall["District"].apply(normalize),
        rainfall["State"].apply(normalize)
    ))

    district_column = dfsi.columns[0]

    dfsi = dfsi.rename(columns={
        district_column: "District"
    })

    dfsi_keys = set(zip(
        dfsi["District"].apply(normalize),
        dfsi["State_Name"].apply(normalize)
    ))

    data_keys = rainfall_keys & dfsi_keys

    results = {
        "matched": [],
        "missing_rainfall": [],
        "missing_dfsi": [],
        "matched_but_not_predicted": []
    }

    for _, row in gdf.iterrows():

        key = (
            normalize(row["district"]),
            normalize(row["state"])
        )

        if key in data_keys:
            if row["risk_level"] == "No data":
                results["matched_but_not_predicted"].append({
                    "district": row["district"],
                    "state": row["state"]
                })
            else:
                results["matched"].append(row["district"])

        elif key not in rainfall_keys:
            results["missing_rainfall"].append({
                "district": row["district"],
                "state": row["state"]
            })

        elif key not in dfsi_keys:
            results["missing_dfsi"].append({
                "district": row["district"],
                "state": row["state"]
            })

    return {
        "total": len(gdf),
        "predicted": len(results["matched"]),
        "missing_rainfall_count": len(results["missing_rainfall"]),
        "missing_dfsi_count": len(results["missing_dfsi"]),
        "matched_but_not_predicted_count": len(
            results["matched_but_not_predicted"]
        ),
        "missing_rainfall": results["missing_rainfall"][:50],
        "missing_dfsi": results["missing_dfsi"][:50],
        "matched_but_not_predicted":
            results["matched_but_not_predicted"][:50]
    }