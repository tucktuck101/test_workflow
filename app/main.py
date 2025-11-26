from fastapi import FastAPI

from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Battleship RL API", version=settings.model_version)
    app.state.settings = settings
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
