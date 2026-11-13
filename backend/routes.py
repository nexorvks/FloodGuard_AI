from fastapi import APIRouter

from backend.schemas import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/api")


@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    # TODO: replace with ml.predict.predict_risk(...)
    return PredictionResponse(risk_level="low", probability=None)


@router.get("/risk-map")
def risk_map():
    # TODO: return GeoJSON with risk level per state/district
    return {"type": "FeatureCollection", "features": []}


@router.get("/history")
def history():
    # TODO: return historical rainfall / flood trends
    return {"rainfall": [], "floods": []}


@router.get("/safety")
def safety():
    return {
        "before": ["Know your area's flood risk", "Prepare an emergency kit"],
        "during": ["Move to higher ground", "Avoid walking or driving through flood water"],
        "after": ["Return home only when authorities say it is safe"],
    }
