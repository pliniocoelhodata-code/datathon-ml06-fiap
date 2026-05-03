"""Functional guardrails for input and output moderation."""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass, field

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
            "|": "i",
        }
    )
    _CONFUSABLE_TRANSLATION = str.maketrans(
        {
            "а": "a",
            "е": "e",
            "і": "i",
            "о": "o",
            "р": "p",
            "с": "c",
            "у": "y",
            "х": "x",
            "ѕ": "s",
            "А": "a",
            "Е": "e",
            "І": "i",
            "О": "o",
            "Р": "p",
            "Х": "x",
            "Α": "a",
            "Ε": "e",
            "Ι": "i",
            "Ο": "o",
            "Ρ": "p",
            "С": "c",
            "Χ": "x",
        }
    )
    _ZERO_WIDTH_PATTERN = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")
    _BASE64_CANDIDATE_PATTERN = re.compile(
        r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])"
    )

    _PROMPT_INJECTION_PATTERNS = (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(todas\s+)?(as\s+)?instrucoes\s+anteriores",
        r"ignore\s+o\s+contexto\s+anterior",
        r"desconsidere\s+(todas\s+)?(as\s+)?instrucoes\s+anteriores",
        r"desconsidere\s+o\s+contexto\s+anterior",
        r"forget\s+(everything|all|your\s+instructions)",
        r"bypass\s+(the\s+)?(policy|guardrails|rules|safety)",
        r"(developer|system)\s+(message|prompt|instructions?)",
        r"revele?\s+(o\s+)?prompt\s+do\s+sistema",
        r"reveal\s+(the\s+)?(system|developer)\s+(prompt|message|instructions?)",
        r"mostre?\s+(as\s+)?instru[cç][oõ]es\s+internas",
        r"mostre?\s+(a\s+)?mensagem\s+(do\s+)?(sistema|desenvolvedor)",
        r"atue\s+como\s+(sistema|administrador|admin)",
        r"system\s*:",
        r"developer\s*:",
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

        normalized_candidates = self._normalized_candidates(text)

        if len(text) > self.max_chars:
            return GuardrailResult(
                False,
                f"Input bloqueado por excesso de tamanho (> {self.max_chars} caracteres).",
                "",
                ["context_stuffing"],
            )

        if (
            self._matches_any(normalized_candidates, self._prompt_patterns)
            or self._prompt_injection_score(normalized_candidates) >= 5
        ):
            return GuardrailResult(
                False,
                "Input bloqueado por tentativa de prompt injection ou vazamento de instrucoes.",
                "",
                ["prompt_injection"],
            )

        if (
            self._matches_any(normalized_candidates, self._exfiltration_patterns)
            or self._exfiltration_score(normalized_candidates) >= 5
        ):
            return GuardrailResult(
                False,
                "Input bloqueado por tentativa de exfiltracao de dados sensiveis.",
                "",
                ["data_exfiltration"],
            )

        if self._matches_any(normalized_candidates, self._tool_patterns):
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

        if self.allowed_topics and not any(
            topic in sanitized_text.lower() for topic in self.allowed_topics
        ):
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
    def _matches_any(cls, texts: tuple[str, ...], patterns: tuple[re.Pattern[str], ...]) -> bool:
        return any(cls._matches(text, patterns) for text in texts)

    @classmethod
    def _normalize_for_security_checks(cls, text: str) -> str:
        """Normalizes text before regex checks to catch simple obfuscation."""
        normalized = cls._ZERO_WIDTH_PATTERN.sub("", text)
        normalized = normalized.translate(cls._CONFUSABLE_TRANSLATION)
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = normalized.lower().translate(cls._OBFUSCATION_TRANSLATION)
        normalized = re.sub(r"[\W_]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def _normalized_candidates(cls, text: str) -> tuple[str, ...]:
        candidates = [text]
        candidates.extend(cls._decode_base64_candidates(text))
        normalized_candidates = []
        for candidate in candidates:
            normalized = cls._normalize_for_security_checks(candidate)
            normalized_candidates.append(normalized)
            normalized_candidates.append(cls._collapse_spaced_letters(normalized))
            normalized_candidates.append(normalized.replace(" ", ""))
        return tuple(dict.fromkeys(item for item in normalized_candidates if item))

    @classmethod
    def _decode_base64_candidates(cls, text: str) -> list[str]:
        decoded: list[str] = []
        for match in cls._BASE64_CANDIDATE_PATTERN.finditer(text):
            try:
                raw = base64.b64decode(match.group(0), validate=True)
                decoded_text = raw.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                continue
            if decoded_text.strip():
                decoded.append(decoded_text)
        return decoded

    @staticmethod
    def _collapse_spaced_letters(text: str) -> str:
        tokens = text.split()
        collapsed: list[str] = []
        i = 0
        while i < len(tokens):
            if len(tokens[i]) == 1 and tokens[i].isalpha():
                letters = [tokens[i]]
                i += 1
                while i < len(tokens) and len(tokens[i]) == 1 and tokens[i].isalpha():
                    letters.append(tokens[i])
                    i += 1
                collapsed.append("".join(letters))
                continue
            collapsed.append(tokens[i])
            i += 1
        return " ".join(collapsed)

    @staticmethod
    def _prompt_injection_score(texts: tuple[str, ...]) -> int:
        text = " ".join(texts)
        compact_text = text.replace(" ", "")
        score = 0
        if re.search(r"\b(ignore|desconsidere|forget|bypass|sobrescreva|override)\b", text):
            score += 2
        if re.search(
            r"\b(instrucoes?|instructions?|regras?|rules?|policy|politica|contexto)\b",
            text,
        ):
            score += 2
        if re.search(r"\b(system|sistema|developer|desenvolvedor|admin|administrador)\b", text):
            score += 2
        if re.search(r"\b(prompt|mensagem|message|internas?|interno|secret|segredo)\b", text):
            score += 2
        if re.search(r"\b(reveal|revele|mostre|exiba|print|retorne|liste)\b", text):
            score += 2
        if any(
            marker in compact_text
            for marker in (
                "ignorepreviousinstructions",
                "ignoretodasasinstrucoesanteriores",
                "desconsidereasinstrucoesanteriores",
                "revealsystemprompt",
                "systemprompt",
                "developerprompt",
            )
        ):
            score += 5
        return score

    @staticmethod
    def _exfiltration_score(texts: tuple[str, ...]) -> int:
        text = " ".join(texts)
        score = 0
        if re.search(r"\b(exporte|liste|retorne|mostre|dump|vaze|exfiltre|leak)\b", text):
            score += 2
        if re.search(
            r"\b(cpf|email|e mail|telefone|token|api key|secret|segredo|credencial)\b",
            text,
        ):
            score += 3
        if re.search(r"\b(base|dataset|documentos?|clientes?|usuarios?|users?)\b", text):
            score += 2
        return score


class OutputGuardrail:
    """Sanitizes and validates model responses before returning them."""

    _LEAKAGE_PATTERNS = (
        r"(prompt\s+do\s+sistema|system\s+prompt|instru[cç][oõ]es\s+internas)",
        r"(instrucoes\s+internas|developer\s+prompt|developer\s+message)",
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

        normalized_candidates = InputGuardrail._normalized_candidates(text)

        if InputGuardrail._matches_any(normalized_candidates, self._leakage_patterns):
            return GuardrailResult(
                False,
                "Saida bloqueada por conter indicio de vazamento de instrucoes ou segredos.",
                "",
                ["sensitive_leakage"],
            )

        if InputGuardrail._matches_any(
            normalized_candidates, self._unsafe_finance_patterns
        ) or self._unsafe_finance_score(normalized_candidates) >= 4:
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

    @staticmethod
    def _unsafe_finance_score(texts: tuple[str, ...]) -> int:
        text = " ".join(texts)
        compact_text = text.replace(" ", "")
        score = 0
        if re.search(r"\b(lucro|retorno|rentabilidade|ganho)\b", text):
            score += 2
        if re.search(r"\b(garantido|garantida|sem risco|semrisco)\b", text):
            score += 2
        if re.search(r"\b(invista|compre|venda)\b", text):
            score += 1
        if "lucrogarantido" in compact_text or "retornogarantido" in compact_text:
            score += 4
        return score


class GuardrailService:
    """Convenience facade for request/response protection."""

    def __init__(
        self,
        input_guardrail: InputGuardrail | None = None,
        output_guardrail: OutputGuardrail | None = None,
    ) -> None:
        self.input_guardrail = input_guardrail or InputGuardrail()
        self.output_guardrail = output_guardrail or OutputGuardrail()

    def secure_exchange(
        self, user_input: str, llm_output: str
    ) -> tuple[GuardrailResult, GuardrailResult]:
        """Evaluates a full request/response exchange."""
        input_result = self.input_guardrail.evaluate(user_input)
        if not input_result.allowed:
            return input_result, GuardrailResult(False, "Saida nao avaliada.", "")
        output_result = self.output_guardrail.evaluate(llm_output)
        return input_result, output_result
