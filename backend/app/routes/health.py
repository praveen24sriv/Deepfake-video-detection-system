from fastapi import APIRouter

from app.schemas.analysis import HealthResponse


router = APIRouter(
    tags=["Health"]
)


@router.get(
    "/health",
    response_model=HealthResponse,
)
def health():

    return HealthResponse(
        status="ok",
        service="deepguard-backend",
    )