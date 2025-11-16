"""
services/pipeline.py - ENHANCED PIPELINE WRAPPER
-------------------------------------------------
Bu dosya artık sadece enhanced_pipeline'ı wrap ediyor.

Tüm yeni özellikler enhanced_pipeline.py içinde:
✅ Türkçe işleme (turkish_language_processor)
✅ Personality engine
✅ Semantic intent detection
✅ Response planning
✅ Coherence checking
✅ Reasoning engine
✅ Adaptive learning

ESKİ SİSTEM: Yorumda kaldı (gerekirse geri dönülebilir)
"""

from __future__ import annotations

import logging
from schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

# ============================================
# ENHANCED PIPELINE IMPORT
# ============================================

from services.enhanced_pipeline import process_chat_enhanced


# ============================================
# MAIN FUNCTION
# ============================================

async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Ana chat fonksiyonu - Enhanced pipeline kullanıyor
    
    Bu fonksiyon artık tüm istekleri enhanced_pipeline'a yönlendiriyor.
    """
    logger.info("🚀 Routing to ENHANCED PIPELINE")
    return await process_chat_enhanced(request)


# ============================================
# ESKİ PIPELINE KODU (YORUM SATIRINDA)
# ============================================

# Eski kod gerekirse buradan erişilebilir:
# https://raw.githubusercontent.com/warhack811/ai/main/backend/services/pipeline.py
#
# Veya eski kodu process_chat_legacy() olarak yeniden adlandırıp
# debug amaçlı kullanabilirsiniz.