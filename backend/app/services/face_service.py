
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

        height, width = frame.shape[:2]
        center_x = x + w / 2.0
        center_y = y + h / 2.0

        side = max(
            1,
            int(np.ceil(max(w, h) * settings.face_crop_margin)),
        )

        padded = cv2.copyMakeBorder(
            frame,
            top=side,
            bottom=side,
            left=side,
            right=side,
            borderType=cv2.BORDER_REPLICATE,
        )

        center_x += side
        center_y += side

        x1 = int(round(center_x - side / 2.0))
        y1 = int(round(center_y - side / 2.0))
        x2 = x1 + side
        y2 = y1 + side

        crop = padded[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        return cv2.resize(
            crop,
            settings.frame_size,
            interpolation=cv2.INTER_AREA,
        )


face_service = FaceDetectionService()
