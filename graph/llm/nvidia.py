"""NVIDIA LLM provider — gọi API NVIDIA NIM (OpenAI-compatible endpoint)."""
import os
import time
import requests

from graph.llm.base import BaseLLM, LLMResponse


class NvidiaLLM(BaseLLM):
    """NVIDIA NIM LLM — tương thích OpenAI API format."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", os.getenv("NIM_API_KEY", ""))
        default_url = "https://integrate.api.nvidia.com/v1"
        self.base_url = (base_url or os.getenv("NVIDIA_BASE_URL", default_url)).rstrip("/")
        self.model = model or os.getenv("NVIDIA_MODEL", os.getenv("NIM_MODEL", "nvidia/nemotron-4-340b-instruct"))

    def call(self, system_prompt, user_prompt, temperature=0.2, max_tokens=4096) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            content = content.strip() if content else None

            # Lấy usage từ response
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                model=self.model,
            )

        except Exception as e:
            print(f"❌ Error calling NVIDIA API: {e}")
            return LLMResponse(content=None, model=self.model)
