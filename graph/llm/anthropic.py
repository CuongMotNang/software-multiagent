"""Anthropic Claude provider — placeholder, sẽ implement sau."""
from typing import Optional
from graph.llm.base import BaseLLM


class AnthropicLLM(BaseLLM):
    """Gọi Anthropic Claude API.
    
    TODO: Implement khi có Claude API key.
    """

    def __init__(self):
        raise NotImplementedError(
            "Anthropic provider chưa được implement. "
            "Cài đặt: pip install anthropic, "
            "thêm ANTHROPIC_API_KEY vào .env"
        )

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        raise NotImplementedError("AnthropicLLM.call() chưa được implement")