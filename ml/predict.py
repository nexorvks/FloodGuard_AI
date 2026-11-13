"""Load the trained model and return a flood-risk class."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "flood_model.joblib"

RISK_LABELS = {0: "low", 1: "moderate", 2: "high"}


def predict_risk(features: dict) -> dict:
    # TODO: model = joblib.load(MODEL_PATH); build feature row; return label + probability
    raise NotImplementedError("Add prediction code here")
