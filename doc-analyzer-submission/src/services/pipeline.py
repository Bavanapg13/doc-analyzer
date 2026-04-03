from ..models import DocumentAnalyzeRequest, DocumentAnalyzeResponse
from .analysis import AnalysisService
from .extraction import decode_base64_file, extract_document_text


def process_document_request(payload: DocumentAnalyzeRequest) -> DocumentAnalyzeResponse:
    file_bytes = decode_base64_file(payload.fileBase64)
    text = extract_document_text(payload.fileType, file_bytes)
    analysis_service = AnalysisService()
    return analysis_service.analyze(text=text, file_name=payload.fileName)
