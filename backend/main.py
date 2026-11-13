from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="FloodGuard AI")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")

app.include_router(router)


def page(name: str):
    def view(request: Request):
        return templates.TemplateResponse(request, name)
    return view


app.get("/")(page("index.html"))
app.get("/map")(page("map.html"))
app.get("/analysis")(page("analysis.html"))
app.get("/safety-guidelines")(page("safety.html"))
