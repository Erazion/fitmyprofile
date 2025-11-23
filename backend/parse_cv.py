from __future__ import annotations

import io
from pathlib import Path

import fitz  # PyMuPDF
import docx  # python-docx
from fastapi import UploadFile, HTTPException, status


def clean_text(text: str) -> str:
    """Nettoyage simple : trim + normalisation des espaces."""
    if not text:
        return ""
    # remplacement des retours chariot multiples par un seul
    lines = [line.strip() for line in text.splitlines()]
    joined = " ".join(line for line in lines if line)
    # collapse espaces multiples
    while "  " in joined:
        joined = joined.replace("  ", " ")
    return joined.strip()


def parse_pdf_bytes(data: bytes) -> str:
    """Extrait le texte d'un PDF (bytes) via PyMuPDF."""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de lire le PDF.",
        ) from exc

    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text("text") or "")

    return clean_text("\n".join(parts))


def parse_docx_bytes(data: bytes) -> str:
    """Extrait le texte d'un DOCX (bytes) via python-docx."""
    try:
        file_obj = io.BytesIO(data)
        document = docx.Document(file_obj)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de lire le fichier DOCX.",
        ) from exc

    parts: list[str] = []
    for para in document.paragraphs:
        if para.text:
            parts.append(para.text)

    return clean_text("\n".join(parts))


async def extract_text_from_validated_upload(
    upload: UploadFile,
    file_bytes: bytes,
) -> str:
    """
    Choisit le parser adapté (PDF/DOCX) selon l'extension du fichier déjà validé.

    `file_bytes` doit déjà avoir été validé par `validate_and_read_upload`.
    """
    ext = Path(upload.filename or "").suffix.lower()

    if ext == ".pdf":
        return parse_pdf_bytes(file_bytes)
    if ext == ".docx":
        return parse_docx_bytes(file_bytes)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Format de fichier non supporté pour l'extraction de texte.",
    )
