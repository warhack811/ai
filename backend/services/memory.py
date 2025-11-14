"""
services/memory.py
------------------
Kısa vadeli (session context) ve uzun vadeli (profil / önemli anılar)
hafıza katmanı.

Bu modül:
- Short-term: Son N mesajı güzel formatlanmış bir history metnine çevirir.
- Long-term: Profil + önemli mesajlardan özet oluşturur.
- Post-interaction: Profil/notes tarafını zenginleştirmek için profile_service'e delege eder.
"""

from __future__ import annotations

from typing import List

from config import get_settings
from schemas.common import ChatMessage, Role
from services import profile_service

settings = get_settings()


# ---------------------------------------------------------------------------
# Short-Term Memory (chat history)
# ---------------------------------------------------------------------------

def build_short_term_history_text(
    user_id: str,
    session_id: str,
    messages: List[ChatMessage],
) -> str:
    """
    Son N mesajı model için uygun bir sohbet transkriptine çevirir.

    Örnek format:
      [USER] ...
      [ASSISTANT] ...
    """
    if not messages:
        return ""

    lines: list[str] = []

    for msg in messages:
        prefix = "[USER]" if msg.role == Role.USER else "[ASSISTANT]" if msg.role == Role.ASSISTANT else "[SYSTEM]"
        lines.append(f"{prefix} {msg.content.strip()}")

    history_text = "\n".join(lines)
    # Aşırı uzunsa biraz kırpabiliriz
    max_chars = 4000
    if len(history_text) > max_chars:
        history_text = history_text[-max_chars:]

    return history_text


# ---------------------------------------------------------------------------
# Long-Term Memory / Profile Context
# ---------------------------------------------------------------------------

def build_long_term_context_text(
    user_id: str,
    session_id: str,
    last_message: ChatMessage,
) -> str:
    """
    Uzun vadeli hafıza:
    - Kullanıcı profili özeti
    - Kullanıcı hakkında önemli notlar
    - Hedefler vs.

    Şimdilik profile_service.get_profile_summary ile çalışıyoruz.
    """
    profile_summary = profile_service.get_profile_summary(user_id)

    if not profile_summary:
        return ""

    text = f"KULLANICI PROFİL ÖZETİ:\n{profile_summary.strip()}"
    return text


# ---------------------------------------------------------------------------
# Post-Interaction Hook
# ---------------------------------------------------------------------------

def handle_post_interaction(
    user_id: str,
    session_id: str,
    user_message: ChatMessage,
    assistant_message: ChatMessage,
) -> None:
    """
    Mesajlar DB'ye kaydedildikten sonra çağrılır.

    Burada:
    - Profil notlarını zenginleştirme
    - Önemli görülen bilgileri profile_service'e delege etme
    gibi işlemleri yapar.
    """
    # Şimdilik memory tarafında ek DB tablosu tutmuyoruz,
    # profil notları üzerinden uzun vadeli hafızayı yönetiyoruz.
    try:
        profile_service.maybe_enrich_profile_notes(
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )
    except Exception:
        # Sessizce yutuyoruz; pipeline zaten logluyor.
        pass
