"""Base LLM interface — tất cả provider đều implement class này."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Kết quả 1 lần gọi LLM, kèm usage để tracking token/chi phí.

    content=None nghĩa là lệnh gọi thất bại (network error, API error...).
    Các provider PHẢI luôn trả về LLMResponse (không được trả None trực
    tiếp), để nơi gọi biết được model đã cố dùng dù có lỗi hay không.
    """
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
    ) -> LLMResponse:
        """Gọi LLM và trả về LLMResponse (content + usage + model).

        Args:
            system_prompt: System prompt cho model
            user_prompt: User message
            temperature: Độ sáng tạo (0.0 - 1.0)
            max_tokens: Số token tối đa trong response

        Returns:
            LLMResponse — content=None nếu lỗi.
        """
        ...