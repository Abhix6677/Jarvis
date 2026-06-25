import requests
from typing import List, Dict
from requests.exceptions import RequestException

from core.config import API_URL, MODEL, CONFIG, get_api_key
from core.logger import get_logger


_client_instance = None


def get_client() -> "GPTClient":
    global _client_instance
    if _client_instance is None:
        _client_instance = GPTClient()
    return _client_instance


class GPTClient:
    def __init__(self):
        self.api_key = get_api_key()
        self.api_url = API_URL
        self.model = MODEL
        self.logger = get_logger("jarvis.api")

    def chat(self, messages: List[Dict[str, str]], temperature: float = None) -> str:
        if temperature is None:
            temperature = CONFIG.chat_temperature

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        last_exception = None

        for attempt in range(CONFIG.api_retries + 1):
            try:
                self.logger.info(f"API request attempt {attempt + 1}")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=CONFIG.api_timeout,
                )

                if response.status_code != 200:
                    body = response.text or ""
                    truncated_body = body[:500]
                    if len(body) > 500:
                        truncated_body += "... [truncated]"
                    raise RuntimeError(
                        f"API Error {response.status_code}: {truncated_body}"
                    )

                data = response.json()

                choices = data.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise RuntimeError(
                        "Invalid API response format: 'choices' missing or empty."
                    )

                first_choice = choices[0]
                if not isinstance(first_choice, dict):
                    raise RuntimeError(
                        "Invalid API response format: 'choices[0]' is malformed."
                    )

                message = first_choice.get("message")
                if not isinstance(message, dict):
                    raise RuntimeError(
                        "Invalid API response format: 'message' missing or malformed."
                    )

                content = message.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError(
                        "Invalid API response format: 'content' missing or empty."
                    )

                from core.response_parser import ResponseParser

                parsed = ResponseParser.extract_text(content)
                if not parsed:
                    raise RuntimeError("Provider returned no user-visible content.")

                return parsed

            except (RequestException, ValueError, RuntimeError) as e:
                self.logger.error(f"API error: {e}")
                last_exception = e

        raise RuntimeError(f"API request failed: {last_exception}")
