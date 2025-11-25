"""
Bootstrap Web UI Server - Port 8001
Modern Bootstrap 4 interface for ArchiveSMP Configuration Manager
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.api import (
    dashboard_endpoints,
    plugin_configurator_endpoints,
    tag_manager_endpoints,
    update_manager_endpoints,
    variance_endpoints,
    audit_log_endpoints,
    deployment_endpoints,
)

# Create FastAPI app
app = FastAPI(
    title="ArchiveSMP Config Manager (Bootstrap UI)",
    description="Modern Bootstrap 4 interface for configuration management",
    version="2.0.0",
)

# Setup templates and static files
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# Include API routers (routers already have their prefixes defined)
app.include_router(dashboard_endpoints.router)
app.include_router(plugin_configurator_endpoints.router)
app.include_router(tag_manager_endpoints.router)
app.include_router(update_manager_endpoints.router)
app.include_router(variance_endpoints.router)
app.include_router(audit_log_endpoints.router)
app.include_router(deployment_endpoints.router)


# Page routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/plugins", response_class=HTMLResponse)
async def plugins(request: Request):
    """Plugin configurator page"""
    return templates.TemplateResponse("plugins.html", {"request": request})


@app.get("/tags", response_class=HTMLResponse)
async def tags(request: Request):
    """Tag manager page"""
    return templates.TemplateResponse("tags.html", {"request": request})


@app.get("/updates", response_class=HTMLResponse)
async def updates(request: Request):
    """Update manager page"""
    return templates.TemplateResponse("updates.html", {"request": request})


@app.get("/variance", response_class=HTMLResponse)
async def variance(request: Request):
    """Variance report page"""
    return templates.TemplateResponse("variance.html", {"request": request})


@app.get("/instance/{instance_name}", response_class=HTMLResponse)
async def instance_detail(request: Request, instance_name: str):
    """Instance detail page"""
    return templates.TemplateResponse("instance_detail.html", {"request": request, "instance_name": instance_name})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "ui_version": "2.0.0-bootstrap"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
