"""
services.llm package
--------------------
LLM katmanındaki yardımcı fonksiyonları dışa açar.
"""

from .model_manager import (
    LLMModelInfo,
    get_model_info,
    get_primary_model,
    list_all_models,
    generate_with_model,
    test_llm_health,
)
from .model_router import route_and_generate
from .llm_qwen import qwen_generate_reply
from .llm_deepseek import deepseek_generate_reply
from .llm_mistral import mistral_generate_reply
from .llm_phi import phi_generate_reply

__all__ = [
    "LLMModelInfo",
    "get_model_info",
    "get_primary_model",
    "list_all_models",
    "generate_with_model",
    "test_llm_health",
    "route_and_generate",
    "qwen_generate_reply",
    "deepseek_generate_reply",
    "mistral_generate_reply",
    "phi_generate_reply",
]
