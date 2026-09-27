import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.ai.providers.base import LLMProvider

logger = logging.getLogger("advisor.gemini")


class GeminiProvider(LLMProvider):
    """
    Google Gemini API Provider for the conversational Student Academic Advisor.
    Communicates server-side with Google Generative Language API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return f"google_gemini ({self._model})"

    def is_available(self) -> bool:
        """Check if Gemini API key is configured and non-placeholder."""
        key = (self._api_key or "").strip()
        if not key:
            return False
        if "your-gemini" in key.lower() or "placeholder" in key.lower():
            return False
        return len(key) >= 10

    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured or invalid.")

        # Build contents array with conversation history
        contents = []

        # Add recent conversation turns
        for turn in history[-8:]:
            role = "user" if turn.get("role") == "user" else "model"
            content_text = turn.get("content", "")
            if content_text:
                contents.append({
                    "role": role,
                    "parts": [{"text": content_text}],
                })

        # Add current user prompt (which contains the grounding context + user question)
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}],
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }

        # Candidate models to try in order
        candidate_models = [
            self._model,
            "gemini-2.5-flash",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-pro-latest",
        ]
        seen = set()
        deduped_models = []
        for m in candidate_models:
            if m not in seen:
                seen.add(m)
                deduped_models.append(m)

        last_error = None
        for model_name in deduped_models:
            clean_name = model_name.replace("models/", "")
            url = f"{self._base_url}/{clean_name}:generateContent?key={self._api_key}"
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
                        return "I received your message, but the model generated an empty response. Please ask again."

                    error_data = resp.text
                    logger.warning(f"Gemini API returned status {resp.status_code} for model {clean_name}: {error_data}")
                    last_error = f"HTTP {resp.status_code}: {error_data}"

            except Exception as e:
                logger.warning(f"Attempt for Gemini model {clean_name} failed: {e}")
                last_error = str(e)

        raise RuntimeError(f"Gemini API generation failed: {last_error}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ):
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured or invalid.")

        contents = []
        for turn in history[-8:]:
            role = "user" if turn.get("role") == "user" else "model"
            content_text = turn.get("content", "")
            if content_text:
                contents.append({
                    "role": role,
                    "parts": [{"text": content_text}],
                })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}],
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }

        clean_name = self._model.replace("models/", "")
        url = f"{self._base_url}/{clean_name}:streamGenerateContent?alt=sse&key={self._api_key}"
        
        # We use sync generator here since we're not fully async throughout yet,
        # but httpx handles it nicely. Wait, we should use httpx.Client().stream()
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status_code != 200:
                    response.read()
                    raise RuntimeError(f"Gemini streaming failed {response.status_code}: {response.text}")
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            if "candidates" in chunk_data and chunk_data["candidates"]:
                                parts = chunk_data["candidates"][0].get("content", {}).get("parts", [])
                                if parts and "text" in parts[0]:
                                    yield parts[0]["text"]
                        except json.JSONDecodeError:
                            continue
