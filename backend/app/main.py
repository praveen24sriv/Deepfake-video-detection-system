from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.staticfiles import StaticFiles

from app.config import settings

from app.routes.analysis import (
    router as analysis_router,
)

from app.routes.analytics import (
    router as analytics_router,
)

from app.routes.health import (
    router as health_router,
)

from app.services.analysis_service import (
    analysis_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    settings.upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    analysis_service.initialize()

    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "FastAPI backend for the "
        "DeepFake Video Detection System."
    ),
    version=settings.api_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=settings.cors_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.mount(
    "/outputs",
    StaticFiles(
        directory=settings.output_dir
    ),
    name="outputs",
)


app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    analysis_router,
    prefix="/api/v1",
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
)