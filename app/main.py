from fastapi import FastAPI

from .config import Settings
from .model_loader import ModelLoader
from .obs import Observability


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Battleship RL API", version=settings.model_version)
    app.state.settings = settings
    loader = ModelLoader(
        model_path=settings.model_path,
        expected_hash=settings.model_hash,
        device=settings.model_device,
        model_version=settings.model_version,
    )
    app.state.model_loader = loader
    app.state.obs = Observability(settings)

    from .routes import get_health_router, get_router

    app.include_router(get_router(app, settings, loader, app.state.obs))
    app.include_router(get_health_router(settings, loader))
    return app


try:
    app = create_app()
except ValueError:
    # Allow import for tests/tools without configured environment.
    app = FastAPI(title="Battleship RL API (unconfigured)")


def run() -> None:
    """Run the API using uvicorn."""
    settings = Settings.from_env()
    import uvicorn

    uvicorn.run(
        "app.main:create_app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level,
        reload=False,
        factory=True,
    )


if __name__ == "__main__":
    run()
