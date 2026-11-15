from pydantic import BaseModel


class PredictionRequest(BaseModel):
    daily_actual: float
    daily_normal: float
    weekly_actual: float
    weekly_normal: float
    cumulative_actual: float
    cumulative_normal: float
    monthly_actual: float
    monthly_normal: float
    dfsi_score: float


class PredictionResponse(BaseModel):
    risk_level: str
    probability: float | None = None