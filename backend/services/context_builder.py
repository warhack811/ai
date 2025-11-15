"""
services/context_builder.py
---------------------------
Akıllı context builder - Her model için optimize edilmiş context
"""

from typing import Tuple
from schemas.common import ChatMode

def build_smart_context(
    user_message: str,
    mode: ChatMode,
    chat_history: str = "",
    rag_context: str = "",
    complexity: int = 5,
) -> Tuple[str, str]:
    """
    Model için optimize edilmiş context oluştur
    
    Returns:
        (system_prompt, full_prompt)
    """
    
    # Context parçalarını birleştir (sıralama önemli!)
    context_parts = []
    
    # 1. Geçmiş sohbet (varsa, kısa tut)
    if chat_history and chat_history.strip():
        # Son 3 mesajı al (fazla history model şaşırtıyor)
        lines = chat_history.strip().split('\n')
        recent_lines = lines[-6:] if len(lines) > 6 else lines  # 3 mesaj = 6 satır (user+assistant)
        
        context_parts.append("## Önceki Konuşma")
        context_parts.append('\n'.join(recent_lines))
        context_parts.append("")
    
    # 2. RAG context (varsa, kısa tut)
    if rag_context and rag_context.strip():
        # Uzunsa kırp
        max_rag_chars = 1500 if complexity <= 5 else 2500
        rag_text = rag_context.strip()
        if len(rag_text) > max_rag_chars:
            rag_text = rag_text[:max_rag_chars] + "..."
        
        context_parts.append("## İlgili Bilgiler")
        context_parts.append(rag_text)
        context_parts.append("")
    
    # 3. Kullanıcı mesajı
    context_parts.append("## Kullanıcı Sorusu")
    context_parts.append(user_message.strip())
    
    full_context = '\n'.join(context_parts)
    
    # System prompt (şimdilik boş, prompt_templates kullanacak)
    system_prompt = ""
    
    return system_prompt, full_context