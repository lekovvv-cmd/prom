from __future__ import annotations

import codecs
import zipfile
from pathlib import Path

from platform_sdk.error_types import ValidationFailed
from platform_sdk.storage import IncomingFile, safe_file_name

CONTENT_TYPE_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".zip": "application/zip",
}
OOXML_MAIN_PART_BY_EXTENSION = {
    ".docx": "word/document.xml",
    ".xlsx": "xl/workbook.xml",
    ".pptx": "ppt/presentation.xml",
}
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
MAX_ARCHIVE_ENTRIES = 10_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024


def validate_metadata(file: IncomingFile) -> tuple[str, str, str | None]:
    original_name = file.file_name or "attachment"
    normalized_name = safe_file_name(original_name)
    extension = Path(normalized_name).suffix.lower()
    if extension not in CONTENT_TYPE_BY_EXTENSION:
        raise ValidationFailed("Недопустимое расширение файла")
    declared = (file.content_type or "").partition(";")[0].strip().lower() or None
    allowed_declared = set(CONTENT_TYPE_BY_EXTENSION.values())
    if declared is not None and declared not in allowed_declared:
        raise ValidationFailed("Недопустимый MIME-тип файла")
    if declared is not None and declared != CONTENT_TYPE_BY_EXTENSION[extension]:
        raise ValidationFailed("MIME-тип не соответствует расширению файла")
    return normalized_name, extension, declared


def detect_and_validate(path: Path, extension: str) -> str:
    detected = CONTENT_TYPE_BY_EXTENSION[extension]
    if extension == ".pdf":
        valid = _starts_with(path, b"%PDF-")
    elif extension in {".doc", ".xls", ".ppt"}:
        valid = _starts_with(path, OLE_SIGNATURE)
    elif extension == ".png":
        valid = _starts_with(path, b"\x89PNG\r\n\x1a\n")
    elif extension in {".jpg", ".jpeg"}:
        valid = _starts_with(path, b"\xff\xd8\xff")
    elif extension in {".txt", ".md", ".csv"}:
        valid = _is_utf8_text(path)
    elif extension in OOXML_MAIN_PART_BY_EXTENSION:
        valid = _is_valid_zip(
            path,
            required_parts={
                "[Content_Types].xml",
                "_rels/.rels",
                OOXML_MAIN_PART_BY_EXTENSION[extension],
            },
        )
    elif extension == ".zip":
        valid = _is_valid_zip(path)
    else:  # pragma: no cover - guarded by metadata validation
        valid = False
    if not valid:
        raise ValidationFailed(
            "Содержимое файла не соответствует его расширению"
        )
    return detected


def _starts_with(path: Path, signature: bytes) -> bool:
    with path.open("rb") as source:
        return source.read(len(signature)) == signature


def _is_utf8_text(path: Path) -> bool:
    decoder = codecs.getincrementaldecoder("utf-8")()
    try:
        with path.open("rb") as source:
            while chunk := source.read(64 * 1024):
                if b"\x00" in chunk:
                    return False
                decoder.decode(chunk)
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        return False
    return True


def _is_valid_zip(path: Path, required_parts: set[str] | None = None) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                return False
            if sum(entry.file_size for entry in entries) > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                return False
            names = {entry.filename for entry in entries}
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return False
    return not required_parts or required_parts.issubset(names)
