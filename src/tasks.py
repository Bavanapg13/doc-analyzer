from .celery_app import celery_app
from .models import DocumentAnalyzeRequest
from .services.pipeline import process_document_request


@celery_app.task(name="document_analyzer.process_document")
def analyze_document_task(payload: dict) -> dict:
    request = DocumentAnalyzeRequest.model_validate(payload)
    response = process_document_request(request)
    return response.model_dump()
