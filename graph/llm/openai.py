"""OpenAI provider — placeholder, sẽ implement sau."""
from typing import Optional
from graph.llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """Gọi OpenAI API (GPT-4, GPT-4o...).
    
    TODO: Implement khi cần.
    """

    def __init__(self):
        raise NotImplementedError(
            "OpenAI provider chưa được implement. "
            "Cài đặt: pip install openai, "
            "thêm OPENAI_API_KEY vào .env"
        )

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        raise NotImplementedError("OpenAILLM.call() chưa được implement")