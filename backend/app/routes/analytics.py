from fastapi import APIRouter

from app.schemas.analysis import AnalyticsResponse
from app.services.analysis_service import analysis_service


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "",
    response_model=AnalyticsResponse,
)
def get_analytics():

    return analysis_service.analytics()