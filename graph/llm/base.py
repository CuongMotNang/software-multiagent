"""Base LLM interface — tất cả provider đều implement class này."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Response wrapper cho LLM call — chứa content + usage metadata."""
    content: Optional[str]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


class BaseLLM(ABC):
    """Abstract base class cho mọi LLM provider (Nvidia, Anthropic, OpenAI...)."""

    @abstractmethod
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> "LLMResponse":
        """Gọi LLM và trả về LLMResponse.
        
        Args:
            system_prompt: System prompt cho model
            user_prompt: User message
            temperature: Độ sáng tạo (0.0 - 1.0)
            max_tokens: Số token tối đa trong response
            
        Returns:
            LLMResponse chứa content + token usage + model info
        """
        ...
