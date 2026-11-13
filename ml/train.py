"""Train the flood-risk classifier and save it to ml/models/."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "flood_dataset.csv"
MODEL_PATH = BASE_DIR / "ml" / "models" / "flood_model.joblib"


def main():
    # TODO: load DATA_PATH, split, train (e.g. XGBoost), evaluate, joblib.dump(model, MODEL_PATH)
    raise NotImplementedError("Add training code here")


if __name__ == "__main__":
    main()
