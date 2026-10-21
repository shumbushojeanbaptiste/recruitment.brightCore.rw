
import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class StoredCV:
    storage_key: str
    original_filename: str
    size_bytes: int
    sha256: str
    path: Path


def _safe_original_filename(filename: str | None) -> str:
    name = (filename or "cv.pdf").replace("\\", "/").split("/")[-1]
    name = "".join(
        ch for ch in name
        if ch.isalnum() or ch in " ._-()"
    ).strip(" .")

    if not name:
        name = "cv.pdf"

    return name[:255]


async def store_cv(upload: UploadFile) -> StoredCV:
    settings = get_settings()

    original_filename = _safe_original_filename(upload.filename)

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CV must be a PDF file",
        )

    if upload.content_type not in (
        "application/pdf",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CV content type must be PDF",
        )

    root = Path(settings.cv_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4().hex}.pdf"
    destination = root / storage_key

    total = 0
    digest = hashlib.sha256()
    first_bytes = bytearray()

    try:
        with destination.open("xb") as output:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break

                total += len(chunk)

                if total > settings.cv_max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="CV must not exceed 5 MB",
                    )

                if len(first_bytes) < 5:
                    first_bytes.extend(chunk[: 5 - len(first_bytes)])

                digest.update(chunk)
                output.write(chunk)

        if bytes(first_bytes) != b"%PDF-":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded file is not a valid PDF signature",
            )

        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CV file is empty",
            )

        return StoredCV(
            storage_key=storage_key,
            original_filename=original_filename,
            size_bytes=total,
            sha256=digest.hexdigest(),
            path=destination,
        )

    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def resolve_cv_path(storage_key: str) -> Path:
    root = Path(get_settings().cv_storage_path).resolve()
    path = (root / storage_key).resolve()

    if path.parent != root or not path.is_file():
        raise FileNotFoundError("CV file not found")

    return path


def delete_cv(storage_key: str) -> None:
    try:
        resolve_cv_path(storage_key).unlink(missing_ok=True)
    except FileNotFoundError:
        pass
