# FloodGuard AI

A web application for detecting and visualising flood risk across India using
historical flood, rainfall and river water-level data, machine learning, and
Explainable AI (SHAP).

## Objectives
- Collect and integrate historical flood, rainfall and river water-level datasets
- Clean, preprocess, explore (EDA) and engineer features
- Build and evaluate ML models for flood-risk classification (Low / Moderate / High)
- Use SHAP to explain which factors drive predictions
- Provide an interactive map of flood risk across India
- Analyse historical rainfall patterns and flood occurrences
- Provide safety guidelines and preparedness information

## Tech Stack
- **Backend:** FastAPI (Python)
- **ML / Data:** pandas, scikit-learn, XGBoost, SHAP, GeoPandas
- **Frontend:** HTML, CSS, JavaScript (Leaflet, Chart.js)

## Project Structure
```
floodguard-ai/
├── data/        # raw/ (original downloads) and processed/ (model-ready data)
├── notebooks/   # cleaning, EDA, feature engineering, modelling, SHAP
├── ml/          # train.py, predict.py, saved models
├── backend/     # FastAPI app (main.py, routes.py, schemas.py)
└── frontend/    # templates/ and static/ (css, js, geojson)
```

## Getting Started
```bash
git clone <repo-url>
cd floodguard-ai
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000 for the site and http://127.0.0.1:8000/docs for the API docs.

## Team Workflow
- `main` holds stable code; work on feature branches (e.g. `feature/risk-map`)
- Open a pull request and get one teammate to review before merging
- Never commit large datasets or secrets (see `.gitignore`); share data via Drive

## Data Sources
List every dataset here with its source and licence (IMD, CWC/India-WRIS, NDMA, DFO, etc.).

| Dataset | Source | Link | Licence |
|---|---|---|---|
| | | | |
