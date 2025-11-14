"""
services/llm/llm_phi.py
-----------------------
Phi 3.5 Mini (veya benzeri küçük model) için wrapper.

Kullanım alanı:
- Hafif kod yardımı
- Küçük, hızlı cevaplar
- Arka plandaki küçük reasoning işleri

Model ismi config.LLMSettings.phi.name içinde tanımlı.
"""

from __future__ import annotations

from typing import Optional

from schemas.common import ChatMode
from .model_manager import generate_with_model


BASE_SYSTEM_PROMPT_PHI = """
You are a small but capable AI model optimized for:
- code snippets
- short technical answers
- quick clarifications

Rules:
- If the user writes in Turkish, reply in fluent Turkish.
- Keep answers as short and focused as possible.
- For code, use fenced code blocks (```language).
- If a problem is complex, outline the main steps briefly.
"""


def build_phi_system_prompt(mode: ChatMode) -> str:
    """
    Mode'a göre Phi promptunu biraz ayarlar.
    """
    base = BASE_SYSTEM_PROMPT_PHI.strip()

    if mode == ChatMode.CODE:
        extra = """
Additional mode: CODE
- Provide minimal but working code examples.
- Avoid long explanations unless the user asks for more detail.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.RESEARCH:
        extra = """
Additional mode: RESEARCH
- You are still concise, but you may give a bit more detail.
""".strip()
        return base + "\n\n" + extra

    return base


async def phi_generate_reply(
    user_prompt: str,
    mode: ChatMode,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Phi modeliyle cevap üretir.
    """
    system_prompt = build_phi_system_prompt(mode)
    return await generate_with_model(
        model_key="phi",
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
