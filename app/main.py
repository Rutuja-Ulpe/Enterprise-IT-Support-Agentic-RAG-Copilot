from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.core.config import get_settings, BASE_DIR
from app.core.logging import configure_logging
from app.services.audit import init_db


# Configure logging
configure_logging()

# Load settings
settings = get_settings()

# Initialize audit database
init_db()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

# Register API routes
app.include_router(router)

# Static files
static_dir = BASE_DIR / "static"

if static_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static",
    )

# Templates
templates_dir = BASE_DIR / "templates"

templates = Jinja2Templates(
    directory=str(templates_dir)
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
        },
    )


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
    }