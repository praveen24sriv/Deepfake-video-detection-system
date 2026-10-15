
import time
import uuid
import statistics

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
from app.services.detector import detector
from app.services.face_service import face_service
from app.services.heatmap_service import heatmap_service
from app.services.quality_service import quality_service
from app.services.video_service import video_service


class AnalysisService:
    def __init__(self):
        self.total_videos = 0
        self.fake_videos = 0
        self.real_videos = 0
        self.processing_times = []

    def initialize(self):
        detector.initialize()

    def analyze(self, video_path, original_filename: str) -> AnalysisResponse:
        start_time = time.perf_counter()

        # 1. Extract video metadata and sample frames.
        inspection = video_service.inspect(video_path)

        frames_read = len(inspection.samples)
        frames_sampled = len(inspection.samples)

        faces_detected = 0
        frames_without_face = 0
        blurred_frames = 0
        usable_frames = 0

        crops = []
        timestamps = []
        blur_scores = []

        first_heatmap_frame = None

        # 2. Detect faces, crop them, and measure image quality.
        # Blurry frames are measured but are NOT discarded.
        for sample in inspection.samples:
            boxes = face_service.detect(sample.frame)

            if not boxes:
                frames_without_face += 1
                continue

            faces_detected += 1

            crop = face_service.crop_largest(sample.frame, boxes)

            if crop is None:
                frames_without_face += 1
                continue

            blur_score = quality_service.laplacian_variance(crop)
            blur_scores.append(blur_score)

            if blur_score < settings.blur_threshold:
                blurred_frames += 1

            # Keep blurry crops too; blur is only recorded as a statistic.
            usable_frames += 1
            crops.append(crop)
            timestamps.append(sample.timestamp)

            if first_heatmap_frame is None:
                first_heatmap_frame = crop

        # 3. Select at most settings.sample_frames crops for model inference.
        # Selection is distributed across the available valid face crops.
        if len(crops) > settings.sample_frames:
            # Rounded like training (16 of 32 -> frames 0, 2, ... 14, 17, 19, ... 31).
            selected_indices = np.linspace(
                0,
                len(crops) - 1,
                num=settings.sample_frames,
            ).round().astype(int).tolist()

            model_crops = [crops[i] for i in selected_indices]
            model_timestamps = [timestamps[i] for i in selected_indices]
        else:
            model_crops = crops
            model_timestamps = timestamps

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
        elif first_heatmap_frame is not None:
            heatmap_service.create_debug_heatmap(
                first_heatmap_frame,
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
