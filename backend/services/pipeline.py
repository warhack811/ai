"""
services/pipeline.py
--------------------
Ana sohbet akışı (pipeline):

1. ChatRequest al
2. Intent & duygu analizi yap
3. Kullanıcı mesajını DB'ye kaydet
4. Kısa vadeli sohbet geçmişini ve uzun vadeli hafızayı hazırla
5. Doküman + web araması (RAG) bağlamını topla
6. LLM için son prompt'u oluştur
7. Uygun modeli seç ve cevap üret
8. Gerekirse self-correction ve safety filtreden geçir
9. Asistan cevabını DB'ye kaydet
10. Mood / profil / reflection / reminder gibi yan etkileri çalıştır
11. ChatResponse döndür
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple
import re  # dosyanın en üstünde varsa tekrar ekleme, yoksa ekle
from config import get_settings
from schemas.chat import ChatRequest, ChatResponse
from schemas.common import (
    ChatMode,
    ChatSourceAnnotatedMessage,
    ChatMessage,
    MessageMetadata,
    Role,
    SourceInfo,
    IntentLabel,
    SafetyLevel,
)
from schemas.profile import MoodLog
from services import chat_db
from services.intent_detector import detect_intent
from services.emotion_detector import analyze_emotion
from services.llm.model_router import route_and_generate

# Bu modüller henüz yazılmadı ama pipeline API'si şimdiden net olsun:
from services import memory
from services import rag_engine
from services import self_correction
from services import safety_filter
from services import profile_service
from services import reflection_engine
from services import reminders_service

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Yardımcı: Sistem Prompt ve Final Prompt Kompozisyonu
# ---------------------------------------------------------------------------

def _build_global_system_prompt(mode: ChatMode) -> str:
    """
    Tüm modeller için ortak, üst seviye sistem prompt'u.
    Türkçe odaklı asistan davranışını burada tanımlar.
    """
    base = """
    You are a PERSONAL AI ASSISTANT whose DEFAULT LANGUAGE IS TURKISH (Türkçe).

    LANGUAGE RULES (VERY IMPORTANT):
    - If the user writes in Turkish, you MUST answer in natural, fluent Turkish.
    - If the user writes in another language BUT DOES NOT EXPLICITLY ASK for that language,
      you STILL answer in Turkish and only translate or quote short phrases if needed.
    - Only answer in English (or another language) if the user CLEARLY asks:
      e.g. "answer in English", "please respond in German", etc.
    - Even when using web search or documents in English, you must EXPLAIN them in Turkish.

    GENERAL RULES:
    - Do NOT include meta comments like "User can continue the conversation in Turkish."
      or "Let's continue the conversation in Turkish." Speak directly to the user.
    - Do NOT include training-style tags like [USER], [ASSISTANT], [INST], unless
      the user explicitly asks for that format. Just give a normal assistant answer.
    - Be honest. If you are not sure about something, say that you are not certain.
    - Prefer concise, clear explanations. Use bullet points and examples when helpful.
    - Avoid hallucinating facts, especially for dates, numbers, or specific names.
    - For code, use fenced code blocks (```language).
    - For emotional topics, be empathetic and respectful.
    - You may use any provided context (chat history, documents, web results, memories).
      Do not mention internal implementation details.
    - Cevaplarında gerektiğinde nazik ve abartısız emoji kullanabilirsin (😊, 👍 gibi), ama aşırıya kaçma.
    """.strip()

    if mode == ChatMode.RESEARCH:
        extra = """
Mode: RESEARCH
- Focus on depth, structure, and clarity.
- If there is conflicting information, explain the conflict.
- Summarize key points at the end.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CREATIVE:
        extra = """
Mode: CREATIVE
- You may be more expressive and imaginative, but stay coherent and helpful.
- Stories, analogies, and metaphors are allowed when they help.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.CODE:
        extra = """
Mode: CODE
- Be precise and technical.
- Provide complete, working code snippets when reasonable.
- Include short explanation of the approach.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.FRIEND:
        extra = """
Mode: FRIEND
- Speak casually and warmly, like a close, supportive friend.
- Show empathy, especially when the user shares feelings or problems.
- Keep answers a bit shorter and more conversational.
""".strip()
        return base + "\n\n" + extra

    if mode == ChatMode.TURKISH_TEACHER:
        extra = """
Mode: TURKISH TEACHER
- You are a patient Turkish language teacher.
- Explain grammar and vocabulary with simple examples.
- When the user makes mistakes, gently correct them and show the right form.
""".strip()
        return base + "\n\n" + extra

    return base
def clean_model_output(text: str) -> str:
    """
    Modelin cevabından gereksiz meta kısımları temizler:
    - 'User can continue the conversation in Turkish.'
    - 'Let's continue the conversation in Turkish.'
    - [USER], [ASSISTANT], [INST] gibi eğitim tag'leri
    """

    if not text:
        return text

    # 1) Sık çıkan meta cümleleri direkt sil
    patterns_to_remove = [
        r"\[User can continue the conversation in Turkish\.\]",
        r"User can continue the conversation in Turkish\.",
        r"Let'?s continue the conversation in Turkish\.",
    ]

    cleaned = text
    for pat in patterns_to_remove:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # 2) Başta/sonda kalan eğitim tag'lerini temizle
    # Örn: [USER] ... , [ASSISTANT] ...
    cleaned = re.sub(r"\[USER\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[ASSISTANT\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[INST\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[/INST\]", "", cleaned, flags=re.IGNORECASE)

    # 3) Çoklu boşlukları sadeleştir
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

    return cleaned.strip()

def _compose_final_prompt(
    user_message: str,
    chat_history_text: str,
    memory_context_text: str,
    rag_context_text: str,
    mode: ChatMode,
    intent: IntentLabel,
) -> str:
    parts: List[str] = []

    parts.append(f"[MODE] {mode.value}")
    parts.append(f"[INTENT] {intent.value}")

    if chat_history_text:
        parts.append("\n[CHAT HISTORY]\n" + chat_history_text.strip())

    if memory_context_text:
        parts.append("\n[MEMORY / PROFILE]\n" + memory_context_text.strip())

    if rag_context_text:
        parts.append("\n[KNOWLEDGE CONTEXT]\n" + rag_context_text.strip())

    parts.append("\n[USER MESSAGE]\n" + user_message.strip())
    parts.append("\n[ASSISTANT RESPONSE]\n")

    return "\n".join(parts)




# ---------------------------------------------------------------------------
# Ana Pipeline
# ---------------------------------------------------------------------------

async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Ana sohbet iş akışı.
    """
    user_id = request.user_id or "anonymous"
    session_id = request.session_id or f"session_{user_id}_{int(datetime.utcnow().timestamp())}"

    # 1) Intent + duygu analizi
    intent = detect_intent(request.message, request.mode)
    sentiment, emotion, intensity, topic = analyze_emotion(request.message)

    importance_score = float(intensity)
    is_sensitive = intensity > 0.6 or intent in (
        IntentLabel.EMOTIONAL_SUPPORT,
        IntentLabel.PROFILE_UPDATE,
    )

    user_meta = MessageMetadata(
        mode=request.mode,
        intent=intent,
        sentiment=sentiment,
        emotion=emotion,
        emotion_intensity=intensity,
        importance_score=importance_score,
        is_sensitive=is_sensitive,
        topic=topic,
    )

    user_msg = ChatMessage(
        session_id=session_id,
        role=Role.USER,
        content=request.message,
        created_at=datetime.utcnow(),
        metadata=user_meta,
    )

    # 2) Kullanıcı mesajını DB'ye kaydet
    user_msg = chat_db.save_chat_message(user_msg, user_id=user_id)

    # 3) Kısa vadeli sohbet geçmişi + uzun vadeli hafıza
    recent_messages = chat_db.get_session_messages(
        session_id=session_id,
        limit=settings.memory.short_term_window,
    )

    chat_history_text = memory.build_short_term_history_text(
        user_id=user_id,
        session_id=session_id,
        messages=recent_messages,
    )

    memory_context_text = memory.build_long_term_context_text(
        user_id=user_id,
        session_id=session_id,
        last_message=user_msg,
    )

    # 4) RAG / doküman + web araması konteksi
    rag_context_text = ""
    sources: List[SourceInfo] = []

    try:
        rag_context_text, sources = await rag_engine.build_augmented_context(
            query=request.message,
            user_id=user_id,
            use_web=request.use_web_search,
            max_sources=request.max_sources,
            intent=intent,
            mode=request.mode,
        )
    except Exception as e:
        # Web/RAG tarafında hata olsa bile, sistemi tamamen durdurmuyoruz.
        logger.error("RAG context hatası: %s", e)
        rag_context_text = ""
        sources = []
        # DEBUG: Şimdilik tüm ek bağlamları kapat (geçmiş, hafıza, RAG)
    chat_history_text = ""
    memory_context_text = ""
    rag_context_text = ""
    sources = []
    # 5) Final prompt'u oluştur
    system_prompt = _build_global_system_prompt(request.mode)
    composed_prompt = _compose_final_prompt(
        user_message=request.message,
        chat_history_text=chat_history_text,
        memory_context_text=memory_context_text,
        rag_context_text=rag_context_text,
        mode=request.mode,
        intent=intent,
    )

    # 6) Model seçimi + cevap üretimi
    raw_answer, model_key = await route_and_generate(
        chat_request=request,
        composed_prompt=composed_prompt,
        system_prompt=system_prompt,
        override_temperature=request.temperature,
        override_max_tokens=request.max_tokens,
    )

    # 7) Self-correction (isteğe bağlı, mod/length'e göre)
    try:
        refined_answer = await self_correction.maybe_refine_answer(
            answer=raw_answer,
            user_message=request.message,
            intent=intent,
            mode=request.mode,
            context_text=rag_context_text,
        )
    except Exception as e:
        logger.error("Self-correction hatası: %s", e)
        refined_answer = raw_answer

    # 8) Safety filtresi (şimdilik yumuşak mod)
    try:
        safe_answer, safety_level = safety_filter.apply_safety(
            answer=refined_answer,
            user_id=user_id,
            mode=request.mode,
            intent=intent,
        )
    except Exception as e:
        logger.error("Safety filtresi hatası: %s", e)
        safe_answer = refined_answer
        safety_level = SafetyLevel.OK
        # 8) Safety filtresi (şimdilik yumuşak mod)
    try:
        safe_answer, safety_level = safety_filter.apply_safety(
            answer=refined_answer,
            user_id=user_id,
            mode=request.mode,
            intent=intent,
        )
    except Exception as e:
        logger.error("Safety filtresi hatası: %s", e)
        safe_answer = refined_answer
        safety_level = SafetyLevel.OK

    # 8.5) Model çıktısını temizle (meta tag'ler, İngilizce meta cümleler vs.)
    safe_answer = clean_model_output(safe_answer)

    # 9) Asistan mesajını DB'ye kaydet
    assistant_meta = MessageMetadata(
        mode=request.mode,
        intent=intent,
        sentiment=sentiment,  # Basit: kullanıcının sentiment'iyle başla
        emotion=emotion,
        emotion_intensity=intensity,
        importance_score=importance_score * 0.8,
        is_sensitive=is_sensitive,
        topic=topic,
    )

    assistant_msg = ChatMessage(
        session_id=session_id,
        role=Role.ASSISTANT,
        content=safe_answer,
        created_at=datetime.utcnow(),
        metadata=assistant_meta,
    )
    assistant_msg = chat_db.save_chat_message(assistant_msg, user_id=user_id)

    # 10) Mood log + profil + reflection + reminder tetikleyicileri

    # Mood log
    try:
        mood = MoodLog(
            user_id=user_id,
            session_id=session_id,
            message_id=user_msg.id,
            timestamp=datetime.utcnow(),
            sentiment=sentiment,
            emotion=emotion,
            intensity=intensity,
            topic=topic,
            summary=None,
        )
        chat_db.save_mood_log(mood)
    except Exception as e:
        logger.error("Mood log kaydı hatası: %s", e)

    # Hafıza ve profil güncelleme
    try:
        memory.handle_post_interaction(
            user_id=user_id,
            session_id=session_id,
            user_message=user_msg,
            assistant_message=assistant_msg,
        )
    except Exception as e:
        logger.error("Memory post-interaction hatası: %s", e)

    try:
        profile_service.update_profile_from_message(
            user_id=user_id,
            message=user_msg,
            intent=intent,
            sentiment=sentiment,
            emotion=emotion,
        )
    except Exception as e:
        logger.error("Profil güncelleme hatası: %s", e)

    # Reflection engine
    try:
        reflection_engine.maybe_schedule_reflection(
            user_id=user_id,
            last_message=user_msg,
            sentiment=sentiment,
            emotion=emotion,
            intensity=intensity,
        )
    except Exception as e:
        logger.error("Reflection engine hatası: %s", e)

    # Reminder tetikleyicileri (eğer intent REMINDER_CREATE ise)
    try:
        reminders_service.maybe_handle_reminder_intent(
            user_id=user_id,
            message_text=request.message,
            intent=intent,
            session_id=session_id,
        )
    except Exception as e:
        logger.error("Reminder service hatası: %s", e)

    # 11) ChatResponse oluştur ve döndür
    response = ChatResponse(
        response=safe_answer,
        sources=sources,
        timestamp=datetime.utcnow(),
        mode=request.mode,
        used_model=model_key,
        session_id=session_id,
        metadata={
            "intent": intent.value,
            "sentiment": sentiment.value,
            "emotion": emotion.value,
            "safety_level": safety_level.value,
        },
    )

    return response
