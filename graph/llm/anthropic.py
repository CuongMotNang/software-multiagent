"""Anthropic LLM provider — placeholder, chưa implement."""
from typing import Optional
from graph.llm.base import BaseLLM, LLMResponse


class AnthropicLLM(BaseLLM):
    """Anthropic Claude LLM — chưa implement."""

    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> LLMResponse:
        raise NotImplementedError("AnthropicLLM.call() chưa được implement")
