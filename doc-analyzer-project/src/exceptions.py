class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed successfully."""


class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when a request contains an unsupported file type."""


class TextExtractionError(DocumentProcessingError):
    """Raised when text cannot be extracted from the input file."""
