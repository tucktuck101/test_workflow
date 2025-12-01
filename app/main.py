import hashlib
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .model_loader import ModelLoader
from .obs import Observability


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Battleship RL API", version=settings.model_version)
    origins = [o for o in [settings.frontend_origin, settings.training_frontend_origin] if o]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.state.settings = settings
    loader = ModelLoader(
        model_path=settings.model_path,
        expected_hash=settings.model_hash,
        device=settings.model_device,
        model_version=settings.model_version,
        model_root=settings.model_root,
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
    """Run the API using uvicorn."""  # pragma: no cover
    settings = Settings.from_env()  # pragma: no cover
    import uvicorn  # pragma: no cover

    uvicorn.run(  # pragma: no cover
        "app.main:create_app",  # pragma: no cover
        host=settings.api_host,  # pragma: no cover
        port=settings.api_port,  # pragma: no cover
        log_level=settings.log_level,  # pragma: no cover
        reload=False,  # pragma: no cover
        factory=True,  # pragma: no cover
    )  # pragma: no cover


def run_stub() -> None:
    """Run the API in deterministic stub mode with a generated model artifact."""  # pragma: no cover
    stub_dir = Path(os.environ.get("STUB_MODEL_DIR", ".stub_model")).resolve()  # pragma: no cover
    stub_dir.mkdir(parents=True, exist_ok=True)  # pragma: no cover
    stub_path = stub_dir / "model.bin"  # pragma: no cover
    content = b"stub-model"  # pragma: no cover
    stub_path.write_bytes(content)  # pragma: no cover
    stub_hash = hashlib.sha256(content).hexdigest()  # pragma: no cover

    os.environ.setdefault("MODEL_PATH", str(stub_path))  # pragma: no cover
    os.environ.setdefault("MODEL_VERSION", "stub")  # pragma: no cover
    os.environ.setdefault("MODEL_HASH", stub_hash)  # pragma: no cover
    os.environ.setdefault("MODEL_DEVICE", "cpu")  # pragma: no cover
    os.environ.setdefault("BOARD_SIZE", "5")  # pragma: no cover
    os.environ.setdefault("DETERMINISTIC_MODE", "true")  # pragma: no cover
    os.environ.setdefault("MAX_ACTIVE_GAMES", "5")  # pragma: no cover
    os.environ.setdefault("API_PORT", "8000")  # pragma: no cover
    os.environ.setdefault("API_HOST", "0.0.0.0")  # pragma: no cover
    os.environ.setdefault("MODEL_ROOT", str(stub_dir))  # pragma: no cover
    os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")  # pragma: no cover
    run()  # pragma: no cover


if __name__ == "__main__":
    import sys  # pragma: no cover

    if len(sys.argv) > 1 and sys.argv[1] == "stub":  # pragma: no cover
        run_stub()  # pragma: no cover
    else:  # pragma: no cover
        run()  # pragma: no cover
