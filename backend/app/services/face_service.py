import cv2
import numpy as np


class FaceDetectionService:

    def __init__(self):

        self.detector = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

    def detect(
        self,
        frame: np.ndarray,
    ):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
        )

        # OpenCV versions can return either a tuple
        # or a NumPy array here.
        if faces is None:
            return []

        return [
            tuple(map(int, face))
            for face in faces
        ]

    def crop_largest(
        self,
        frame: np.ndarray,
        boxes,
    ):

        if not boxes:
            return None

        x, y, w, h = max(
            boxes,
            key=lambda box: box[2] * box[3],
        )

        crop = frame[
            y:y + h,
            x:x + w,
        ]

        if crop.size == 0:
            return None

        return crop


face_service = FaceDetectionService()