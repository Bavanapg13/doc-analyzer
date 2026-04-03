import json
import logging

from ..config import get_settings
from ..models import DocumentAnalyzeResponse, ExtractedEntities
from .heuristics import build_extractive_summary, build_heuristic_entities, classify_sentiment

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def analyze(self, text: str, file_name: str) -> DocumentAnalyzeResponse:
        truncated_text = text[: self.settings.max_analysis_characters]

        if self._should_use_openai():
            try:
                return self._analyze_with_openai(truncated_text, file_name)
            except Exception as exc:  # pragma: no cover - fallback path
                logger.warning("OpenAI analysis failed, falling back to heuristics: %s", exc)

        return self._analyze_with_heuristics(truncated_text, file_name)

    def _should_use_openai(self) -> bool:
        provider = self.settings.analysis_provider
        if provider == "heuristic":
            return False
        if provider == "openai":
            return bool(self.settings.openai_api_key)
        return bool(self.settings.openai_api_key)

    def _analyze_with_openai(self, text: str, file_name: str) -> DocumentAnalyzeResponse:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        system_prompt = (
            "You extract structured insights from documents. "
            "Return strict JSON with keys summary, entities, and sentiment. "
            "entities must contain names, dates, organizations, and amounts. "
            "sentiment must be exactly one of Positive, Neutral, or Negative."
        )
        user_prompt = (
            "Analyze the following document text.\n"
            "Produce a concise summary and key entities.\n"
            "If an entity type is absent, return an empty array.\n"
            "Document text:\n"
            f"{text}"
        )

        response = client.chat.completions.create(
            model=self.settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        entities = self._normalize_entities(parsed.get("entities", {}))
        sentiment = self._normalize_sentiment(parsed.get("sentiment"))
        summary = str(parsed.get("summary", "")).strip() or build_extractive_summary(text)

        return DocumentAnalyzeResponse(
            fileName=file_name,
            summary=summary,
            entities=entities,
            sentiment=sentiment,
        )

    def _analyze_with_heuristics(self, text: str, file_name: str) -> DocumentAnalyzeResponse:
        return DocumentAnalyzeResponse(
            fileName=file_name,
            summary=build_extractive_summary(text),
            entities=build_heuristic_entities(text),
            sentiment=classify_sentiment(text),
        )

    def _normalize_entities(self, data: dict) -> ExtractedEntities:
        return ExtractedEntities(
            names=self._normalize_string_list(data.get("names")),
            dates=self._normalize_string_list(data.get("dates")),
            organizations=self._normalize_string_list(data.get("organizations")),
            amounts=self._normalize_string_list(data.get("amounts")),
        )

    def _normalize_string_list(self, values: object) -> list[str]:
        if not isinstance(values, list):
            return []

        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, str):
                continue
            normalized = " ".join(value.split()).strip()
            if not normalized:
                continue
            marker = normalized.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            output.append(normalized)
        return output

    def _normalize_sentiment(self, value: object) -> str:
        if isinstance(value, str):
            normalized = value.strip().capitalize()
            if normalized in {"Positive", "Neutral", "Negative"}:
                return normalized
        return "Neutral"
