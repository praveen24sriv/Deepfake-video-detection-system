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

    sample_frames: int = 10
    blur_threshold: float = 50.0
    frame_size: tuple[int, int] = (224, 224)

    model_name: str = "DeepGuard Spatiotemporal Detector"
    model_version: str = "0.1.0-demo"

    # Keep this TRUE until your actual trained model is integrated.
    demo_mode: bool = True

    cors_origins: list[str] = [
        "http://localhost:5173",
    ]

    upload_dir: Path = BASE_DIR / "uploads"
    output_dir: Path = BASE_DIR / "outputs"

    model_path: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()