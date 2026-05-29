"""
LLM Service for AI chat functionality
Supports both OpenAI and Ollama backends
"""

import os
import json
from typing import Optional, List, Dict, Any
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

    def _ollama_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Send request to Ollama local LLM"""
        try:
            # Convert to Ollama format
            prompt = "\n".join(
                [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
            )
            prompt += "\nASSISTANT:"

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", "").strip(),
                    "tokens_used": data.get("eval_count", 0),
                    "provider": "ollama",
                }
            else:
                return {
                    "response": f"Ollama error: {response.status_code}",
                    "tokens_used": 0,
                    "provider": "ollama",
                    "error": True,
                }
        except requests.exceptions.ConnectionError:
            return {
                "response": (
                    "Could not connect to Ollama. Make sure it's running at "
                    f"{self.ollama_url}"
                ),
                "tokens_used": 0,
                "provider": "ollama",
                "error": True,
            }
        except Exception as e:
            return {
                "response": f"Error with Ollama: {str(e)}",
                "tokens_used": 0,
                "provider": "ollama",
                "error": True,
            }

    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current LLM provider"""
        return {
            "provider": self.provider,
            "model": "gpt-3.5-turbo" if self.provider == "openai" else self.ollama_model,
            "ollama_url": self.ollama_url if self.provider == "ollama" else None,
        }
