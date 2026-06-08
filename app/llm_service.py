"""
LLM Service for AI chat functionality
Supports both OpenAI and Ollama backends
"""

import os
from typing import List, Dict, Any
import requests
from django.conf import settings


class LLMService:
    """Service to interact with LLM providers"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", None)
        self.ollama_url = settings.OLLAMA_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.provider = "openai" if self.api_key else "ollama"

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM based on conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Dict with 'response' and 'tokens_used'
        """
        if self.provider == "openai":
            return self._openai_request(messages, temperature, max_tokens)
        else:
            return self._ollama_request(messages, temperature, max_tokens)

    def _openai_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Send request to OpenAI API"""
        try:
            import openai

            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "provider": "openai",
            }
        except Exception as e:
            return {
                "response": f"Error with OpenAI: {str(e)}",
                "tokens_used": 0,
                "provider": "openai",
                "error": True,
            }

    def _pull_model(self) -> bool:
        """Pull the configured model into Ollama (blocks up to 10 min)."""
        try:
            r = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": self.ollama_model, "stream": False},
                timeout=600,
            )
            return r.status_code == 200
        except Exception:
            return False

    def model_is_available(self) -> bool:
        """Return True if the model is already present in Ollama."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if r.status_code != 200:
                return False
            models = [m.get("name", "") for m in r.json().get("models", [])]
            return any(self.ollama_model in m for m in models)
        except Exception:
            return False

    def _ollama_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Send request to Ollama. Auto-pulls the model if it is missing (404)."""
        try:
            prompt = "\n".join(
                [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
            )
            prompt += "\nASSISTANT:"

            def _post():
                return requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": False,
                    },
                    timeout=120,
                )

            response = _post()

            # Model not pulled yet — download it then retry
            if response.status_code == 404:
                if not self._pull_model():
                    return {
                        "response": (
                            f"AI model '{self.ollama_model}' is not installed.\n"
                            "Run this command to install it:\n\n"
                            f"  docker exec webapp-ollama ollama pull {self.ollama_model}"
                        ),
                        "tokens_used": 0,
                        "provider": "ollama",
                        "error": True,
                    }
                response = _post()

            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", "").strip(),
                    "tokens_used": data.get("eval_count", 0),
                    "provider": "ollama",
                }
            return {
                "response": f"Ollama returned HTTP {response.status_code}.",
                "tokens_used": 0,
                "provider": "ollama",
                "error": True,
            }
        except requests.exceptions.ConnectionError:
            return {
                "response": f"Cannot reach Ollama at {self.ollama_url}. Is the container running?",
                "tokens_used": 0,
                "provider": "ollama",
                "error": True,
            }
        except Exception as e:
            return {
                "response": f"Ollama error: {str(e)}",
                "tokens_used": 0,
                "provider": "ollama",
                "error": True,
            }

    def get_provider_info(self) -> Dict[str, str]:
        """Return provider info including whether the model is ready."""
        available = self.model_is_available() if self.provider == "ollama" else True
        return {
            "provider": self.provider,
            "model": (
                "gpt-3.5-turbo" if self.provider == "openai" else self.ollama_model
            ),
            "ollama_url": self.ollama_url if self.provider == "ollama" else None,
            "available": available,
            "pull_cmd": (
                f"docker exec webapp-ollama ollama pull {self.ollama_model}"
                if not available
                else None
            ),
        }
