"""Functional guardrails for input and output moderation."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata

from src.security.pii_detection import PIIDetector


@dataclass(frozen=True)
class GuardrailResult:
    """Result returned by a guardrail evaluation."""

    allowed: bool
    reason: str
    sanitized_text: str
    detections: list[str] = field(default_factory=list)


class InputGuardrail:
    """Validates and sanitizes user prompts before they reach the model."""

    _OBFUSCATION_TRANSLATION = str.maketrans(
        {
            "0": "o",
            "1": "i",
            "3": "e",
            "4": "a",
            "5": "s",
            "7": "t",
            "@": "a",
            "$": "s",
            "!": "i",
        }
    )

    _PROMPT_INJECTION_PATTERNS = (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+o\s+contexto\s+anterior",
        r"forget\s+(everything|all|your\s+instructions)",
        r"revele?\s+(o\s+)?prompt\s+do\s+sistema",
        r"mostre?\s+(as\s+)?instru[cç][oõ]es\s+internas",
        r"system\s*:",
        r"<\|system\|>",
        r"\[INST\]",
    )
    _DATA_EXFILTRATION_PATTERNS = (
        r"(exporte|liste|retorne|mostre).*(cpf|e-?mail|telefone|api[_ -]?key|token)",
        r"dump.*(base|dataset|documentos?)",
        r"(mostre|retorne).*(segredo|secret|credencial|credential)",
    )
    _TOOL_ABUSE_PATTERNS = (
        r"(execute|rode|run).*(shell|terminal|comando)",
        r"(delete|apague|remova).*(arquivo|base|dataset)",
        r"(curl|wget|powershell|cmd\.exe|bash)",
    )

    def __init__(
        self,
        max_chars: int = 1_500,
        redact_pii: bool = True,
        allowed_topics: tuple[str, ...] | None = None,
    ) -> None:
        self.max_chars = max_chars
        self.redact_pii = redact_pii
        self.allowed_topics = tuple(topic.lower() for topic in allowed_topics or ())
        self.pii_detector = PIIDetector()
        self._prompt_patterns = self._compile(self._PROMPT_INJECTION_PATTERNS)
        self._exfiltration_patterns = self._compile(self._DATA_EXFILTRATION_PATTERNS)
        self._tool_patterns = self._compile(self._TOOL_ABUSE_PATTERNS)

    def evaluate(self, user_input: str) -> GuardrailResult:
        """Returns a decision for the provided user input."""
        text = user_input.strip()
        if not text:
            return GuardrailResult(False, "Input vazio.", "")

        normalized_text = self._normalize_for_security_checks(text)

        if len(text) > self.max_chars:
            return GuardrailResult(
                False,
                f"Input bloqueado por excesso de tamanho (> {self.max_chars} caracteres).",
                "",
                ["context_stuffing"],
            )

        if self._matches(normalized_text, self._prompt_patterns):
            return GuardrailResult(
                False,
                "Input bloqueado por tentativa de prompt injection ou vazamento de instrucoes.",
                "",
                ["prompt_injection"],
            )

        if self._matches(normalized_text, self._exfiltration_patterns):
            return GuardrailResult(
                False,
                "Input bloqueado por tentativa de exfiltracao de dados sensiveis.",
                "",
                ["data_exfiltration"],
            )

        if self._matches(normalized_text, self._tool_patterns):
            return GuardrailResult(
                False,
                "Input bloqueado por tentativa de abuso de ferramentas ou comandos.",
                "",
                ["tool_abuse"],
            )

        sanitized_text = text
        detections: list[str] = []
        if self.redact_pii and self.pii_detector.has_pii(text):
            sanitized_text = self.pii_detector.redact(text)
            detections.append("pii_redacted")

        if self.allowed_topics and not any(topic in sanitized_text.lower() for topic in self.allowed_topics):
            return GuardrailResult(
                False,
                "Input fora do escopo configurado para o assistente.",
                "",
                ["out_of_scope"],
            )

        return GuardrailResult(True, "OK", sanitized_text, detections)

    @staticmethod
    def _compile(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
        return tuple(re.compile(pattern, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)

    @staticmethod
    def _matches(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
        return any(pattern.search(text) for pattern in patterns)

    @classmethod
    def _normalize_for_security_checks(cls, text: str) -> str:
        """Normalizes text before regex checks to catch simple obfuscation."""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = normalized.lower().translate(cls._OBFUSCATION_TRANSLATION)
        normalized = re.sub(r"[\W_]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()


class OutputGuardrail:
    """Sanitizes and validates model responses before returning them."""

    _LEAKAGE_PATTERNS = (
        r"(prompt\s+do\s+sistema|system\s+prompt|instru[cç][oõ]es\s+internas)",
        r"(api[_ -]?key|token|secret|credencial)",
        r"(conte[uú]do\s+integral\s+da\s+base|dump\s+completo)",
    )
    _UNSAFE_FINANCE_PATTERNS = (
        r"(lucro|retorno)\s+garantido",
        r"compre\s+agora\s+sem\s+risco",
        r"venda\s+tudo\s+agora",
        r"invista\s+todo\s+o\s+capital",
    )

    def __init__(self, redact_pii: bool = True) -> None:
        self.redact_pii = redact_pii
        self.pii_detector = PIIDetector()
        self._leakage_patterns = InputGuardrail._compile(self._LEAKAGE_PATTERNS)
        self._unsafe_finance_patterns = InputGuardrail._compile(self._UNSAFE_FINANCE_PATTERNS)

    def evaluate(self, llm_output: str) -> GuardrailResult:
        """Returns a safe, sanitized response when possible."""
        text = llm_output.strip()
        if not text:
            return GuardrailResult(False, "Saida vazia.", "")

        if InputGuardrail._matches(text, self._leakage_patterns):
            return GuardrailResult(
                False,
                "Saida bloqueada por conter indicio de vazamento de instrucoes ou segredos.",
                "",
                ["sensitive_leakage"],
            )

        if InputGuardrail._matches(text, self._unsafe_finance_patterns):
            return GuardrailResult(
                False,
                "Saida bloqueada por linguagem de recomendacao financeira indevida.",
                "",
                ["unsafe_financial_advice"],
            )

        sanitized_text = text
        detections: list[str] = []
        if self.redact_pii and self.pii_detector.has_pii(text):
            sanitized_text = self.pii_detector.redact(text)
            detections.append("pii_redacted")

        return GuardrailResult(True, "OK", sanitized_text, detections)


class GuardrailService:
    """Convenience facade for request/response protection."""

    def __init__(
        self,
        input_guardrail: InputGuardrail | None = None,
        output_guardrail: OutputGuardrail | None = None,
    ) -> None:
        self.input_guardrail = input_guardrail or InputGuardrail()
        self.output_guardrail = output_guardrail or OutputGuardrail()

    def secure_exchange(self, user_input: str, llm_output: str) -> tuple[GuardrailResult, GuardrailResult]:
        """Evaluates a full request/response exchange."""
        input_result = self.input_guardrail.evaluate(user_input)
        if not input_result.allowed:
            return input_result, GuardrailResult(False, "Saida nao avaliada.", "")
        output_result = self.output_guardrail.evaluate(llm_output)
        return input_result, output_result
