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
            settings.extracted_frames,
            frame_count,
        )

        # Rounded (not truncated) indexes: same frames as the training preprocessing.
        wanted = set(
            np.linspace(
                0,
                frame_count - 1,
                num=sample_count,
            ).round().astype(int).tolist()
        )
        last = max(wanted)

        # Read frames in order (grab/retrieve) instead of seeking with
        # CAP_PROP_POS_FRAMES: seeking in compressed H.264 can land on a
        # different frame. This is how the training frames were read.
        samples = []
        index = 0

        while index <= last:

            if not capture.grab():
                break

            if index in wanted:

                success, frame = capture.retrieve()

                if success and frame is not None:

                    samples.append(
                        FrameSample(
                            index=index,
                            timestamp=index / fps,
                            frame=frame,
                        )
                    )

            index += 1

        return samples


video_service = VideoService()