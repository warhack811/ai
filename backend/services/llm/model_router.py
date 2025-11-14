"""
services/llm/model_router.py
----------------------------
Farklı LLM modelleri arasında seçim yapan yönlendirici katman.

- ChatMode ve mesajın doğasına göre uygun modeli seçer
- Gerekirse force_model ile zorla model seçilebilir (debug / ayar için)
- model_manager.generate_with_model'i kullanarak cevap üretir
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from schemas.common import ChatMode
from schemas.chat import ChatRequest
from .model_manager import (
    LLMModelInfo,
    generate_with_model,
    get_model_info,
    get_primary_model,
    list_all_models,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model Seçim Mantığı
# ---------------------------------------------------------------------------

def decide_model_key_for_mode(
    mode: ChatMode,
    message: str,
) -> str:
    """
    Mod ve mesaj içeriğine göre hangi modelin kullanılacağını belirler.

    Basit ilk versiyon:
    - code          -> phi (varsa) yoksa mistral
    - research      -> deepseek (zor sorular, mantık ağırlıklı)
    - creative      -> qwen
    - turkish_teacher -> qwen
    - friend        -> qwen
    - normal / teacher / diğer -> qwen
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
        # Qwen yoksa en azından primary'yi kullan
        primary = get_primary_model()
        return primary.key if primary else "qwen"

    # Diğer modlar: NORMAL, TEACHER, vs.
    primary = get_primary_model()
    if primary:
        return primary.key

    # Son çare
    return "qwen"


def resolve_model_key(
    mode: ChatMode,
    message: str,
    force_model: Optional[str] = None,
) -> str:
    """
    Eğer force_model belirtilmişse onu kullanır,
    aksi takdirde decide_model_key_for_mode ile seçim yapar.
    """
    if force_model:
        info = get_model_info(force_model)
        if info is None:
            logger.warning("force_model=%s tanımsız, otomatik seçime geçiliyor.", force_model)
        else:
            return force_model

    return decide_model_key_for_mode(mode, message)


# ---------------------------------------------------------------------------
# Yönlendirilmiş Generate
# ---------------------------------------------------------------------------

async def route_and_generate(
    chat_request: ChatRequest,
    composed_prompt: str,
    system_prompt: str,
    *,
    force_model: Optional[str] = None,
    override_temperature: Optional[float] = None,
    override_max_tokens: Optional[int] = None,
) -> Tuple[str, str]:
    """
    ChatRequest + hazır prompt + system prompt alır,
    uygun model key'ini seçer ve generate_with_model çağırır.

    Dönüş:
      (cevap_metni, kullanılan_model_key)
    """
    mode = chat_request.mode
    msg = chat_request.message

    model_key = resolve_model_key(mode, msg, force_model=force_model)
    info: Optional[LLMModelInfo] = get_model_info(model_key)

    # Temperature / max_tokens ayarları:
    temp = override_temperature
    max_toks = override_max_tokens

    if info:
        if temp is None:
            temp = info.default_temperature
        if max_toks is None:
            max_toks = info.default_max_tokens

    logger.debug(
        "Model router seçimi: mode=%s, model=%s, temp=%.2f, max_tokens=%s",
        mode,
        model_key,
        temp if temp is not None else -1,
        max_toks,
    )

    text = await generate_with_model(
        model_key=model_key,
        prompt=composed_prompt,
        system_prompt=system_prompt,
        temperature=temp,
        max_tokens=max_toks,
    )

    return text, model_key
