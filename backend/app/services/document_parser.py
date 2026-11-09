"""PDF / DOCX parsing with real content validation. Uploaded files are parsed in memory and never written to disk."""
import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePath

from app.config import get_settings
from app.services.text_utils import normalize_whitespace


class DocumentError(Exception):
    """A user-facing document problem. `code` is machine-readable; `status` is the HTTP status to return."""

    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    text: str


ALLOWED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx"}
_MAX_UNCOMPRESSED = 50 * 1024 * 1024  # zip-bomb guard for DOCX


def parse_document(filename: str, data: bytes) -> ParsedDocument:
    settings = get_settings()
    safe_name = PurePath((filename or "").replace("\\", "/")).name[:255] or "resume"
    ext = PurePath(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentError("unsupported_file_type", "Unsupported file type. Please upload a PDF or DOCX resume.", 415)
    if not data:
        raise DocumentError("empty_file", "The uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise DocumentError("file_too_large", f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.", 413)

    file_type = ALLOWED_EXTENSIONS[ext]
    if file_type == "pdf":
        if not data.lstrip()[:5].startswith(b"%PDF"):
            raise DocumentError("content_mismatch", "The file content is not a valid PDF.", 415)
        text = _parse_pdf(data, settings.max_pdf_pages)
    else:
        if not data.startswith(b"PK"):
            raise DocumentError("content_mismatch", "The file content is not a valid DOCX document.", 415)
        text = _parse_docx(data)

    text = normalize_whitespace(text)
    if not text:
        raise DocumentError(
            "no_extractable_text",
            "No readable text was found. Scanned or image-only documents need OCR, which ResumeIQ does not support yet.",
        )
    if len(text) > settings.max_resume_chars:
        text = text[: settings.max_resume_chars]
    return ParsedDocument(safe_name, file_type, text)


def _parse_pdf(data: bytes, max_pages: int) -> str:
    import pymupdf as fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentError("corrupted_file", "The PDF could not be opened. It may be corrupted.") from exc
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise DocumentError("encrypted_file", "Password-protected PDFs are not supported.")
        if doc.page_count > max_pages:
            raise DocumentError("too_many_pages", f"PDF has more than {max_pages} pages.", 413)
        return "\n".join(page.get_text("text") for page in doc)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("corrupted_file", "The PDF could not be read. It may be corrupted.") from exc
    finally:
        doc.close()


def _parse_docx(data: bytes) -> str:
    from docx import Document

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
            if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                raise DocumentError("content_mismatch", "The file is a ZIP archive but not a valid DOCX document.", 415)
            if sum(i.file_size for i in zf.infolist()) > _MAX_UNCOMPRESSED:
                raise DocumentError("file_too_large", "The document expands to an unreasonable size.", 413)
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells if c.text.strip()))
        return "\n".join(parts)
    except DocumentError:
        raise
    except Exception as exc:  # zipfile.BadZipFile, KeyError, XML errors ...
        raise DocumentError("corrupted_file", "The DOCX could not be read. It may be corrupted.") from exc
