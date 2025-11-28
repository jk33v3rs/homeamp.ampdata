"""HomeAMP V2.0 - FastAPI application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from homeamp_v2.api.routes import (
    approvals,
    audit,
    config,
    dashboard,
    datapacks,
    deployments,
    groups,
    instances,
    plugins,
    tags,
    updates,
)
from homeamp_v2.core.config import get_settings
from homeamp_v2.core.logging import setup_logging
from homeamp_v2.web import web_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting HomeAMP V2.0 API")
    yield
    # Shutdown
    logger.info("Shutting down HomeAMP V2.0 API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    # Setup logging
    setup_logging()

    # Create app
    app = FastAPI(
        title="HomeAMP Configuration Manager",
        description="API for managing AMP Minecraft server instances",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = Path(__file__).parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Include web UI router (must be before API routers to handle root route)
    app.include_router(web_router, tags=["web"])

    # Include routers - Core
    app.include_router(instances.router)
    app.include_router(plugins.router)
    app.include_router(deployments.router)
    app.include_router(tags.router)
    app.include_router(config.router)

    # Include routers - V2 Features
    app.include_router(dashboard.router)
    app.include_router(updates.router)
    app.include_router(approvals.router)
    app.include_router(audit.router)
    app.include_router(groups.router)
    app.include_router(datapacks.router)

    @app.get("/health")
    def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/api")
    def api_info():
        """API info endpoint."""
        return {
            "name": "HomeAMP Configuration Manager",
            "version": "2.0.0",
            "status": "operational",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "homeamp_v2.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
