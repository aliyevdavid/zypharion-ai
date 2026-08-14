import json
from typing import Any

from pydantic import ValidationError

from app.ai.models import AIIntelligenceResult


class AIResponseValidationError(ValueError):
    """Provider content could not be decoded into page intelligence."""


class PageIntelligenceResponseParser:
    """
    Decode and validate provider output for page intelligence.
    """

    def parse(self, content: str) -> AIIntelligenceResult:
        try:
            response_data = self._normalize(content)
            return AIIntelligenceResult.model_validate(response_data)
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            ValidationError,
        ) as error:
            raise AIResponseValidationError(
                "AI response is not valid page intelligence."
            ) from error

    def _normalize(self, content: str) -> dict[str, Any]:
        """Extract exactly one JSON object from supported provider output."""
        if "```" in content:
            return self._normalize_fenced(content)

        values = self._decode_structured_values(content)
        objects = [value for value in values if isinstance(value, dict)]
        if len(values) != 1 or len(objects) != 1:
            raise ValueError("Response must contain exactly one JSON object.")

        return objects[0]

    def _normalize_fenced(self, content: str) -> dict[str, Any]:
        if content.count("```") != 2:
            raise ValueError("Response contains malformed Markdown fences.")

        opening = content.index("```")
        closing = content.index("```", opening + 3)
        header_end = content.find("\n", opening + 3, closing)
        if header_end == -1:
            raise ValueError("Fenced content must begin on a new line.")

        language = content[opening + 3 : header_end].strip().lower()
        if language not in {"", "json"}:
            raise ValueError("Unsupported Markdown fence language.")

        closing_line_start = content.rfind("\n", header_end, closing) + 1
        if content[closing_line_start:closing].strip():
            raise ValueError("Closing Markdown fence must be on its own line.")

        closing_line_end = content.find("\n", closing + 3)
        if closing_line_end == -1:
            closing_line_end = len(content)
        if content[closing + 3 : closing_line_end].strip():
            raise ValueError("Closing Markdown fence must be on its own line.")

        fenced_content = content[header_end + 1 : closing_line_start]
        response_data = self._decode_complete_value(fenced_content)
        if not isinstance(response_data, dict):
            raise ValueError("Fenced response must contain a JSON object.")

        outside = content[:opening] + content[closing_line_end:]
        if self._decode_structured_values(outside):
            raise ValueError("Response contains multiple structured values.")

        return response_data

    @staticmethod
    def _decode_complete_value(content: str) -> Any:
        decoder = json.JSONDecoder()
        stripped = content.strip()
        value, end = decoder.raw_decode(stripped)
        if stripped[end:].strip():
            raise ValueError("Fenced block contains extra content.")
        return value

    @staticmethod
    def _decode_structured_values(content: str) -> list[Any]:
        """Decode non-overlapping JSON objects or arrays embedded in text."""
        decoder = json.JSONDecoder()
        values: list[Any] = []
        index = 0

        while index < len(content):
            if content[index] not in "{[":
                index += 1
                continue

            try:
                value, end = decoder.raw_decode(content, index)
            except json.JSONDecodeError:
                index += 1
                continue

            values.append(value)
            index = end

        return values
