"""
backend/services/enhanced_pipeline.py
======================================
ULTIMATE HYBRID PIPELINE - MODEL KEYS DÜZELTİLDİ

Version: 4.1 FIXED
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple

from config import get_settings
from schemas.chat import ChatRequest, ChatResponse
from schemas.common import (
    ChatMode, ChatMessage, MessageMetadata, Role, 
    SourceInfo, IntentLabel, SafetyLevel, EmotionLabel, SentimentLabel
)
from schemas.profile import MoodLog

# Mevcut servisler
from services import chat_db
from services.emotion_detector import analyze_emotion
from services.llm.model_router import route_and_generate
from services.llm.complexity_scorer import ComplexityScorer
from services.cache_manager import get_cache_manager
from services import memory
from services import rag_engine
from services import safety_filter
from services import profile_service

# ESKİ servisler
from services.output_cleaner import OutputCleaner
from services.quality_validator import QualityValidator

# YENİ servisler - Turkish Processing
from services.turkish_language_processor import (
    normalize_user_input,
    enhance_model_output,
    calculate_turkish_quality,
)

# YENİ servisler - Personality
from services.personality_engine import (
    get_personality,
    build_personality_prompt,
)

# YENİ servisler - Semantic Understanding
from services.semantic_intent_detector import detect_intent_semantic

# YENİ servisler - Quality Control
from services.response_coherence_checker import check_response_coherence

# YENİ servisler - Planning
from services.response_planner import (
    plan_response,
    build_planning_instructions,
)

# YENİ servisler - Reasoning
from services.reasoning_engine import (
    should_use_reasoning,
    build_reasoning_prompt,
    extract_reasoning_and_answer,
    verify_reasoning,
)

# YENİ servisler - Learning
from services.adaptive_learning_system import (
    record_feedback,
    detect_implicit_signal,
    get_model_recommendation,
    FeedbackEvent,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Global instances
complexity_scorer = ComplexityScorer()
cache = get_cache_manager()
output_cleaner = OutputCleaner()
quality_validator = QualityValidator()


class EnhancedContextBuilder:
    """Akıllı context oluşturucu"""
    
    @staticmethod
    def should_include_profile(query: str, intent: IntentLabel) -> bool:
        personal_keywords = ['beni', 'ben', 'benim', 'bana', 'hatırla', 'hakkımda']
        if any(kw in query.lower() for kw in personal_keywords):
            return True
        if intent == IntentLabel.PROFILE_UPDATE:
            return True
        return False
    
    @staticmethod
    def should_include_history(query: str, intent: IntentLabel) -> bool:
        if intent == IntentLabel.SMALL_TALK and len(query.split()) < 10:
            return False
        continuation_markers = [
            'peki', 'ee', 'o zaman', 'ayrıca', 'bir de',
            'onun için', 'bunun üzerine', 'daha önce'
        ]
        if any(marker in query.lower() for marker in continuation_markers):
            return True
        creative_keywords = ['fıkra', 'şaka', 'hikaye', 'masal']
        if any(kw in query.lower() for kw in creative_keywords):
            return False
        return True
    
    @staticmethod
    def should_include_rag(query: str, intent: IntentLabel, mode: ChatMode) -> bool:
        if intent == IntentLabel.DOCUMENT_QUESTION:
            return True
        if mode == ChatMode.RESEARCH:
            return True
        if intent == IntentLabel.SMALL_TALK:
            return False
        creative_keywords = ['fıkra', 'şaka', 'hikaye', 'masal', 'şiir']
        if any(kw in query.lower() for kw in creative_keywords):
            return False
        return True
    
    @staticmethod
    def build_smart_context(
        user_message: str,
        mode: ChatMode,
        intent: IntentLabel,
        chat_history: str = "",
        rag_context: str = "",
        profile_context: str = "",
    ) -> str:
        context_parts = []
        
        if EnhancedContextBuilder.should_include_profile(user_message, intent):
            if profile_context and profile_context.strip():
                profile_text = profile_context.strip()[:200]
                context_parts.append(f"[Kullanıcı Hakkında]\n{profile_text}")
                context_parts.append("")
        
        if EnhancedContextBuilder.should_include_rag(user_message, intent, mode):
            if rag_context and rag_context.strip():
                rag_text = rag_context.strip()[:1000]
                context_parts.append(f"[İlgili Bilgiler]\n{rag_text}")
                context_parts.append("")
        
        if EnhancedContextBuilder.should_include_history(user_message, intent):
            if chat_history and chat_history.strip():
                history_text = chat_history.strip()[:500]
                context_parts.append(f"[Önceki Konuşma]\n{history_text}")
                context_parts.append("")
        
        if context_parts:
            context_parts.append(f"[Soru]\n{user_message}")
        else:
            context_parts.append(user_message)
        
        full_context = '\n'.join(context_parts)
        
        if len(full_context) > 2000:
            full_context = full_context[:2000]
        
        return full_context


async def process_chat_enhanced(request: ChatRequest) -> ChatResponse:
    """
    ULTIMATE HYBRID PIPELINE v4.1 FIXED
    """
    
    user_id = request.user_id or "anonymous"
    session_id = request.session_id or f"session_{user_id}_{int(datetime.utcnow().timestamp())}"
    
    logger.info("=" * 80)
    logger.info(f"🚀 ULTIMATE HYBRID PIPELINE v4.1 - NEW REQUEST")
    logger.info(f"   User: {user_id} | Session: {session_id}")
    logger.info(f"   Query: {request.message[:80]}...")
    logger.info("=" * 80)
    
    start_time = datetime.utcnow()
    
    # PHASE 1: INPUT NORMALIZATION
    normalized_message = normalize_user_input(request.message)
    logger.info(f"📝 Normalized: {normalized_message[:80]}...")
    
    # PHASE 2: PARALLEL PREPROCESSING
    async def async_intent():
        cache_key = f"{normalized_message}:{request.mode.value}"
        cached = cache.get_cached_intent(cache_key, request.mode.value)
        if cached:
            return cached, 1.0
        
        intent_result = detect_intent_semantic(
            message=normalized_message,
            mode=request.mode,
            conversation_history=None
        )
        
        cache.cache_intent(cache_key, request.mode.value, intent_result.intent)
        return intent_result.intent, intent_result.confidence
    
    async def async_emotion():
        cached = cache.get_cached_emotion(normalized_message)
        if cached:
            return cached
        emotion_data = analyze_emotion(normalized_message)
        cache.cache_emotion(normalized_message, emotion_data)
        return emotion_data
    
    async def async_history():
        try:
            recent = chat_db.get_session_messages(session_id, limit=6)
            if recent:
                return memory.build_short_term_history_text(
                    user_id=user_id,
                    session_id=session_id,
                    messages=recent,
                    max_exchanges=3
                )
        except Exception as e:
            logger.error(f"History error: {e}")
        return ""
    
    async def async_profile():
        try:
            return memory.build_long_term_context_text(
                user_id=user_id,
                session_id=session_id,
                last_message=None,
            )
        except Exception as e:
            logger.error(f"Profile error: {e}")
        return ""
    
    async def async_rag():
        cached = cache.get_cached_rag(normalized_message)
        if cached:
            return cached
        
        try:
            result = await rag_engine.build_augmented_context(
                query=normalized_message,
                user_id=user_id,
                use_web=request.use_web_search,
                max_sources=3,
                intent=IntentLabel.QUESTION,
                mode=request.mode,
            )
            cache.cache_rag(normalized_message, result[0], result[1])
            return result
        except Exception as e:
            logger.error(f"RAG error: {e}")
            return "", []
    
    parallel_start = datetime.utcnow()
    
    (intent, intent_confidence), (sentiment, emotion, intensity, topic), chat_history, profile_context, (rag_context, sources) = await asyncio.gather(
        async_intent(),
        async_emotion(),
        async_history(),
        async_profile(),
        async_rag()
    )
    
    parallel_time = (datetime.utcnow() - parallel_start).total_seconds() * 1000
    logger.info(f"⚡ Parallel preprocessing: {parallel_time:.0f}ms")
    logger.info(f"   Intent: {intent.value} (conf: {intent_confidence:.2f})")
    logger.info(f"   Emotion: {emotion.value} ({intensity:.2f})")
    
    # PHASE 3: COMPLEXITY SCORING
    complexity = complexity_scorer.score(normalized_message, request.mode, intent)
    logger.info(f"📊 Complexity: {complexity}/10")
    
    # PHASE 3.5: REASONING CHECK
    use_reasoning = should_use_reasoning(
        query=normalized_message,
        intent=intent,
        complexity=complexity,
        mode=request.mode
    )
    
    logger.info(f"🧠 Reasoning: {'YES' if use_reasoning else 'NO'}")
    
    # PHASE 4: PERSONALITY ENGINE
    safety_level = getattr(request, 'safety_level', 0) if hasattr(request, 'safety_level') else 0
    
    personality_profile = get_personality(
        mode=request.mode,
        emotion=emotion,
        sentiment=sentiment,
        safety_level=safety_level,
    )
    
    personality_instructions = build_personality_prompt(personality_profile)
    
    logger.info(f"🎭 Personality: tone={personality_profile.tone.value}, "
                f"formality={personality_profile.formality:.1f}")
    
    # PHASE 4.5: RESPONSE PLANNING
    response_plan = plan_response(
        query=normalized_message,
        intent=intent,
        mode=request.mode,
        complexity=complexity,
    )
    
    planning_instructions = build_planning_instructions(response_plan)
    
    logger.info(f"📋 Response plan: {response_plan.approach} approach")
    
    # PHASE 5: SMART CONTEXT BUILDING
    smart_context = EnhancedContextBuilder.build_smart_context(
        user_message=normalized_message,
        mode=request.mode,
        intent=intent,
        chat_history=chat_history,
        rag_context=rag_context,
        profile_context=profile_context,
    )
    
    logger.info(f"📝 Smart context: {len(smart_context)} chars")
    
    # PHASE 5.5: FINAL PROMPT CONSTRUCTION
    if use_reasoning:
        final_system_prompt = build_reasoning_prompt(
            query=normalized_message,
            context=smart_context,
            base_instructions=f"{personality_instructions}\n\n{planning_instructions}"
        )
        logger.info("🧠 Using reasoning prompt format")
    else:
        final_system_prompt = f"{personality_instructions}\n\n{planning_instructions}"
    
    # PHASE 6: METADATA
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
    
    try:
        user_msg = chat_db.save_chat_message(user_msg, user_id=user_id)
    except Exception as e:
        logger.error(f"DB save error: {e}")
    
    # PHASE 7: ADAPTIVE LEARNING MODEL SELECTION
    # ✅ DÜZELTİLDİ: config.py'deki model key'leriyle uyumlu
    available_models = ["phi", "qwen", "deepseek", "mistral"]
    
    learned_model, learning_confidence = get_model_recommendation(
        intent=intent.value,
        complexity=complexity,
        available_models=available_models
    )
    
    force_model = None
    if learned_model and learning_confidence > 0.7:
        force_model = learned_model
        logger.info(f"📚 Learned recommendation: {learned_model} (conf: {learning_confidence:.2f})")
    
    # PHASE 8: MODEL GENERATION (MULTI-LAYER RETRY)
    max_retries = 2
    best_answer = None
    best_quality = 0.0
    model_key = None
    reasoning_steps = []
    
    for attempt in range(max_retries):
        logger.info(f"🤖 Generation attempt {attempt + 1}/{max_retries}")
        
        model_start = datetime.utcnow()
        
        try:
            raw_answer, model_key = await route_and_generate(
                chat_request=request,
                composed_prompt="",
                system_prompt=final_system_prompt,
                override_temperature=request.temperature or 0.7,
                override_max_tokens=request.max_tokens or 2048,
                intent=intent,
                user_message=normalized_message,
                context=smart_context,
                mode=request.mode,
                force_model=force_model,
            )
            
            model_time = (datetime.utcnow() - model_start).total_seconds() * 1000
            logger.info(f"   Model: {model_key.upper()} | Time: {model_time:.0f}ms")
            
            # REASONING EXTRACTION
            if use_reasoning:
                extracted_steps, extracted_answer = extract_reasoning_and_answer(raw_answer)
                
                if extracted_steps:
                    reasoning_steps = extracted_steps
                    logger.info(f"🧠 Reasoning steps: {len(reasoning_steps)}")
                    
                    is_valid, reasoning_confidence = verify_reasoning(
                        reasoning_steps,
                        extracted_answer,
                        normalized_message
                    )
                    
                    if is_valid:
                        raw_answer = extracted_answer
                        logger.info(f"✅ Reasoning validated (conf: {reasoning_confidence:.2f})")
                    else:
                        logger.warning("⚠️ Reasoning invalid, using full output")
                else:
                    logger.warning("⚠️ No reasoning tags found")
            
            # LAYER 1: ESKİ OUTPUT CLEANER
            cleaned_answer = output_cleaner.clean(raw_answer, model_key)
            logger.info(f"   🧹 Layer 1: OutputCleaner applied")
            
            # LAYER 2: YENİ TURKISH ENHANCEMENT
            enhanced_answer = enhance_model_output(cleaned_answer, aggressive=False)
            logger.info(f"   🇹🇷 Layer 2: Turkish enhancement applied")
            
            # LAYER 3: ESKİ QUALITY VALIDATOR
            is_valid_old, quality_old = quality_validator.validate(enhanced_answer, normalized_message)
            logger.info(f"   ✓ Layer 3: Old quality = {quality_old:.2f}")
            
            # LAYER 4: YENİ TURKISH QUALITY
            turkish_quality = calculate_turkish_quality(enhanced_answer)
            logger.info(f"   🇹🇷 Layer 4: Turkish quality = {turkish_quality.overall:.2f}")
            
            # LAYER 5: YENİ COHERENCE CHECK
            coherence_score = check_response_coherence(
                response=enhanced_answer,
                original_query=normalized_message,
                rag_sources=[s.snippet for s in sources] if sources else None
            )
            logger.info(f"   🔍 Layer 5: Coherence = {coherence_score.overall:.2f}")
            
            # FINAL QUALITY SCORE (5 LAYER)
            overall_quality = (
                quality_old * 0.2 +
                turkish_quality.overall * 0.3 +
                coherence_score.overall * 0.5
            )
            
            logger.info(f"   📊 FINAL QUALITY: {overall_quality:.2f}")
            
            all_issues = turkish_quality.issues + coherence_score.issues
            if all_issues:
                logger.warning(f"   ⚠️ Issues: {', '.join(all_issues[:3])}")
            
            if overall_quality > best_quality:
                best_answer = enhanced_answer
                best_quality = overall_quality
            
            if overall_quality >= 0.7:
                logger.info(f"✅ Quality excellent ({overall_quality:.2f}), stopping retries")
                break
            
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Quality low ({overall_quality:.2f}), retrying...")
                await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Model error (attempt {attempt + 1}): {e}")
            import traceback
            traceback.print_exc()
            if attempt == max_retries - 1:
                best_answer = "Üzgünüm, şu anda bir teknik sorun yaşıyorum. Lütfen tekrar dener misiniz?"
                model_key = "error"
    
    final_answer = best_answer or "Üzgünüm, cevap üretemedim."
    
    # PHASE 9: SAFETY FILTER
    safe_answer = final_answer
    safety_level_result = SafetyLevel.OK
    
    apply_safety = (
        settings.safety.enabled or 
        (hasattr(request, 'safety_level') and request.safety_level and request.safety_level > 0)
    )
    
    if apply_safety:
        try:
            safe_answer, safety_level_result = safety_filter.apply_safety(
                answer=final_answer,
                user_id=user_id,
                mode=request.mode,
                intent=intent,
                safety_level=safety_level,
            )
            logger.info(f"🛡️ Safety: {safety_level_result.value}")
        except Exception as e:
            logger.error(f"Safety filter error: {e}")
    
    # PHASE 10: SAVE ASSISTANT MESSAGE
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
    
    # PHASE 11: SIDE EFFECTS
    async def async_side_effects():
        try:
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
            
            memory.handle_post_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=user_msg,
                assistant_message=assistant_msg,
            )
            
            profile_service.update_profile_from_message(
                user_id=user_id,
                message=user_msg,
                intent=intent,
                sentiment=sentiment,
                emotion=emotion,
            )
        except Exception as e:
            logger.error(f"Side effects error: {e}")
    
    asyncio.create_task(async_side_effects())
    
    # PHASE 12: ADAPTIVE LEARNING
    total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    async def async_learning():
        try:
            previous_msg = None
            previous_resp = None
            
            history = chat_db.get_session_messages(session_id, limit=4)
            if len(history) >= 2:
                for i in range(len(history) - 1, -1, -1):
                    if history[i].role == Role.USER and i != len(history) - 1:
                        previous_msg = history[i].content
                        break
                
                for i in range(len(history) - 1, -1, -1):
                    if history[i].role == Role.ASSISTANT:
                        previous_resp = history[i].content
                        break
            
            implicit_signal = detect_implicit_signal(
                current_query=request.message,
                previous_query=previous_msg,
                previous_response=previous_resp,
                user_id=user_id
            )
            
            feedback_event = FeedbackEvent(
                user_id=user_id,
                session_id=session_id,
                message_id=assistant_msg.id,
                query=request.message,
                response=safe_answer,
                model_used=model_key,
                explicit_rating=None,
                implicit_signal=implicit_signal,
                intent=intent.value,
                mode=request.mode.value,
                complexity=complexity,
                response_time_ms=total_time,
                timestamp=datetime.utcnow()
            )
            
            record_feedback(feedback_event)
            
            logger.info(f"📚 Learning: '{implicit_signal}' signal recorded")
            
        except Exception as e:
            logger.error(f"Learning error: {e}")
    
    asyncio.create_task(async_learning())
    
    # PHASE 13: BUILD RESPONSE
    logger.info("=" * 80)
    logger.info(f"✅ ULTIMATE HYBRID PIPELINE v4.1 COMPLETE")
    logger.info(f"   Total: {total_time:.0f}ms | Model: {model_key.upper()}")
    logger.info(f"   Quality: {best_quality:.2f} | Safety: {safety_level_result.value}")
    if use_reasoning and reasoning_steps:
        logger.info(f"   Reasoning: {len(reasoning_steps)} steps")
    logger.info(f"   Answer: {safe_answer[:100]}...")
    logger.info("=" * 80)
    
    response = ChatResponse(
        response=safe_answer,
        sources=sources,
        timestamp=datetime.utcnow(),
        mode=request.mode,
        used_model=model_key,
        session_id=session_id,
        metadata={
            "intent": intent.value,
            "intent_confidence": intent_confidence,
            "sentiment": sentiment.value,
            "emotion": emotion.value,
            "safety_level": safety_level_result.value,
            "complexity_score": complexity,
            "quality_score": best_quality,
            "total_time_ms": total_time,
            "used_reasoning": use_reasoning,
            "reasoning_steps_count": len(reasoning_steps) if reasoning_steps else 0,
        },
    )
    
    return response