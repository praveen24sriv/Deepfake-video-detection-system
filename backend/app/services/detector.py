"""
Deepfake detector service.

Wraps the trained DeepGuard model (CNN + BiLSTM) from app/services/deepguard.py,
a copy of ml_pipeline/deepguard.py. The model file is NOT in git: download
deepguard_v1.pt into backend/models/ (see backend/models/README.md).

Contract with analysis_service:
    predict(crops, timestamps, heatmap_path)
    - crops: RGB face crops from deepguard.FaceCropper (the training cropper),
      224x224, 1.3x margin, in time order
"""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.config import BASE_DIR, settings


@dataclass
class Prediction:
    verdict: str                      # REAL | FAKE | NO_FACE | MODEL_UNAVAILABLE
    fake_probability: float
    real_probability: float
    artifacts: list[str]
    suspicious_start: float | None
    suspicious_end: float | None
    frame_scores: list[float] = field(default_factory=list)
    heatmap_written: bool = False


def _round(seconds: float | None) -> float | None:
    return None if seconds is None else round(seconds, 2)


def _empty(verdict: str) -> Prediction:
    return Prediction(
        verdict=verdict,
        fake_probability=0.0,
        real_probability=0.0,
        artifacts=[],
        suspicious_start=None,
        suspicious_end=None,
    )


class DeepfakeDetector:
    def __init__(self):
        self.initialized = False
        self.predictor = None

    @property
    def available(self) -> bool:
        return self.predictor is not None

    def initialize(self):
        """Load the model once at startup. Demo mode skips loading."""
        if settings.demo_mode:
            self.initialized = True
            return

        model_path = Path(settings.model_path)
        if not model_path.is_absolute():
            model_path = BASE_DIR / model_path
        if not model_path.is_file():
            raise RuntimeError(
                f"Model file not found: {model_path}. Download deepguard_v1.pt into "
                "backend/models/ (see backend/models/README.md), or set DEMO_MODE=true."
            )

        # Imported here so demo mode works without torch installed.
        from app.services.deepguard import DeepGuardPredictor

        self.predictor = DeepGuardPredictor(model_path, device=settings.model_device or None)
        self.initialized = True

    def predict(
        self,
        crops: list[np.ndarray],
        timestamps: list[float],
        heatmap_path: Path | None = None,
    ) -> Prediction:
        if not crops:
            return _empty("NO_FACE")

        if not self.available:
            return _empty("MODEL_UNAVAILABLE")

        result = self.predictor.predict_crops(crops, timestamps, heatmap_path=heatmap_path)

        return Prediction(
            verdict=result["verdict"],
            fake_probability=result["fake_probability"],
            real_probability=result["real_probability"],
            artifacts=[],
            suspicious_start=_round(result["suspicious_start"]),
            suspicious_end=_round(result["suspicious_end"]),
            frame_scores=result["frame_scores"],
            heatmap_written=heatmap_path is not None,
        )


detector = DeepfakeDetector()
