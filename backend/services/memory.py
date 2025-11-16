"""
services/memory.py - FAS 1 VERSION
------------------
✅ Meta tag'siz temiz history
✅ Kontaminasyon engelleme
✅ Optimal context length
"""

from __future__ import annotations

from typing import List

from config import get_settings
from schemas.common import ChatMessage, Role
from services import profile_service

settings = get_settings()


# ---------------------------------------------------------------------------
# Short-Term Memory (chat history) - FIXED
# ---------------------------------------------------------------------------

def build_short_term_history_text(
    user_id: str,
    session_id: str,
    messages: List[ChatMessage],
    max_exchanges: int = 15,  # Son 15 soru-cevap çifti (30 mesaj)
) -> str:
    """
    Son N mesajı model için TEMIZ bir formata çevirir.
    
    ❌ ESKİ (HATALI):
    [USER] Merhaba
    [ASSISTANT] Selam
    
    ✅ YENİ (DOĞRU):
    Kullanıcı: Merhaba
    Asistan: Selam
    
    NOT: Meta tag'ler KESINLIKLE kullanılmıyor!
    """
    if not messages:
        return ""

    lines: list[str] = []
    
    # Sadece son N exchange'i al
    max_messages = max_exchanges * 2  # Her exchange = 1 user + 1 assistant
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

    for msg in recent_messages:
        # Temiz, doğal etiketler kullan
        if msg.role == Role.USER:
            role_label = "Kullanıcı"
        elif msg.role == Role.ASSISTANT:
            role_label = "Asistan"
        else:
            role_label = "Sistem"
        
        # Basit, temiz format
        content = msg.content.strip()
        
        # Çok uzunsa kırp (tek mesaj max 500 karakter)
        if len(content) > 500:
            content = content[:497] + "..."
        
        lines.append(f"{role_label}: {content}")

    # Birleştir
    history_text = "\n\n".join(lines)
    
    # Total history max 4000 karakter (2000 → 4000)
    max_total_chars = 4000
    if len(history_text) > max_total_chars:
        # Sondan başlayarak kırp (en yeni mesajlar kalır)
        history_text = "...\n\n" + history_text[-max_total_chars:]

    return history_text


# ---------------------------------------------------------------------------
# Long-Term Memory / Profile Context - FIXED
# ---------------------------------------------------------------------------

def build_long_term_context_text(
    user_id: str,
    session_id: str,
    last_message: ChatMessage,
) -> str:
    """
    Uzun vadeli hafıza:
    - Kullanıcı profili özeti
    - Önemli notlar
    
    NOT: Çok uzun olmamalı (max 500 karakter)
    """
    try:
        profile_summary = profile_service.get_profile_summary(user_id)
    except Exception as e:
        # Hata durumunda boş döndür
        return ""

    if not profile_summary or len(profile_summary.strip()) == 0:
        return ""

    # Kısa ve öz tut
    summary = profile_summary.strip()
    if len(summary) > 500:
        summary = summary[:497] + "..."
    
    text = f"[Kullanıcı Profili]\n{summary}"
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
    
    Profil notlarını zenginleştirme işlemini yapar.
    """
    try:
        profile_service.maybe_enrich_profile_notes(
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )
    except Exception:
        # Sessizce yut, pipeline zaten logluyor
        pass


# ---------------------------------------------------------------------------
# UTILITY: Clean message content
# ---------------------------------------------------------------------------

def clean_message_content(content: str) -> str:
    """
    Mesaj içeriğindeki meta tag'leri temizle
    
    Bu fonksiyon DB'ye kaydetmeden önce çağrılabilir
    """
    import re
    
    # Meta tag'leri kaldır
    patterns = [
        r'\[/?USER\]',
        r'\[/?ASSISTANT\]',
        r'\[/?INST\]',
        r'\[/?SYSTEM\]',
        r'<\|im_start\|>.*?<\|im_end\|>',
        r'<\|.*?\|>',
        r'###\s*(?:User|Assistant|System):',
    ]
    
    cleaned = content
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Fazla boşlukları temizle
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned