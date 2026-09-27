import logging
from app.ai.providers.base import LLMProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.grounded_fallback import GroundedFallbackProvider

logger = logging.getLogger("advisor.factory")


def get_llm_provider() -> LLMProvider:
    """
    Factory function returning the active LLM provider.
    Priority:
    1. Google Gemini (Preferred active provider via GEMINI_API_KEY)
    2. Anthropic Claude (Optional secondary provider via ANTHROPIC_API_KEY)
    3. Grounded Deterministic Conversational Engine (Zero-dependency fallback)
    """
    gemini = GeminiProvider()
    if gemini.is_available():
        return gemini

    anthropic = AnthropicProvider()
    if anthropic.is_available():
        return anthropic

    logger.info("No active external LLM API key detected; using GroundedFallbackProvider.")
    return GroundedFallbackProvider()
