"""
services/llm/llm_deepseek.py
----------------------------
Derin mantık (reasoning) ve zor sorular için DeepSeek model wrapper'ı.

- Zor mantık soruları
- Ayrıntılı analiz gereken durumlar
- Araştırma modu ile iyi çalışır
"""

from __future__ import annotations

from typing import Optional

from schemas.common import ChatMode
from .model_manager import generate_with_model


BASE_SYSTEM_PROMPT_DEEPSEEK = """
You are a reasoning-focused AI assistant.

Core rules:
- Always think step by step internally before answering.
- The final answer should be clear and structured, not just raw reasoning.
- Use bullet points and numbered lists for complex explanations.
- If there are multiple possibilities, compare them and state which is most likely and why.
- When the user writes in Turkish, answer in natural Turkish.
- For sensitive or uncertain topics, highlight assumptions and limitations.
"""


def build_deepseek_system_prompt(mode: ChatMode) -> str:
    """
    Mode'a göre DeepSeek için sistem promptunu özelleştirir.
    """
    base = BASE_SYSTEM_PROMPT_DEEPSEEK.strip()

    if mode == ChatMode.RESEARCH:
        extra = """
Additional mode: RESEARCH
- Focus strongly on evidence, logic, and clarity.
- Summarize key points at the end in a short bullet list.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CODE:
        extra = """
Additional mode: CODE
- First, analyze the problem step by step in your mind.
- Then provide a clean, working code solution.
- Explain briefly why this approach is correct or efficient.
""".strip()
        return base + "\n\n" + extra

    # Diğer modlar için base yeterli
    return base


async def deepseek_generate_reply(
    user_prompt: str,
    mode: ChatMode,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    DeepSeek modeliyle cevap üretir.
    Özellikle zor mantık, problem çözme ve araştırma gerektiren sorularda tercih edilir.
    """
    system_prompt = build_deepseek_system_prompt(mode)
    return await generate_with_model(
        model_key="deepseek",
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
