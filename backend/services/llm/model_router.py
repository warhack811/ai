"""
services/llm/model_router.py - FAS 1 FIXED
----------------------------
✅ user_message parametresi eklendi
✅ Complexity-based intelligent routing
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
# Intelligent Model Selection
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
    
    logger.debug(f"Query complexity: {complexity}/10")
    
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
# Routed Generate with Complexity
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
    # YENİ PARAMETRELER (FAS 1):
    user_message: str = "",
    context: str = "",
    mode: Optional[ChatMode] = None,
) -> Tuple[str, str]:
    """
    FAS 1: Complexity-based routing with native templates
    
    Returns:
        (answer_text, used_model_key)
    """
    # Mode'u belirle
    if mode is None:
        mode = chat_request.mode
    
    # user_message yoksa request'ten al
    if not user_message:
        user_message = chat_request.message
    
    # context yoksa composed_prompt kullan
    if not context:
        context = composed_prompt
    
    msg = chat_request.message

    # Complexity-based selection
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

    # Generate with native templates
    text = await generate_with_model(
        model_key=model_key,
        prompt=composed_prompt,  # Deprecated (backward compat)
        system_prompt=system_prompt,  # Deprecated (backward compat)
        temperature=temp,
        max_tokens=max_toks,
        # YENİ PARAMETRELER:
        user_message=user_message,
        context=context,
        mode=mode,
    )

    return text, model_key