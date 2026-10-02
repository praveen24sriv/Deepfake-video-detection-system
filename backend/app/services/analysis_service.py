import time
import uuid
import statistics

import cv2

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

    def analyze(
        self,
        video_path,
        original_filename: str,
    ) -> AnalysisResponse:

        start_time = time.perf_counter()

        inspection = video_service.inspect(
            video_path
        )

        frames_read = len(
            inspection.samples
        )

        frames_sampled = len(
            inspection.samples
        )

        faces_detected = 0
        frames_without_face = 0
        blurred_frames = 0
        usable_frames = 0

        crops = []
        timestamps = []

        first_heatmap_frame = None

        for sample in inspection.samples:

            boxes = face_service.detect(
                sample.frame
            )

            if not boxes:

                frames_without_face += 1
                continue

            faces_detected += 1

            crop = face_service.crop_largest(
                sample.frame,
                boxes,
            )

            if crop is None:

                frames_without_face += 1
                continue

            if quality_service.is_blurry(
                crop
            ):

                blurred_frames += 1
                continue

            usable_frames += 1

            resized = cv2.resize(
                crop,
                settings.frame_size,
            )

            crops.append(resized)

            timestamps.append(
                sample.timestamp
            )

            if first_heatmap_frame is None:

                first_heatmap_frame = crop

        prediction = detector.predict(
            crops,
            timestamps,
        )

        heatmap_url = None
        note = None

        if first_heatmap_frame is not None:

            output_name = (
                f"{uuid.uuid4().hex}.jpg"
            )

            output_path = (
                settings.output_dir
                / output_name
            )

            heatmap_service.create_debug_heatmap(
                first_heatmap_frame,
                output_path,
            )

            heatmap_url = (
                f"/outputs/{output_name}"
            )

            note = (
                "Development heatmap only. "
                "Replace with true Grad-CAM "
                "after model integration."
            )

        processing_time = (
            time.perf_counter()
            - start_time
        )

        fake = None

        if prediction.verdict == "FAKE":

            fake = True
            self.fake_videos += 1

        elif prediction.verdict == "REAL":

            fake = False
            self.real_videos += 1

        self.total_videos += 1

        self.processing_times.append(
            processing_time
        )

        confidence = max(
            prediction.fake_probability,
            prediction.real_probability,
        )

        return AnalysisResponse(

            video=VideoStats(

                filename=original_filename,

                duration_seconds=round(
                    inspection.duration,
                    3,
                ),

                fps=round(
                    inspection.fps,
                    3,
                ),

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
            ),

            detection=DetectionResult(

                verdict=prediction.verdict,

                fake=fake,

                confidence=round(
                    confidence,
                    4,
                ),

                confidence_percent=round(
                    confidence * 100,
                    2,
                ),

                artifacts=prediction.artifacts,

                timeline=SuspiciousTimeline(

                    suspicious_start=(
                        prediction.suspicious_start
                    ),

                    suspicious_end=(
                        prediction.suspicious_end
                    ),

                    duration=round(
                        inspection.duration,
                        3,
                    ),
                ),
            ),

            model=ModelInfo(

                name=settings.model_name,

                version=settings.model_version,

                demo_mode=settings.demo_mode,
            ),

            meta=AnalysisMeta(

                processing_time_seconds=round(
                    processing_time,
                    3,
                ),

                heatmap_url=heatmap_url,

                note=note,
            ),
        )

    def analytics(
        self,
    ) -> AnalyticsResponse:

        if self.processing_times:

            average = statistics.mean(
                self.processing_times
            )

        else:

            average = 0.0

        if self.total_videos:

            fake_rate = (
                self.fake_videos
                / self.total_videos
                * 100
            )

        else:

            fake_rate = 0.0

        return AnalyticsResponse(

            total_videos_analyzed=(
                self.total_videos
            ),

            fake_videos=self.fake_videos,

            real_videos=self.real_videos,

            average_processing_time_seconds=round(
                average,
                3,
            ),

            fake_rate_percent=round(
                fake_rate,
                2,
            ),
        )


analysis_service = AnalysisService()