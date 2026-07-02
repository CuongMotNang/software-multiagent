"""Base LLM interface — tất cả provider đều implement class này."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    """Abstract base class cho mọi LLM provider (Nvidia, Anthropic, OpenAI...)."""

    @abstractmethod
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """Gọi LLM và trả về text response.
        
        Args:
            system_prompt: System prompt cho model
            user_prompt: User message
            temperature: Độ sáng tạo (0.0 - 1.0)
            max_tokens: Số token tối đa trong response
            
        Returns:
            String response hoặc None nếu lỗi
        """
        ...