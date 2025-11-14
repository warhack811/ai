"""
services/llm/llm_mistral.py
---------------------------
Mistral modeli için wrapper.

- Hızlı ve hafif cevaplar
- Basit sorular, kısa açıklamalar, hızlı geri dönüş gereken durumlar
"""

from __future__ import annotations

from typing import Optional

from schemas.common import ChatMode
from .model_manager import generate_with_model


BASE_SYSTEM_PROMPT_MISTRAL = """
You are a fast and concise AI assistant.

Core rules:
- Prioritize speed and brevity while staying correct.
- Answer in Turkish if the user writes in Turkish.
- Use short paragraphs and avoid unnecessary verbosity.
- If more detail is useful, mention that you can expand on request.
"""


def build_mistral_system_prompt(mode: ChatMode) -> str:
    """
    Mode'a göre Mistral sistem promptunu biraz değiştirir.
    """
    base = BASE_SYSTEM_PROMPT_MISTRAL.strip()

    if mode == ChatMode.CREATIVE:
        extra = """
Additional mode: CREATIVE
- You may be a bit more expressive, but still keep answers compact.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CODE:
        extra = """
Additional mode: CODE
- Provide short, focused code snippets.
- Minimal explanation unless the user asks for more detail.
""".strip()
        return base + "\n\n" + extra

    # Diğer modlar için base yeterli
    return base


async def mistral_generate_reply(
    user_prompt: str,
    mode: ChatMode,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Mistral ile hızlı ve kısa cevap üretir.
    """
    system_prompt = build_mistral_system_prompt(mode)
    return await generate_with_model(
        model_key="mistral",
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
