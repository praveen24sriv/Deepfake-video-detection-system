import cv2

import numpy as np

from app.config import settings


class QualityService:

    def laplacian_variance(
        self,
        image: np.ndarray,
    ) -> float:

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        return float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

    def is_blurry(
        self,
        image: np.ndarray,
    ) -> bool:

        variance = self.laplacian_variance(
            image
        )

        return variance < settings.blur_threshold


quality_service = QualityService()