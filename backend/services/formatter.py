"""
services/formatter.py
---------------------
LLM tarafından üretilen cevabı, mod / state / niyet / duyguya göre
daha uygun bir konuşma stiline dönüştüren katman.

Bu, final cevabın %100 insansı ve senin istediğin kaliteye yakın çıkmasını sağlar.
"""

from __future__ import annotations

from typing import List, Optional

from schemas.common import SourceInfo, ChatMode
from services.dialogue_state import DialogueState


# ----------------------------------------------------------
# Temel formatlar (cevap stilini belirleyen fonksiyonlar)
# ----------------------------------------------------------

def _format_sources(sources: List[SourceInfo]) -> str:
    if not sources:
        return ""

    lines = ["\n\n### 📚 Kaynaklar:\n"]
    for s in sources:
        title = s.title or "Bilinmeyen"
        url = s.url or ""
        if url:
            lines.append(f"- [{title}]({url})")
        else:
            lines.append(f"- {title}")
    return "\n".join(lines)


def _format_emotional_support(text: str, state: DialogueState) -> str:
    """
    Üzgün / yalnız / stresli durumlar için yumuşak, destekleyici tarz.
    """
    prefix = "💛 Sana destek olmak için buradayım.\n\n"
    return prefix + text


def _format_code(text: str, state: DialogueState) -> str:
    """
    Kod modunda daha teknik, düzenli bir format.
    """
    return f"💻 **Kod Yardımı**\n\n{text}"


def _format_research(text: str, state: DialogueState) -> str:
    """
    Araştırma modunda hafif akademik ama düzgün bir format.
    """
    return f"🔍 **Araştırma Sonuçları**\n\n{text}"


def _format_casual(text: str, state: DialogueState) -> str:
    """
    Normal sohbet formatı.
    """
    return text


def _format_default(text: str, state: DialogueState) -> str:
    return text


# Haritalama
MODE_FORMATTERS = {
    "emotional_support": _format_emotional_support,
    "code_help": _format_code,
    "research": _format_research,
    "casual_chat": _format_casual,
    "general_chat": _format_default,
    "document_question": _format_research,
    "reminder": _format_default,
    "profile_related": _format_default,
    "unknown": _format_default,
}


# ----------------------------------------------------------
# Ana Formatter: pipeline sonunda uygulanır
# ----------------------------------------------------------

def format_final_answer(
    answer_text: str,
    state: DialogueState,
    sources: Optional[List[SourceInfo]] = None,
) -> str:
    """
    LLM cevabını, uygun konuşma stiline dönüştürür.
    """
    formatter = MODE_FORMATTERS.get(state.state_name, _format_default)
    processed = formatter(answer_text, state)

    if sources:
        processed += _format_sources(sources)

    return processed
