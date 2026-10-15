
import cv2
import numpy as np
from facenet_pytorch import MTCNN

from app.config import settings


class FaceDetectionService:
    def __init__(self):
        self.detector = MTCNN(
            keep_all=True,
            device="cpu",
        )

    def detect(self, frame):
        if frame is None or frame.size == 0:
            return []

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes, _ = self.detector.detect(rgb)

        if boxes is None:
            return []

        height, width = frame.shape[:2]
        results = []

        for box in boxes:
            if box is None:
                continue

            try:
                box = np.asarray(box, dtype=np.float64).reshape(-1)
            except (TypeError, ValueError):
                continue

            if box.size < 4 or not np.isfinite(box[:4]).all():
                continue

            x1, y1, x2, y2 = box[:4]

            x1 = max(0, int(np.floor(x1)))
            y1 = max(0, int(np.floor(y1)))
            x2 = min(width, int(np.ceil(x2)))
            y2 = min(height, int(np.ceil(y2)))

            if x2 > x1 and y2 > y1:
                results.append(
                    (x1, y1, x2 - x1, y2 - y1)
                )

        return results

    def crop_largest(self, frame, boxes):
        if frame is None or frame.size == 0 or not boxes:
            return None

        x, y, w, h = max(
            boxes,
            key=lambda box: box[2] * box[3],
        )

        if w <= 0 or h <= 0:
            return None

        # Same square crop as training (deepguard.square_box): side = longest
        # face side x margin, limited to the frame, and shifted to stay inside it.
        height, width = frame.shape[:2]
        center_x = x + w / 2.0
        center_y = y + h / 2.0

        side = min(max(w, h) * settings.face_crop_margin, width, height)
        x1 = int(np.clip(center_x - side / 2.0, 0, width - side))
        y1 = int(np.clip(center_y - side / 2.0, 0, height - side))
        x2 = x1 + int(side)
        y2 = y1 + int(side)

        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        return cv2.resize(
            crop,
            settings.frame_size,
            interpolation=cv2.INTER_AREA,
        )


face_service = FaceDetectionService()
