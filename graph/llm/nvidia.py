"""Nvidia NIM provider — implement BaseLLM cho Nvidia GPT API."""
import os
from typing import Optional
import httpx
from dotenv import load_dotenv
from graph.llm.base import BaseLLM

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class NvidiaLLM(BaseLLM):
    """Gọi Nvidia NIM API (OpenAI-compatible)."""

    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.api_base = os.getenv(
            "NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1"
        )
        self.model = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip() if content else None
        except Exception as e:
            print(f"[NvidiaLLM] Error: {e}")
            return None