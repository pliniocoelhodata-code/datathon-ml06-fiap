"""PII detection helpers with optional Presidio integration.

The project currently uses lightweight regex-based detection by default so the
guardrails remain functional even when Presidio models are not installed in the
execution environment.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:  # pragma: no cover - optional runtime dependency
    AnalyzerEngine = None
    AnonymizerEngine = None


@dataclass(frozen=True)
class PIIMatch:
    """Represents a single PII match detected in text."""

    entity_type: str
    start: int
    end: int
    text: str
    score: float


class PIIDetector:
    """Detects and redacts common PII patterns.

    The default regex patterns focus on data that is especially relevant to the
    project context: Brazilian identifiers, personal contacts and credentials
    that should never be exposed by the model.
    """

    _REGEX_PATTERNS: dict[str, str] = {
        "BR_CPF": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b",
        "EMAIL_ADDRESS": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        "PHONE_NUMBER": r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}|\d{4})-?\d{4}\b",
        "API_KEY": r"\b(?:sk|rk|pk)_[A-Za-z0-9]{16,}\b",
    }

    def __init__(self, language: str = "pt", use_presidio: bool = False) -> None:
        self.language = language
        self.use_presidio = use_presidio and AnalyzerEngine is not None
        self._compiled_patterns = {
            entity: re.compile(pattern, flags=re.IGNORECASE)
            for entity, pattern in self._REGEX_PATTERNS.items()
        }
        self._analyzer = AnalyzerEngine() if self.use_presidio else None
        self._anonymizer = AnonymizerEngine() if self.use_presidio else None

    def scan(self, text: str) -> list[PIIMatch]:
        """Returns detected PII spans without mutating the input."""
        matches = self._scan_regex(text)
        if self._analyzer is not None:
            matches.extend(self._scan_presidio(text))
        return self._deduplicate(matches)

    def has_pii(self, text: str) -> bool:
        """Returns whether the text contains any PII."""
        return bool(self.scan(text))

    def redact(self, text: str, replacement: str = "[REDACTED]") -> str:
        """Redacts all detected PII spans from a text."""
        matches = sorted(self.scan(text), key=lambda item: (item.start, item.end))
        if not matches:
            return text

        redacted_parts: list[str] = []
        last_end = 0
        for match in matches:
            if match.start < last_end:
                continue
            redacted_parts.append(text[last_end:match.start])
            redacted_parts.append(replacement)
            last_end = match.end
        redacted_parts.append(text[last_end:])
        return "".join(redacted_parts)

    def _scan_regex(self, text: str) -> list[PIIMatch]:
        matches: list[PIIMatch] = []
        for entity_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        score=0.8,
                    )
                )
        return matches

    def _scan_presidio(self, text: str) -> list[PIIMatch]:
        assert self._analyzer is not None  # for type-checkers
        results = self._analyzer.analyze(text=text, language=self.language)
        return [
            PIIMatch(
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                text=text[result.start : result.end],
                score=float(result.score),
            )
            for result in results
        ]

    @staticmethod
    def _deduplicate(matches: Iterable[PIIMatch]) -> list[PIIMatch]:
        unique: dict[tuple[str, int, int], PIIMatch] = {}
        for match in matches:
            key = (match.entity_type, match.start, match.end)
            previous = unique.get(key)
            if previous is None or match.score > previous.score:
                unique[key] = match
        return list(unique.values())
