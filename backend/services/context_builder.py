"""
services/context_builder.py - FAS 1 VERSION
---------------------------
✅ Optimize edilmiş context building
✅ Minimum overhead
✅ Model-aware sizing
"""

from typing import Tuple
from schemas.common import ChatMode

def build_smart_context(
    user_message: str,
    mode: ChatMode,
    chat_history: str = "",
    rag_context: str = "",
    complexity: int = 5,
    profile_context: str = "",
) -> Tuple[str, str]:
    """
    Model için optimize edilmiş context oluştur
    
    Args:
        user_message: Kullanıcının sorusu
        mode: Chat modu
        chat_history: Önceki sohbet (temiz format)
        rag_context: RAG'den gelen bilgiler
        complexity: Soru zorluk seviyesi (1-10)
        profile_context: Kullanıcı profili özeti
    
    Returns:
        (system_prompt, full_context)
        
    NOT: system_prompt artık kullanılmıyor (native templates'e geçildi)
    """
    
    context_parts = []
    
    # OPTIMAL SIRALAMASI:
    # 1. Profil (varsa, çok kısa)
    # 2. RAG (varsa, orta uzunlukta)
    # 3. History (varsa, kısa)
    # 4. Kullanıcı mesajı (her zaman)
    
    # ------------------------------------------
    # 1. PROFILE CONTEXT (çok kısa, max 300 char)
    # ------------------------------------------
    if profile_context and profile_context.strip():
        profile_text = profile_context.strip()
        if len(profile_text) > 300:
            profile_text = profile_text[:297] + "..."
        
        context_parts.append(profile_text)
        context_parts.append("")  # Boş satır
    
    # ------------------------------------------
    # 2. RAG CONTEXT (orta uzunlukta, complexity'ye göre)
    # ------------------------------------------
    if rag_context and rag_context.strip():
        # Complexity'ye göre max uzunluk belirle
        if complexity <= 3:
            max_rag_chars = 800  # Basit sorular için az bilgi
        elif complexity <= 6:
            max_rag_chars = 1500  # Orta sorular
        elif complexity <= 8:
            max_rag_chars = 2500  # Karmaşık sorular
        else:
            max_rag_chars = 3500  # Çok karmaşık (DeepSeek için)
        
        rag_text = rag_context.strip()
        if len(rag_text) > max_rag_chars:
            rag_text = rag_text[:max_rag_chars - 3] + "..."
        
        context_parts.append("İlgili Bilgiler:")
        context_parts.append(rag_text)
        context_parts.append("")  # Boş satır
    
    # ------------------------------------------
    # 3. CHAT HISTORY (kısa, max 4000 char)
    # ------------------------------------------
    if chat_history and chat_history.strip():
        history_text = chat_history.strip()
        
        # History'yi kırp (max 4000 karakter - memory.py ile eşleşik)
        max_history_chars = 4000
        if len(history_text) > max_history_chars:
            # Son kısmı al (en yeni mesajlar)
            history_text = "...\n\n" + history_text[-max_history_chars:]
        
        context_parts.append("Önceki Konuşma:")
        context_parts.append(history_text)
        context_parts.append("")  # Boş satır
    
    # ------------------------------------------
    # 4. USER MESSAGE (her zaman)
    # ------------------------------------------
    context_parts.append("Soru:")
    context_parts.append(user_message.strip())
    
    # Birleştir
    full_context = '\n'.join(context_parts)
    
    # TOTAL CONTEXT SIZE CHECK
    # Complexity'ye göre max total size (2x artırıldı)
    if complexity <= 3:
        max_total = 3000  # Phi için minimal (1500 → 3000)
    elif complexity <= 6:
        max_total = 5000  # Mistral için orta (2500 → 5000)
    elif complexity <= 8:
        max_total = 8000  # Qwen için geniş (4000 → 8000)
    else:
        max_total = 12000  # DeepSeek için çok geniş (6000 → 12000)
    
    if len(full_context) > max_total:
        # İlk önce history'yi kısalt
        if chat_history:
            # History'yi tamamen çıkar
            context_parts_no_history = [p for p in context_parts if "Önceki Konuşma:" not in p and p != history_text]
            full_context = '\n'.join(context_parts_no_history)
        
        # Hala çok uzunsa RAG'i kısalt
        if len(full_context) > max_total and rag_context:
            # RAG'i yarıya indir
            shortened_rag = rag_context[:len(rag_context)//2] + "..."
            full_context = full_context.replace(rag_context, shortened_rag)
    
    # system_prompt artık kullanılmıyor (backward compatibility için boş dönüyor)
    system_prompt = ""
    
    return system_prompt, full_context


# ---------------------------------------------------------------------------
# UTILITY: Context Statistics
# ---------------------------------------------------------------------------

def get_context_stats(context: str) -> dict:
    """
    Context istatistiklerini döndür (debug/monitoring için)
    """
    return {
        "total_chars": len(context),
        "total_lines": context.count('\n') + 1,
        "estimated_tokens": len(context.split()) * 1.3,  # Rough estimate
    }