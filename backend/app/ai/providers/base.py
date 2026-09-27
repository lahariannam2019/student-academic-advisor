from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    """Abstract base class for conversational LLM providers (Gemini, Anthropic, Grounded Engine)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier for the active LLM provider."""
        pass

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> str:
        """
        Generate a conversational response from the LLM.
        
        Args:
            prompt: Formatted user prompt with grounding context
            system_instruction: System prompt for role definition & behavioral rules
            history: List of recent conversation turns [{'role': 'user'|'assistant', 'content': '...'}]
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials and network configurations are available."""
        pass
