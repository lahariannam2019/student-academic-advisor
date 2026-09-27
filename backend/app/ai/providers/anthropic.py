import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.ai.providers.base import LLMProvider

logger = logging.getLogger("advisor.anthropic")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Provider for conversational academic guidance."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._model = "claude-3-5-sonnet-20241022"

    @property
    def provider_name(self) -> str:
        return f"anthropic_claude ({self._model})"

    def is_available(self) -> bool:
        key = (self._api_key or "").strip()
        if not key:
            return False
        if "your-anthropic" in key.lower() or "placeholder" in key.lower():
            return False
        return key.startswith("sk-ant")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Anthropic API key is not configured or invalid.")

        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)

        messages = []
        for turn in history[-6:]:
            role = turn.get("role")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": turn.get("content", "")})

        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_instruction,
            messages=messages,
        )

        return response.content[0].text.strip()
