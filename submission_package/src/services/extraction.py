import base64
import io
from typing import Iterable

import fitz
from docx import Document as DocxDocument
from docx.document import Document as DocxDocumentType
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image

from ..config import get_settings
from ..exceptions import TextExtractionError, UnsupportedFileTypeError
from .ocr import extract_text_from_image


def decode_base64_file(file_base64: str) -> bytes:
    payload = file_base64.strip()
    if "," in payload and payload.lower().startswith("data:"):
        payload = payload.split(",", maxsplit=1)[1]

    try:
        return base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise TextExtractionError("The provided fileBase64 value is not valid Base64.") from exc


def _normalize_text(parts: Iterable[str]) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(cleaned).strip()


def _iter_docx_blocks(document: DocxDocumentType):
    parent = document.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def extract_docx_text(file_bytes: bytes) -> str:
    document = DocxDocument(io.BytesIO(file_bytes))
    chunks: list[str] = []

    for block in _iter_docx_blocks(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                chunks.append(text)
            continue

        if isinstance(block, Table):
            for row in block.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    chunks.append(row_text)

    text = _normalize_text(chunks)
    if not text:
        raise TextExtractionError("No readable text could be extracted from the DOCX file.")
    return text


def extract_image_text(file_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as exc:
        raise TextExtractionError("The provided image file could not be opened.") from exc

    try:
        text = extract_text_from_image(image)
    except Exception as exc:
        raise TextExtractionError(
            "OCR failed for the image. Ensure Tesseract is installed and configured."
        ) from exc

    if not text:
        raise TextExtractionError("No readable text could be extracted from the image.")
    return text


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise TextExtractionError("The provided PDF file could not be opened.") from exc

    page_chunks: list[str] = []
    for page in document:
        blocks = page.get_text("blocks", sort=True)
        block_text = _normalize_text(block[4] for block in blocks if len(block) > 4)

        if len(block_text) < 30:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            try:
                block_text = extract_text_from_image(image)
            except Exception as exc:
                raise TextExtractionError(
                    "OCR failed for a scanned PDF page. Ensure Tesseract is installed and configured."
                ) from exc

        if block_text:
            page_chunks.append(block_text)

    text = _normalize_text(page_chunks)
    if not text:
        raise TextExtractionError("No readable text could be extracted from the PDF.")
    return text


def extract_document_text(file_type: str, file_bytes: bytes) -> str:
    settings = get_settings()
    if len(file_bytes) > settings.max_file_size_bytes:
        raise TextExtractionError(
            f"File size exceeds the configured limit of {settings.max_file_size_mb} MB."
        )

    normalized_type = file_type.lower().strip()
    if normalized_type == "pdf":
        return extract_pdf_text(file_bytes)
    if normalized_type == "docx":
        return extract_docx_text(file_bytes)
    if normalized_type == "image":
        return extract_image_text(file_bytes)
    raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")
