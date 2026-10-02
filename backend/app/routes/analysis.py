from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.schemas.analysis import AnalysisResponse

from app.services.analysis_service import (
    analysis_service,
)

from app.services.storage_service import (
    storage_service,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_video(
    file: UploadFile = File(...),
):

    try:

        video_path = (
            await storage_service.save_upload(
                file
            )
        )

        try:

            result = analysis_service.analyze(
                video_path,
                file.filename or "video",
            )

            return result

        finally:

            storage_service.delete_file(
                video_path
            )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc