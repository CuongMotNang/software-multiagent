"""LLM Provider Factory — tạo provider dựa trên tên."""
from typing import Optional
from graph.llm.base import BaseLLM
from graph.llm.nvidia import NvidiaLLM
from graph.llm.anthropic import AnthropicLLM
from graph.llm.openai import OpenAILLM


_PROVIDERS = {
    "nvidia": NvidiaLLM,
    "anthropic": AnthropicLLM,
    "openai": OpenAILLM,
}


def llm_factory(provider: Optional[str] = None) -> BaseLLM:
    """Tạo LLM provider instance.
    
    Args:
        provider: Tên provider ("nvidia", "anthropic", "openai").
                  Nếu None, đọc từ env var LLM_PROVIDER (mặc định "nvidia").
    
    Returns:
        Instance của provider tương ứng.
    
    Raises:
        ValueError: Nếu provider không được hỗ trợ.
    """
    import os
    if not provider:
        provider = os.getenv("LLM_PROVIDER") or "nvidia"
    
    provider = provider.lower().strip()
    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(
            f"Provider '{provider}' không được hỗ trợ. "
            f"Các provider hiện có: {', '.join(_PROVIDERS.keys())}"
        )
    return cls()