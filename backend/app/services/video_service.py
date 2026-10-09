from dataclasses import dataclass

import cv2
import numpy as np

from app.config import settings


@dataclass
class FrameSample:
    index: int
    timestamp: float
    frame: np.ndarray


@dataclass
class VideoInspection:
    fps: float
    frame_count: int
    width: int
    height: int
    duration: float
    samples: list[FrameSample]


class VideoService:

    def inspect(
        self,
        video_path,
    ) -> VideoInspection:

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():

            raise ValueError(
                "Unable to open uploaded video."
            )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
            or 0
        )

        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
            or 0
        )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
            or 0
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
            or 0
        )

        if fps <= 0 or frame_count <= 0:

            capture.release()

            raise ValueError(
                "Invalid or unreadable video."
            )

        duration = frame_count / fps

        samples = self._sample_frames(
            capture,
            frame_count,
            fps,
        )

        capture.release()

        if not samples:

            raise ValueError(
                "No readable frames found."
            )

        return VideoInspection(
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration=duration,
            samples=samples,
        )

    def _sample_frames(
        self,
        capture,
        frame_count: int,
        fps: float,
    ):

        sample_count = min(
            settings.sample_frames,
            frame_count,
        )

        indexes = np.linspace(
            0,
            frame_count - 1,
            num=sample_count,
            dtype=int,
        )

        samples = []

        seen = set()

        for index in indexes.tolist():

            if index in seen:
                continue

            seen.add(index)

            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                index,
            )

            success, frame = capture.read()

            if not success:
                continue

            if frame is None:
                continue

            samples.append(
                FrameSample(
                    index=index,
                    timestamp=index / fps,
                    frame=frame,
                )
            )

        return samples


video_service = VideoService()