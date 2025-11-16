"""
services/pipeline.py - FAS 1 VERSION
--------------------
✅ Native prompt templates
✅ Fixed memory system
✅ Optimized context
✅ Better performance
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from typing import List

from config import get_settings
from schemas.chat import ChatRequest, ChatResponse
from schemas.common import (
    ChatMode, ChatMessage, MessageMetadata, Role, 
    SourceInfo, IntentLabel, SafetyLevel
)
from schemas.profile import MoodLog
from services import chat_db
from services.intent_detector import detect_intent
from services.emotion_detector import analyze_emotion
from services.llm.model_router import route_and_generate
from services.llm.complexity_scorer import ComplexityScorer
from services.context_builder import build_smart_context
from services.output_cleaner import OutputCleaner
from services.quality_validator import QualityValidator
from services.cache_manager import get_cache_manager
from services import memory
from services import rag_engine
from services import safety_filter
from services import profile_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Global instances
output_cleaner = OutputCleaner()
quality_validator = QualityValidator()
complexity_scorer = ComplexityScorer()
cache = get_cache_manager()


async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    FAS 1: OPTIMIZED PIPELINE
    - Native prompt templates ✅
    - Fixed memory contamination ✅
    - Optimized context building ✅
    - Better performance ✅
    """
    
    user_id = request.user_id or "anonymous"
    session_id = request.session_id or f"session_{user_id}_{int(datetime.utcnow().timestamp())}"
    
    logger.info("=" * 60)
    logger.info(f"📥 NEW REQUEST: {request.message[:80]}...")
    logger.info(f"   User: {user_id} | Session: {session_id}")
    logger.info("=" * 60)
    
    start_time = datetime.utcnow()
    
    # ============================================
    # PHASE 1: PARALLEL PREPROCESSING
    # ============================================
    
    async def async_intent():
        """Intent detection with cache"""
        cached = cache.get_cached_intent(request.message, request.mode.value)
        if cached:
            logger.debug("✓ Intent from cache")
            return cached
        
        intent = detect_intent(request.message, request.mode)
        cache.cache_intent(request.message, request.mode.value, intent)
        return intent
    
    async def async_emotion():
        """Emotion analysis with cache"""
        cached = cache.get_cached_emotion(request.message)
        if cached:
            logger.debug("✓ Emotion from cache")
            return cached
        
        emotion_data = analyze_emotion(request.message)
        cache.cache_emotion(request.message, emotion_data)
        return emotion_data
    
    async def async_history():
        """Chat history fetch - FIXED VERSION"""
        try:
            # Son 15 exchange'i getir (30 mesaj) - daha uzun hafıza
            recent = chat_db.get_session_messages(session_id, limit=30)
            if recent:
                # YENİ: Temiz format kullan (meta tag'siz)
                return memory.build_short_term_history_text(
                    user_id=user_id,
                    session_id=session_id,
                    messages=recent,
                    max_exchanges=15  # Son 15 soru-cevap
                )
        except Exception as e:
            logger.error(f"History error: {e}")
        return ""
    
    async def async_profile():
        """User profile context"""
        try:
            return memory.build_long_term_context_text(
                user_id=user_id,
                session_id=session_id,
                last_message=None,  # Will be set later
            )
        except Exception as e:
            logger.error(f"Profile error: {e}")
        return ""
    
    async def async_rag():
        """RAG pipeline with cache"""
        # RAG her zaman çalışsın (use_web_search olmasa da local docs için)
        
        # Cache check
        cached = cache.get_cached_rag(request.message)
        if cached:
            logger.debug("✓ RAG from cache")
            return cached
        
        try:
            result = await rag_engine.build_augmented_context(
                query=request.message,
                user_id=user_id,
                use_web=request.use_web_search,
                max_sources=3,
                intent=IntentLabel.QUESTION,  # Will be updated after intent detection
                mode=request.mode,
            )
            cache.cache_rag(request.message, result[0], result[1])
            return result
        except Exception as e:
            logger.error(f"RAG error: {e}")
            return "", []
    
    # 🚀 RUN ALL IN PARALLEL
    logger.info("⚡ Running parallel preprocessing...")
    parallel_start = datetime.utcnow()
    
    intent, (sentiment, emotion, intensity, topic), chat_history, profile_context, (rag_context, sources) = await asyncio.gather(
        async_intent(),
        async_emotion(),
        async_history(),
        async_profile(),
        async_rag()
    )
    
    parallel_time = (datetime.utcnow() - parallel_start).total_seconds() * 1000
    logger.info(f"✓ Parallel preprocessing: {parallel_time:.0f}ms")
    logger.info(f"   Intent: {intent.value} | Emotion: {emotion.value} ({intensity:.2f})")
    
    # ============================================
    # PHASE 2: COMPLEXITY SCORING
    # ============================================
    
    complexity = complexity_scorer.score(request.message, request.mode, intent)
    logger.info(f"📊 Complexity: {complexity}/10")
    
    # ============================================
    # PHASE 3: BUILD METADATA
    # ============================================
    
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
    
    # Save user message
    try:
        user_msg = chat_db.save_chat_message(user_msg, user_id=user_id)
    except Exception as e:
        logger.error(f"DB save error: {e}")
    
    # ============================================
    # PHASE 4: BUILD OPTIMIZED CONTEXT
    # ============================================
    
    system_prompt, composed_prompt = build_smart_context(
        user_message=request.message,
        mode=request.mode,
        chat_history=chat_history,
        rag_context=rag_context,
        complexity=complexity,
        profile_context=profile_context,
    )
    
    logger.info(f"📝 Context: {len(composed_prompt)} chars")
    
    # ============================================
    # PHASE 5: MODEL GENERATION (NATIVE TEMPLATES)
    # ============================================
    
    model_start = datetime.utcnow()
    
    try:
        # YENİ: Native template sistemini kullan
        raw_answer, model_key = await route_and_generate(
            chat_request=request,
            composed_prompt=composed_prompt,  # Deprecated but kept for compatibility
            system_prompt=system_prompt,  # Deprecated but kept for compatibility
            override_temperature=request.temperature or 0.7,
            override_max_tokens=request.max_tokens or 2048,
            intent=intent,  # Pass intent for better routing
            # YENİ PARAMETRELER:
            user_message=request.message,
            context=composed_prompt,  # Temiz context
            mode=request.mode,
        )
        
        model_time = (datetime.utcnow() - model_start).total_seconds() * 1000
        logger.info(f"🤖 Model: {model_key.upper()} | Time: {model_time:.0f}ms | Length: {len(raw_answer)} chars")
        
    except Exception as e:
        logger.error(f"Model error: {e}", exc_info=True)
        raw_answer = f"Üzgünüm, bir hata oluştu: {str(e)}"
        model_key = "error"
    
    # ============================================
    # PHASE 6: OUTPUT CLEANING & VALIDATION
    # ============================================
    
    cleaned_answer = output_cleaner.clean(raw_answer, model_key)
    is_valid, quality_score = quality_validator.validate(cleaned_answer, request.message)
    
    if not is_valid:
        logger.warning(f"⚠️ Low quality output (score: {quality_score:.2f})")
        cleaned_answer = "Üzgünüm, tatmin edici bir cevap üretemedim. Lütfen sorunuzu farklı şekilde sorar mısınız?"
        quality_score = 0.3
    
    logger.info(f"✨ Quality score: {quality_score:.2f}")
    
    # ============================================
    # PHASE 7: SAFETY FILTER
    # ============================================
    
    safe_answer = cleaned_answer
    safety_level = SafetyLevel.OK
    
    # Sansür seviyesi kontrolü
    apply_safety = (
        settings.safety.enabled or 
        (hasattr(request, 'safety_level') and request.safety_level and request.safety_level > 0)
    )
    
    if apply_safety:
        try:
            safe_answer, safety_level = safety_filter.apply_safety(
                answer=cleaned_answer,
                user_id=user_id,
                mode=request.mode,
                intent=intent,
                safety_level=getattr(request, 'safety_level', 0),
            )
            logger.info(f"🛡️ Safety level: {safety_level.value}")
        except Exception as e:
            logger.error(f"Safety filter error: {e}")
    
    # ============================================
    # PHASE 8: SAVE ASSISTANT MESSAGE
    # ============================================
    
    assistant_meta = MessageMetadata(
        mode=request.mode,
        intent=intent,
        sentiment=sentiment,
        emotion=emotion,
        emotion_intensity=intensity * 0.8,
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
        logger.error(f"DB save error: {e}")
    
    # ============================================
    # PHASE 9: SIDE EFFECTS (async, non-blocking)
    # ============================================
    
    async def async_side_effects():
        try:
            # Mood log
            mood = MoodLog(
                user_id=user_id,
                session_id=session_id,
                message_id=user_msg.id if user_msg.id else None,
                timestamp=datetime.utcnow(),
                sentiment=sentiment,
                emotion=emotion,
                intensity=intensity,
                topic=topic,
                summary=None,
            )
            chat_db.save_mood_log(mood)
            
            # Memory update
            memory.handle_post_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=user_msg,
                assistant_message=assistant_msg,
            )
            
            # Profile update
            profile_service.update_profile_from_message(
                user_id=user_id,
                message=user_msg,
                intent=intent,
                sentiment=sentiment,
                emotion=emotion,
            )
        except Exception as e:
            logger.error(f"Side effects error: {e}")
    
    # Run in background
    asyncio.create_task(async_side_effects())
    
    # ============================================
    # PHASE 10: BUILD RESPONSE
    # ============================================
    
    total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    logger.info("=" * 60)
    logger.info(f"✅ RESPONSE COMPLETE")
    logger.info(f"   Total: {total_time:.0f}ms | Model: {model_key.upper()}")
    logger.info(f"   Quality: {quality_score:.2f} | Safety: {safety_level.value}")
    logger.info(f"   Answer: {safe_answer[:100]}...")
    logger.info("=" * 60)
    
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
            "complexity_score": complexity,
            "quality_score": quality_score,
            "total_time_ms": total_time,
            "model_time_ms": model_time if 'model_time' in locals() else 0,
        },
    )
    
    return response