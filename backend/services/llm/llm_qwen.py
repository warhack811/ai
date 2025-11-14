"""
services/llm/llm_qwen.py
------------------------
Qwen tabanlı ana sohbet modeli için yardımcı wrapper fonksiyonlar.

- Genel asistan, Türkçe ağırlıklı kullanım
- Ton: doğal, arkadaşça ama gerektiğinde teknik
"""

from __future__ import annotations

from typing import Optional

from schemas.common import ChatMode
from .model_manager import generate_with_model


BASE_SYSTEM_PROMPT_QWEN = """
You are an advanced multilingual AI assistant with a strong focus on Turkish.

Core rules:
- PRIMARY LANGUAGE: If the user writes in Turkish, always respond in natural, fluent Turkish.
- If the user writes in another language, respond in that language unless they explicitly ask otherwise.
- Be helpful, clear, and friendly. Match the user's tone (casual/formal).
- Use step-by-step reasoning internally, but give concise and understandable explanations in the final answer.
- For code questions, clearly separate explanation and code blocks.
- If you don't know something for sure, say that you are not certain instead of hallucinating.
"""


def build_qwen_system_prompt(mode: ChatMode) -> str:
    """
    Mode'a göre Qwen için sistem promptunu biraz özelleştirir.
    """
    base = BASE_SYSTEM_PROMPT_QWEN.strip()

    if mode == ChatMode.RESEARCH:
        extra = """
Additional mode: RESEARCH
- Focus on depth, sources, and careful reasoning.
- If the answer depends on external information, clearly mention assumptions.
- Structure the answer with headings and bullet points when useful.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CREATIVE:
        extra = """
Additional mode: CREATIVE
- Be more imaginative and expressive.
- Use metaphors or examples when they help understanding.
- Still keep the answer logically consistent and not too long.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CODE:
        extra = """
Additional mode: CODE
- Be precise and technical.
- Show complete code snippets inside fenced code blocks (```).
- Explain the reasoning briefly before or after the code.
- Avoid unnecessary extra text around the code.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.TURKISH_TEACHER:
        extra = """
Additional mode: TURKISH TEACHER
- You are a patient Turkish language teacher.
- Explain grammar points clearly and with simple examples.
- If the user makes a mistake, correct it gently and show the correct form.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.FRIEND:
        extra = """
Additional mode: FRIEND
- Speak casually and warmly, like a close friend.
- Show empathy and understanding.
- Keep answers shorter and more conversational.
""".strip()
        return base + "\n\n" + extra

    # NORMAL / TEACHER / others
    return base


async def qwen_generate_reply(
    user_prompt: str,
    mode: ChatMode,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Qwen modeliyle genel sohbet cevabı üretir.
    """
    system_prompt = build_qwen_system_prompt(mode)
    return await generate_with_model(
        model_key="qwen",
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
