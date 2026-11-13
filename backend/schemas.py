from pydantic import BaseModel


class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    rainfall_mm: float | None = None
    river_level_m: float | None = None


class PredictionResponse(BaseModel):
    risk_level: str          # "low" | "moderate" | "high"
    probability: float | None = None
