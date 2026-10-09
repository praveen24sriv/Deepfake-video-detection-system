from pydantic import BaseModel, Field


class VideoStats(BaseModel):
    filename: str
    duration_seconds: float
    fps: float
    frame_count: int
    width: int
    height: int
    sampled_frames: int


class PreprocessingStats(BaseModel):
    frames_read: int
    frames_sampled: int
    faces_detected: int
    frames_without_face: int
    blurred_frames: int
    usable_frames: int


class SuspiciousTimeline(BaseModel):
    suspicious_start: float | None = None
    suspicious_end: float | None = None
    duration: float


class DetectionResult(BaseModel):
    verdict: str = Field(
        description="REAL, FAKE, or MODEL_UNAVAILABLE"
    )

    fake: bool | None = None

    confidence: float
    confidence_percent: float

    artifacts: list[str] = []

    timeline: SuspiciousTimeline


class ModelInfo(BaseModel):
    name: str
    version: str
    demo_mode: bool


class AnalysisMeta(BaseModel):
    processing_time_seconds: float
    heatmap_url: str | None = None
    note: str | None = None


class AnalysisResponse(BaseModel):
    success: bool = True

    video: VideoStats

    preprocessing: PreprocessingStats

    detection: DetectionResult

    model: ModelInfo

    meta: AnalysisMeta


class AnalyticsResponse(BaseModel):
    total_videos_analyzed: int
    fake_videos: int
    real_videos: int
    average_processing_time_seconds: float
    fake_rate_percent: float


class HealthResponse(BaseModel):
    status: str
    service: str