
import time
import uuid
import statistics

import cv2
import numpy as np

from app.config import settings
from app.schemas.analysis import (
    AnalysisMeta,
    AnalysisResponse,
    AnalyticsResponse,
    DetectionResult,
    ModelInfo,
    PreprocessingStats,
    SuspiciousTimeline,
    VideoStats,
)
from app.services.deepguard import FaceCropper, blur_score
from app.services.detector import detector
from app.services.heatmap_service import heatmap_service
from app.services.video_service import video_service


def select_evenly(items, n):
    """Pick n items spread evenly over the list, keeping order (rounded linspace).
    Same rule as training and DeepGuardPredictor.predict_video: 16 of 32 crops."""
    if len(items) <= n:
        return list(items)
    keep = np.linspace(0, len(items) - 1, n).round().astype(int)
    return [items[i] for i in keep]


class AnalysisService:
    def __init__(self):
        self.total_videos = 0
        self.fake_videos = 0
        self.real_videos = 0
        self.processing_times = []
        self.face_cropper = None

    def initialize(self):
        detector.initialize()
        # Face cropping uses the SAME FaceCropper as the training preprocessing
        # (deepguard.py): MTCNN, largest face, square 1.3x crop clamped to the frame,
        # last box reused when a frame has no detection, leading frames back-filled.
        if detector.available:
            self.face_cropper = detector.predictor.cropper
        else:
            self.face_cropper = FaceCropper(device=settings.model_device or None)

    def analyze(self, video_path, original_filename: str) -> AnalysisResponse:
        start_time = time.perf_counter()

        # 1. Extract video metadata and sample frames.
        inspection = video_service.inspect(video_path)

        frames_read = len(inspection.samples)
        frames_sampled = len(inspection.samples)

        # 2. Face crops, exactly as in training (deepguard.FaceCropper).
        # Every sampled frame keeps its place in time: a frame without a detected
        # face reuses the last face box, frames before the first detection are
        # back-filled. No face in the whole video -> no crops -> NO_FACE verdict.
        frames_rgb = [
            cv2.cvtColor(sample.frame, cv2.COLOR_BGR2RGB)
            for sample in inspection.samples
        ]
        timestamps = [sample.timestamp for sample in inspection.samples]

        crops, detected = self.face_cropper.crop(frames_rgb)   # RGB, 224x224

        faces_detected = int(sum(detected))
        frames_without_face = len(detected) - faces_detected
        usable_frames = len(crops)

        # Blur is measured as a statistic only; blurry crops are NOT discarded.
        blur_scores = [blur_score(crop) for crop in crops]
        blurred_frames = sum(
            score < settings.blur_threshold for score in blur_scores
        )

        # 3. 16 of the 32 crops for the model (same rule as training).
        if crops:
            model_crops = select_evenly(crops, settings.sample_frames)
            model_timestamps = select_evenly(timestamps, settings.sample_frames)
        else:
            model_crops = []
            model_timestamps = []

        # 4. Run the detector. With the model loaded it also writes a Grad-CAM
        # heatmap of the most suspicious frame to output_path.
        output_name = f"{uuid.uuid4().hex}.jpg"
        output_path = settings.output_dir / output_name

        prediction = detector.predict(
            model_crops,
            model_timestamps,
            heatmap_path=output_path if detector.available and model_crops else None,
        )

        # 5. Heatmap: real Grad-CAM from the model, or a debug overlay in demo mode.
        heatmap_url = None
        note = None

        if prediction.heatmap_written:
            heatmap_url = f"/outputs/{output_name}"
            note = (
                "Grad-CAM: red areas influenced the fake score most, "
                "shown on the most suspicious frame."
            )
        elif crops:
            heatmap_service.create_debug_heatmap(
                cv2.cvtColor(crops[0], cv2.COLOR_RGB2BGR),
                output_path,
            )
            heatmap_url = f"/outputs/{output_name}"
            note = (
                "Development heatmap only (demo mode). "
                "Grad-CAM is produced when the model is loaded."
            )

        # 6. Record processing time and analytics.
        processing_time = time.perf_counter() - start_time

        fake = None

        if prediction.verdict == "FAKE":
            fake = True
            self.fake_videos += 1
        elif prediction.verdict == "REAL":
            fake = False
            self.real_videos += 1

        self.total_videos += 1
        self.processing_times.append(processing_time)

        confidence = max(
            prediction.fake_probability,
            prediction.real_probability,
        )

        # 7. Build the API response.
        return AnalysisResponse(
            video=VideoStats(
                filename=original_filename,
                duration_seconds=round(inspection.duration, 3),
                fps=round(inspection.fps, 3),
                frame_count=inspection.frame_count,
                width=inspection.width,
                height=inspection.height,
                sampled_frames=frames_sampled,
            ),
            preprocessing=PreprocessingStats(
                frames_read=frames_read,
                frames_sampled=frames_sampled,
                faces_detected=faces_detected,
                frames_without_face=frames_without_face,
                blurred_frames=blurred_frames,
                usable_frames=usable_frames,
                model_frames_used=len(model_crops),
                average_blur_score=(
                    round(statistics.mean(blur_scores), 2)
                    if blur_scores
                    else 0.0
                ),
            ),
            detection=DetectionResult(
                verdict=prediction.verdict,
                fake=fake,
                confidence=round(confidence, 4),
                confidence_percent=round(confidence * 100, 2),
                artifacts=prediction.artifacts,
                timeline=SuspiciousTimeline(
                    suspicious_start=prediction.suspicious_start,
                    suspicious_end=prediction.suspicious_end,
                    duration=round(inspection.duration, 3),
                ),
            ),
            model=ModelInfo(
                name=settings.model_name,
                version=settings.model_version,
                demo_mode=settings.demo_mode,
            ),
            meta=AnalysisMeta(
                processing_time_seconds=round(processing_time, 3),
                heatmap_url=heatmap_url,
                note=note,
            ),
        )

    def analytics(self) -> AnalyticsResponse:
        average = (
            statistics.mean(self.processing_times)
            if self.processing_times
            else 0.0
        )

        fake_rate = (
            self.fake_videos / self.total_videos * 100
            if self.total_videos
            else 0.0
        )

        return AnalyticsResponse(
            total_videos_analyzed=self.total_videos,
            fake_videos=self.fake_videos,
            real_videos=self.real_videos,
            average_processing_time_seconds=round(average, 3),
            fake_rate_percent=round(fake_rate, 2),
        )


analysis_service = AnalysisService()
