import re
from collections import Counter

from dateparser.search import search_dates
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..models import ExtractedEntities

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)"
)

ORG_SUFFIXES = {
    "bank",
    "college",
    "company",
    "corp",
    "corporation",
    "foundation",
    "inc",
    "institute",
    "labs",
    "limited",
    "ltd",
    "llc",
    "pvt",
    "private",
    "solutions",
    "technologies",
    "technology",
    "university",
}

analyzer = SentimentIntensityAnalyzer()


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", value).strip()
        if not normalized:
            continue
        marker = normalized.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        output.append(normalized)
    return output


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def build_extractive_summary(text: str, max_sentences: int = 3) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered_words = [word for word in words if word not in STOPWORDS]
    if not filtered_words:
        return " ".join(sentences[:max_sentences])

    frequencies = Counter(filtered_words)
    max_count = max(frequencies.values())
    normalized = {word: count / max_count for word, count in frequencies.items()}

    scored: list[tuple[int, float]] = []
    for index, sentence in enumerate(sentences):
        sentence_words = re.findall(r"\b[a-zA-Z]{3,}\b", sentence.lower())
        score = sum(normalized.get(word, 0.0) for word in sentence_words)
        if score > 0:
            scored.append((index, score))

    selected_indices = sorted(
        index for index, _ in sorted(scored, key=lambda item: item[1], reverse=True)[:max_sentences]
    )
    if not selected_indices:
        selected_indices = list(range(min(max_sentences, len(sentences))))

    return " ".join(sentences[index] for index in selected_indices)


def extract_dates(text: str) -> list[str]:
    explicit_patterns = [
        re.compile(rf"\b\d{{1,2}}\s+{MONTH_PATTERN}\s+\d{{4}}\b", re.IGNORECASE),
        re.compile(rf"\b{MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),
        re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
        re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),
    ]

    matches: list[str] = []
    for pattern in explicit_patterns:
        matches.extend(pattern.findall(text))

    results = search_dates(
        text,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DAY_OF_MONTH": "first",
        },
    )
    if results:
        for match, _ in results:
            cleaned = match.strip()
            if len(cleaned) < 6:
                continue
            if re.search(MONTH_PATTERN, cleaned, flags=re.IGNORECASE) and re.search(r"\d", cleaned):
                matches.append(cleaned)
            elif re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", cleaned):
                matches.append(cleaned)
            elif re.fullmatch(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}", cleaned):
                matches.append(cleaned)

    return _unique_preserve_order(matches)


def extract_amounts(text: str) -> list[str]:
    currency_pattern = re.compile(
        r"(?:[$€£₹]|Rs\.?|INR|USD|EUR|GBP)\s?\d[\d,]*(?:\.\d{1,2})?|\b\d[\d,]*(?:\.\d{1,2})?\s?(?:USD|INR|EUR|GBP|rupees?|dollars?)\b",
        re.IGNORECASE,
    )
    contextual_pattern = re.compile(
        r"\b(?:amount|balance|cost|emi|fee|fees|payment|price|total)\b(?:\s+\w+){0,3}\s+([?]?\d[\d,]*(?:\.\d{1,2})?)",
        re.IGNORECASE,
    )

    matches = currency_pattern.findall(text)
    contextual_matches = [match.lstrip("?").strip() for match in contextual_pattern.findall(text)]
    combined = _unique_preserve_order(matches + contextual_matches)

    filtered: list[str] = []
    lowered = [value.casefold() for value in combined]
    for index, value in enumerate(combined):
        bare_value = re.sub(r"^(?:[$€£₹]|Rs\.?|INR|USD|EUR|GBP)\s*", "", value, flags=re.IGNORECASE)
        has_richer_variant = any(
            other_index != index and bare_value and bare_value.casefold() in lowered[other_index]
            and lowered[other_index] != bare_value.casefold()
            for other_index in range(len(combined))
        )
        if not has_richer_variant:
            filtered.append(value)

    return filtered


def extract_organizations(text: str) -> list[str]:
    pattern = re.compile(
        r"\b([A-Z][\w&.,'-]*(?:\s+[A-Z][\w&.,'-]*)*\s+(?:Inc|Ltd|LLC|Corporation|Corp|Company|Co|Pvt|Private|Institute|University|Bank|Solutions|Technologies))\b"
    )
    return _unique_preserve_order(pattern.findall(text))


def extract_names(text: str, organizations: list[str]) -> list[str]:
    org_markers = {org.casefold() for org in organizations}
    candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", text)

    filtered: list[str] = []
    for candidate in candidates:
        marker = candidate.casefold()
        tokens = {token.casefold() for token in candidate.split()}
        if marker in org_markers:
            continue
        if tokens & ORG_SUFFIXES:
            continue
        if candidate in {"Data Science", "Machine Learning", "Artificial Intelligence"}:
            continue
        filtered.append(candidate)

    return _unique_preserve_order(filtered)


def classify_sentiment(text: str) -> str:
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.5:
        return "Positive"
    if compound <= -0.5:
        return "Negative"
    return "Neutral"


def build_heuristic_entities(text: str) -> ExtractedEntities:
    organizations = extract_organizations(text)
    return ExtractedEntities(
        names=extract_names(text, organizations),
        dates=extract_dates(text),
        organizations=organizations,
        amounts=extract_amounts(text),
    )
