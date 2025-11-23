from pathlib import Path
from typing import Iterable

from fastapi import UploadFile, HTTPException, status


ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx"}
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
DEFAULT_MAX_UPLOAD_MB = 5


class UploadValidationError(HTTPException):
    """Erreur dédiée à la validation d'upload."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


def _extension_allowed(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def _mime_allowed(content_type: str | None) -> bool:
    if content_type is None:
        return False
    return content_type.lower() in ALLOWED_MIME_TYPES


async def validate_and_read_upload(
    upload: UploadFile,
    max_upload_mb: int | None = None,
    allowed_extensions: Iterable[str] | None = None,
    allowed_mime_types: Iterable[str] | None = None,
) -> bytes:
    """
    Valide un fichier uploadé (extension, MIME, taille) et renvoie ses bytes.

    - Vérifie l'extension (PDF/DOCX)
    - Vérifie le content-type
    - Limite la taille à `max_upload_mb` (par défaut DEFAULT_MAX_UPLOAD_MB)

    Lève UploadValidationError (hérite de HTTPException) en cas de problème.
    """
    if max_upload_mb is None:
        max_upload_mb = DEFAULT_MAX_UPLOAD_MB

    allowed_extensions_set = set(allowed_extensions or ALLOWED_EXTENSIONS)
    allowed_mime_types_set = set(allowed_mime_types or ALLOWED_MIME_TYPES)

    if not _extension_allowed(upload.filename or ""):
        raise UploadValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de fichier non supporté. Utilise un PDF ou un DOCX.",
        )

    if not _mime_allowed(upload.content_type):
        raise UploadValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type de contenu non supporté pour ce fichier.",
        )

    max_bytes = max_upload_mb * 1024 * 1024
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await upload.read(1024 * 1024)  # 1 Mo
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadValidationError(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux (max {max_upload_mb} Mo).",
            )
        chunks.append(chunk)

    if total == 0:
        raise UploadValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier vide ou illisible.",
        )

    return b"".join(chunks)
