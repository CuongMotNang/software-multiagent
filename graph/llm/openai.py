"""OpenAI LLM provider — placeholder, chưa implement."""
from graph.llm.base import BaseLLM, LLMResponse


class OpenAILLM(BaseLLM):
    """OpenAI LLM — chưa implement."""

    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> LLMResponse:
        raise NotImplementedError("OpenAILLM.call() chưa được implement")
