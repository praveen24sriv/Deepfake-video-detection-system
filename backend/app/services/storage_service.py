import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


class StorageService:

    def __init__(self):
        settings.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        settings.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save_upload(
        self,
        file: UploadFile,
    ) -> Path:

        filename = file.filename or ""

        extension = Path(filename).suffix.lower()

        if extension not in settings.allowed_extensions:
            raise ValueError(
                f"Unsupported video format: "
                f"{extension or 'unknown'}"
            )

        destination = (
            settings.upload_dir
            / f"{uuid.uuid4().hex}{extension}"
        )

        max_bytes = (
            settings.max_upload_size_mb
            * 1024
            * 1024
        )

        total_bytes = 0

        try:

            with destination.open("wb") as output:

                while True:

                    chunk = await file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    total_bytes += len(chunk)

                    if total_bytes > max_bytes:

                        raise ValueError(
                            f"Video exceeds "
                            f"{settings.max_upload_size_mb} MB limit."
                        )

                    output.write(chunk)

        except Exception:

            destination.unlink(
                missing_ok=True
            )

            raise

        finally:

            await file.close()

        return destination

    def delete_file(
        self,
        path: Path,
    ):

        path.unlink(
            missing_ok=True
        )


storage_service = StorageService()