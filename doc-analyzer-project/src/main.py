from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .exceptions import DocumentProcessingError
from .models import DocumentAnalyzeRequest, DocumentAnalyzeResponse, ErrorResponse
from .security import verify_api_key
from .services.pipeline import process_document_request

app = FastAPI(
    title="Data Extraction API",
    version="1.0.0",
    description="Track 2 AI-powered document analysis and extraction service.",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(DocumentProcessingError)
async def document_processing_exception_handler(
    request: Request,
    exc: DocumentProcessingError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message=str(exc)).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=message).model_dump(),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post(
    "/api/document-analyze",
    response_model=DocumentAnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def analyze_document(
    payload: DocumentAnalyzeRequest,
    _: None = Depends(verify_api_key),
) -> DocumentAnalyzeResponse:
    return process_document_request(payload)
