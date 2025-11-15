"""
services/llm/model_router.py - DAY 2 VERSION
----------------------------
Complexity-based intelligent model routing
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from schemas.common import ChatMode, IntentLabel
from schemas.chat import ChatRequest
from .complexity_scorer import ComplexityScorer
from .model_manager import (
    LLMModelInfo,
    generate_with_model,
    get_model_info,
    get_primary_model,
    list_all_models,
)

logger = logging.getLogger(__name__)

# Global complexity scorer
_complexity_scorer = ComplexityScorer()


# ---------------------------------------------------------------------------
# NEW: Intelligent Model Selection
# ---------------------------------------------------------------------------

def select_model_by_complexity(
    query: str,
    mode: ChatMode,
    intent: Optional[IntentLabel] = None,
    force_model: Optional[str] = None,
) -> Tuple[str, int]:
    """
    Complexity-based model selection
    
    Returns:
        (model_key, complexity_score)
    """
    # Force model varsa direkt kullan
    if force_model:
        info = get_model_info(force_model)
        if info:
            return force_model, 5  # Default complexity
        logger.warning(f"Force model {force_model} bulunamadı, otomatik seçim yapılıyor")
    
    # Complexity skorla
    complexity = _complexity_scorer.score(query, mode, intent)
    
    logger.info(f"Query complexity: {complexity}/10 - {_complexity_scorer.explain_score(complexity)}")
    
    # Model seç
    all_models = list_all_models()
    
    if complexity <= 3:
        # Basit sorular - Phi
        if "phi" in all_models:
            return "phi", complexity
        elif "mistral" in all_models:
            return "mistral", complexity
        else:
            return "qwen", complexity
    
    elif complexity <= 6:
        # Orta sorular - Mistral
        if "mistral" in all_models:
            return "mistral", complexity
        elif "phi" in all_models:
            return "phi", complexity
        else:
            return "qwen", complexity
    
    elif complexity <= 8:
        # Karmaşık sorular - Qwen
        if "qwen" in all_models:
            return "qwen", complexity
        elif "mistral" in all_models:
            return "mistral", complexity
        else:
            primary = get_primary_model()
            return primary.key if primary else "qwen", complexity
    
    else:
        # Çok karmaşık - DeepSeek (reasoning)
        if "deepseek" in all_models:
            return "deepseek", complexity
        elif "qwen" in all_models:
            return "qwen", complexity
        else:
            primary = get_primary_model()
            return primary.key if primary else "qwen", complexity


# ---------------------------------------------------------------------------
# OLD: Kept for backward compatibility
# ---------------------------------------------------------------------------

def decide_model_key_for_mode(
    mode: ChatMode,
    message: str,
) -> str:
    """
    DEPRECATED: Use select_model_by_complexity instead
    Kept for backward compatibility
    """
    all_models = list_all_models()

    def has_model(key: str) -> bool:
        return key in all_models

    if mode == ChatMode.CODE:
        if has_model("phi"):
            return "phi"
        if has_model("mistral"):
            return "mistral"
        return "qwen"

    if mode == ChatMode.RESEARCH:
        if has_model("deepseek"):
            return "deepseek"
        return "qwen"

    if mode in (ChatMode.CREATIVE, ChatMode.FRIEND, ChatMode.TURKISH_TEACHER):
        if has_model("qwen"):
            return "qwen"
        primary = get_primary_model()
        return primary.key if primary else "qwen"

    primary = get_primary_model()
    if primary:
        return primary.key

    return "qwen"


def resolve_model_key(
    mode: ChatMode,
    message: str,
    force_model: Optional[str] = None,
) -> str:
    """
    DEPRECATED: Use select_model_by_complexity instead
    """
    if force_model:
        info = get_model_info(force_model)
        if info is None:
            logger.warning("force_model=%s tanımsız, otomatik seçime geçiliyor.", force_model)
        else:
            return force_model

    return decide_model_key_for_mode(mode, message)


# ---------------------------------------------------------------------------
# NEW: Routed Generate with Complexity
# ---------------------------------------------------------------------------

async def route_and_generate(
    chat_request: ChatRequest,
    composed_prompt: str,
    system_prompt: str,
    *,
    force_model: Optional[str] = None,
    override_temperature: Optional[float] = None,
    override_max_tokens: Optional[int] = None,
    intent: Optional[IntentLabel] = None,
) -> Tuple[str, str]:
    """
    UPGRADED: Complexity-based routing
    
    Returns:
        (answer_text, used_model_key)
    """
    mode = chat_request.mode
    msg = chat_request.message

    # NEW: Complexity-based selection
    model_key, complexity = select_model_by_complexity(
        query=msg,
        mode=mode,
        intent=intent,
        force_model=force_model,
    )
    
    info: Optional[LLMModelInfo] = get_model_info(model_key)

    # Temperature / max_tokens
    temp = override_temperature
    max_toks = override_max_tokens

    if info:
        if temp is None:
            temp = info.default_temperature
        if max_toks is None:
            max_toks = info.default_max_tokens

    logger.info(
        "🎯 Routed to: %s (complexity=%d/10) | temp=%.2f, max_tokens=%s",
        model_key.upper(),
        complexity,
        temp if temp is not None else -1,
        max_toks,
    )

    # Generate
    text = await generate_with_model(
        model_key=model_key,
        prompt=composed_prompt,
        system_prompt=system_prompt,
        temperature=temp,
        max_tokens=max_toks,
        user_message=msg,
        context=composed_prompt,
        mode=mode,
    )

    return text, model_key