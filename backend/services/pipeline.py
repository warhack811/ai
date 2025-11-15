"""
services/pipeline.py - DÜZELTILMIŞ FINAL VERSIYON
--------------------
Context'ler AÇIK, ama prompt basitleştirilmiş
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List
import re

from config import get_settings
from schemas.chat import ChatRequest, ChatResponse
from schemas.common import (
    ChatMode,
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
from services import memory
from services import rag_engine
from services import self_correction
from services import safety_filter
from services import profile_service
from services import reflection_engine
from services import reminders_service

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_global_system_prompt(mode: ChatMode) -> str:
    """
    SADELEŞTIRILMIŞ sistem prompt - Türkçe odaklı, gereksiz tag'ler yok
    """
    base = """Sen Türkçe konuşan kişisel bir AI asistansın.

ÖNEMLİ KURALLAR:
- Kullanıcı Türkçe yazıyorsa MUTLAKA Türkçe cevap ver
- Doğal, akıcı ve samimi bir dille konuş
- Emin olmadığın konularda "Tam emin değilim" de, asla uydurma
- Kod sorularında önce kısa açıklama, sonra ```kod``` bloğu ver
- Cevabına [USER], [ASSISTANT], [INST] gibi tag'ler EKLEME
- Geçmiş konuşmayı ve sağlanan bilgileri kullan"""

    if mode == ChatMode.RESEARCH:
        return base + "\n\nMod: Araştırma - Detaylı, yapılandırılmış ve kaynak göstererek cevapla."
    
    if mode == ChatMode.CREATIVE:
        return base + "\n\nMod: Yaratıcı - Daha imgesel ve ilham verici olabilirsin."
    
    if mode == ChatMode.CODE:
        return base + "\n\nMod: Kod - Teknik ve kesin ol. Çalışan kod örnekleri göster."
    
    if mode == ChatMode.FRIEND:
        return base + "\n\nMod: Arkadaş - Samimi ve destekleyici konuş, biraz daha kısa tut."
    
    if mode == ChatMode.TURKISH_TEACHER:
        return base + "\n\nMod: Türkçe Öğretmen - Dilbilgisi hatalarını nazikçe düzelt ve açıkla."
    
    return base


def _compose_final_prompt(
    user_message: str,
    chat_history_text: str,
    memory_context_text: str,
    rag_context_text: str,
) -> str:
    """
    SADELEŞTIRILMIŞ prompt kompozisyonu - gereksiz tag'ler yok
    """
    parts = []
    
    # Geçmiş sohbet (varsa)
    if chat_history_text and chat_history_text.strip():
        parts.append("# Önceki Konuşma")
        parts.append(chat_history_text.strip())
        parts.append("")
    
    # Kullanıcı profili/hafıza (varsa)
    if memory_context_text and memory_context_text.strip():
        parts.append("# Kullanıcı Hakkında")
        parts.append(memory_context_text.strip())
        parts.append("")
    
    # RAG bilgileri (varsa)
    if rag_context_text and rag_context_text.strip():
        parts.append("# İlgili Bilgiler")
        parts.append(rag_context_text.strip())
        parts.append("")
    
    # Güncel kullanıcı mesajı
    parts.append("# Kullanıcı Sorusu")
    parts.append(user_message.strip())
    
    return "\n".join(parts)


def clean_model_output(text: str) -> str:
    """Model çıktısını temizle."""
    if not text:
        return text
    
    # Meta cümleleri kaldır
    patterns = [
        r"\[?User can continue.*?\]?",
        r"\[?Let'?s continue.*?\]?",
        r"Let me respond in Turkish[.:!]?",
        r"\[USER\]",
        r"\[ASSISTANT\]",
        r"\[INST\]",
        r"\[/INST\]",
        r"<\|.*?\|>",  # Special tokens
    ]
    
    cleaned = text
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    
    # Fazla boşlukları düzelt
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    
    return cleaned.strip()


async def process_chat(request: ChatRequest) -> ChatResponse:
    """Ana sohbet pipeline."""
    
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
    
    # 2) Kullanıcı mesajını kaydet
    try:
        user_msg = chat_db.save_chat_message(user_msg, user_id=user_id)
    except Exception as e:
        logger.error(f"DB kayıt hatası: {e}")
    
    # 3) Sohbet geçmişi (SON 5 MESAJ - fazla context model şaşırtıyor)
    chat_history_text = ""
    try:
        recent_messages = chat_db.get_session_messages(
            session_id=session_id,
            limit=5,  # 20 yerine 5
        )
        
        if recent_messages:
            chat_history_text = memory.build_short_term_history_text(
                user_id=user_id,
                session_id=session_id,
                messages=recent_messages,
            )
    except Exception as e:
        logger.error(f"Chat history hatası: {e}")
        chat_history_text = ""
    
    # 4) Uzun vadeli hafıza (ŞİMDİLİK KAPALI - basite indirgiyoruz)
    memory_context_text = ""
    # try:
    #     memory_context_text = memory.build_long_term_context_text(
    #         user_id=user_id,
    #         session_id=session_id,
    #         last_message=user_msg,
    #     )
    # except Exception as e:
    #     logger.error(f"Memory context hatası: {e}")
    
    # 5) RAG context (Web + Doküman) - SADECE İSTENİRSE
    rag_context_text = ""
    sources: List[SourceInfo] = []
    
    if request.use_web_search:
        try:
            rag_context_text, sources = await rag_engine.build_augmented_context(
                query=request.message,
                user_id=user_id,
                use_web=True,
                max_sources=3,  # 5 yerine 3
                intent=intent,
                mode=request.mode,
            )
        except Exception as e:
            logger.error(f"RAG hatası: {e}")
            rag_context_text = ""
            sources = []
    
    # 6) Prompt'u oluştur
    system_prompt = _build_global_system_prompt(request.mode)
    composed_prompt = _compose_final_prompt(
        user_message=request.message,
        chat_history_text=chat_history_text,
        memory_context_text=memory_context_text,
        rag_context_text=rag_context_text,
    )
    
    # DEBUG LOG
    logger.info("=" * 60)
    logger.info("MODEL ÇAĞRISI")
    logger.info("=" * 60)
    logger.info(f"User: {request.message[:100]}...")
    logger.info(f"Mode: {request.mode.value}")
    logger.info(f"Chat history: {len(chat_history_text)} chars")
    logger.info(f"RAG context: {len(rag_context_text)} chars")
    logger.info(f"System prompt: {system_prompt[:150]}...")
    logger.info(f"Full prompt length: {len(composed_prompt)} chars")
    logger.info(f"Temperature: {request.temperature or 0.7}")
    logger.info(f"Max tokens: {request.max_tokens or 2048}")
    
    # 7) Model çağrısı - GELIŞTIRILMIŞ AYARLAR
    try:
        raw_answer, model_key = await route_and_generate(
            chat_request=request,
            composed_prompt=composed_prompt,
            system_prompt=system_prompt,
            override_temperature=request.temperature or 0.7,  # Varsayılan 0.7
            override_max_tokens=request.max_tokens or 2048,   # Varsayılan 2048
        )
        
        logger.info("=" * 60)
        logger.info("MODEL CEVABI")
        logger.info("=" * 60)
        logger.info(f"Model: {model_key}")
        logger.info(f"Raw length: {len(raw_answer)} chars")
        logger.info(f"Raw preview: {raw_answer[:300]}...")
        
    except Exception as e:
        logger.error(f"Model çağrı hatası: {e}", exc_info=True)
        raw_answer = f"Üzgünüm, bir hata oluştu: {str(e)}"
        model_key = "error"
    
    # 8) Self-correction (hafif)
    refined_answer = raw_answer
    try:
        refined_answer = await self_correction.maybe_refine_answer(
            answer=raw_answer,
            user_message=request.message,
            intent=intent,
            mode=request.mode,
            context_text=rag_context_text,
        )
    except Exception as e:
        logger.error(f"Self-correction hatası: {e}")
    
    # 9) Safety filter
    safe_answer = refined_answer
    safety_level = SafetyLevel.OK
    try:
        safe_answer, safety_level = safety_filter.apply_safety(
            answer=refined_answer,
            user_id=user_id,
            mode=request.mode,
            intent=intent,
        )
    except Exception as e:
        logger.error(f"Safety hatası: {e}")
    
    # 10) Çıktıyı temizle
    safe_answer = clean_model_output(safe_answer)
    
    # 11) BOŞ CEVAP KONTROLÜ
    if not safe_answer or len(safe_answer.strip()) < 10:
        logger.error(f"BOŞ CEVAP! Raw: '{raw_answer[:200]}'")
        safe_answer = "Üzgünüm, cevap üretemedim. Lütfen sorunuzu farklı şekilde sorar mısınız?"
    
    logger.info(f"Final answer: {safe_answer[:300]}...")
    logger.info("=" * 60)
    
    # 12) Asistan mesajını kaydet
    assistant_meta = MessageMetadata(
        mode=request.mode,
        intent=intent,
        sentiment=sentiment,
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
    
    try:
        assistant_msg = chat_db.save_chat_message(assistant_msg, user_id=user_id)
    except Exception as e:
        logger.error(f"DB kayıt hatası: {e}")
    
    # 13) Yan etkiler (mood, profil vs.)
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
        logger.error(f"Mood log hatası: {e}")
    
    try:
        memory.handle_post_interaction(
            user_id=user_id,
            session_id=session_id,
            user_message=user_msg,
            assistant_message=assistant_msg,
        )
    except Exception as e:
        logger.error(f"Memory hatası: {e}")
    
    try:
        profile_service.update_profile_from_message(
            user_id=user_id,
            message=user_msg,
            intent=intent,
            sentiment=sentiment,
            emotion=emotion,
        )
    except Exception as e:
        logger.error(f"Profile hatası: {e}")
    
    # 14) Response oluştur
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