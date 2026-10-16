from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "DeepGuard AI Backend"
    api_version: str = "1.0.0"

    host: str = "127.0.0.1"
    port: int = 8000

    max_upload_size_mb: int = 500

    allowed_extensions: tuple[str, ...] = (
        ".mp4",
        ".avi",
        ".mov",
    )

    # Video preprocessing
    extracted_frames: int = 32
    sample_frames: int = 16

    # Face preprocessing
    blur_threshold: float = 50.0
    frame_size: tuple[int, int] = (224, 224)
    face_crop_margin: float = 1.3

    model_name: str = "DeepGuard Spatiotemporal Detector (EfficientNet-B0 + BiLSTM)"
    model_version: str = "1.0.0"

    # True = skip the model and return MODEL_UNAVAILABLE (no torch needed).
    demo_mode: bool = False

    cors_origins: list[str] = [
        "http://localhost:5173",
    ]

    upload_dir: Path = BASE_DIR / "uploads"
    output_dir: Path = BASE_DIR / "outputs"

    # Relative paths are resolved from the backend/ folder.
    model_path: str = "models/deepguard_v1.pt"
    # "" = auto (CUDA if available, else CPU); or "cpu" / "cuda".
    model_device: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()