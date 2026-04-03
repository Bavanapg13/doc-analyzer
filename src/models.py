from typing import Literal

from pydantic import BaseModel, Field


class DocumentAnalyzeRequest(BaseModel):
    fileName: str = Field(..., min_length=1)
    fileType: Literal["pdf", "docx", "image"]
    fileBase64: str = Field(..., min_length=1)


class ExtractedEntities(BaseModel):
    names: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)


class DocumentAnalyzeResponse(BaseModel):
    status: Literal["success"] = "success"
    fileName: str
    summary: str
    entities: ExtractedEntities
    sentiment: Literal["Positive", "Neutral", "Negative"]


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str
