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

                # Provider-aware parsing
                # Expected OpenAI-style schema:
                # { "choices": [ { "message": { "role": "assistant", "content": ... , ... } } ] }

                choices = data.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise RuntimeError("Invalid API response: missing choices.")

                first_choice = choices[0]
                if not isinstance(first_choice, dict):
                    raise RuntimeError("Invalid API response: malformed choice object.")

                message = first_choice.get("message")
                if not isinstance(message, dict):
                    raise RuntimeError("Invalid API response: missing assistant message.")

                if message.get("role") != "assistant":
                    raise RuntimeError("Invalid API response: expected assistant role.")

                # Handle string content
                content = message.get("content")

                # Case 1: content is simple string
                if isinstance(content, str) and content.strip():
                    return content.strip()

                # Case 2: content is structured blocks (list)
                if isinstance(content, list):
                    text_blocks = []
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "text":
                            text_value = block.get("text")
                            if isinstance(text_value, str) and text_value.strip():
                                text_blocks.append(text_value.strip())
                    if text_blocks:
                        return "\n".join(text_blocks).strip()

                raise RuntimeError("Provider returned no user-visible assistant text.")

            except (RequestException, ValueError, RuntimeError) as e:
                self.logger.error(f"API error: {e}")
                last_exception = e

        raise RuntimeError(f"API request failed: {last_exception}")
