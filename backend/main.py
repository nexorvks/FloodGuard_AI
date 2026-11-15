
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.routes import router
from backend.forecasting.forecast_routes import router as forecast_router
from backend.rainfall.rainfall_routes import router as rainfall_router


# ----------------------------------
# PROJECT PATHS
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"


# ----------------------------------
# FASTAPI APPLICATION
# ----------------------------------

app = FastAPI(title="FloodGuard AI")

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


# ----------------------------------
# COMMON PAGE RENDERER
# ----------------------------------

def render_page(request: Request, template_name: str):
    return templates.TemplateResponse(
        request,
        template_name
    )


# ----------------------------------
# FRONTEND PAGE ROUTES
# ----------------------------------

@app.get("/")
def home_page(request: Request):
    return render_page(request, "index.html")


@app.get("/map")
def map_page(request: Request):
    return render_page(request, "map.html")


@app.get("/rainfall")
def rainfall_page(request: Request):
    return render_page(request, "rainfall.html")


@app.get("/safety-guidelines")
def safety_page(request: Request):
    return render_page(request, "safety.html")


@app.get("/search")
def search_page(request: Request):
    return render_page(request, "search.html")


@app.get("/analysis")
def analysis_page(request: Request):
    return render_page(request, "analysis.html")


# ----------------------------------
# API ROUTERS
# ----------------------------------

app.include_router(router)
app.include_router(forecast_router)
app.include_router(rainfall_router)
