from dataclasses import dataclass

import numpy as np

from app.config import settings


@dataclass
class Prediction:

    verdict: str

    fake_probability: float

    real_probability: float

    artifacts: list[str]

    suspicious_start: float | None

    suspicious_end: float | None


class DeepfakeDetector:

    def __init__(self):

        self.initialized = False

    def initialize(self):

        self.initialized = True

    def predict(
        self,
        crops: list[np.ndarray],
        timestamps: list[float],
    ) -> Prediction:

        if not crops:

            return Prediction(
                verdict="MODEL_UNAVAILABLE",
                fake_probability=0.0,
                real_probability=0.0,
                artifacts=[],
                suspicious_start=None,
                suspicious_end=None,
            )

        # -------------------------------------------------
        # TEMPORARY DEVELOPMENT MODE
        # -------------------------------------------------

        if settings.demo_mode:

            return Prediction(
                verdict="MODEL_UNAVAILABLE",
                fake_probability=0.50,
                real_probability=0.50,
                artifacts=[],
                suspicious_start=None,
                suspicious_end=None,
            )

        # -------------------------------------------------
        # REAL MODEL WILL BE PLACED HERE
        # -------------------------------------------------

        raise RuntimeError(
            "Real deepfake model has not been integrated yet."
        )


detector = DeepfakeDetector()