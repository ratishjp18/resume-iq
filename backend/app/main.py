import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.errors import register_error_handlers
from app.api.routes import router
from app.config import BACKEND_DIR, get_settings

logger = logging.getLogger("resumeiq")


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    if settings.auto_migrate:
        run_migrations()
    if settings.preload_model:
        from app.services.embedding import get_embedder

        get_embedder()  # load the model once at startup
        logger.info("Embedding model ready")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ResumeIQ API",
        version=__version__,
        description="Local resume analysis and job-description matching. Scores are explainable heuristics, "
        "not an ATS score or hiring probability.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # explicit local dev origins only; never "*"
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
