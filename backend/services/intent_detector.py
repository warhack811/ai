"""
services/intent_detector.py - İYİLEŞTİRİLMİŞ
---------------------------------------------
✅ Öneri/karşılaştırma intent'leri eklendi
✅ Kelime önceliği optimize edildi
✅ Daha hassas tespit
"""

from __future__ import annotations
import asyncio
import re
from typing import Tuple

from schemas.common import ChatMode, IntentLabel


# ============================================================
# KELİME LİSTELERİ (ÖNCELİK SIRASINA GÖRE)
# ============================================================

# 1. ÖNCELİKLİ: Recommendation (ÖNERİ)
RECOMMENDATION_KEYWORDS = [
    "öner", "önerisi", "öneri", "tavsiye", "tavsiye et", "tavsiye eder misin",
    "recommend", "suggestion", "suggest",
    "ne almalıyım", "ne seçmeliyim", "hangisini almalıyım",
    "what should i", "which one should i",
    "seçmeli", "tercih", "prefer",
]

# 2. ÖNCELİKLİ: Comparison (KARŞILAŞTIRMA)
COMPARISON_KEYWORDS = [
    "fark", "farkı", "farklar", "difference", "differences",
    "karşılaştır", "karşılaştırma", "compare", "comparison",
    "arasında", "between", "ile", "vs", "versus",
    "hangisi daha", "which is better", "daha iyi",
    "avantaj", "dezavantaj", "pros", "cons",
]

# 3. Kod / Programming
CODE_KEYWORDS = [
    "kod yaz", "kod örneği", "code example",
    "python", "javascript", "react", "fastapi", "java", "c++", "c#",
    "hata alıyorum", "error", "exception", "bug",
    "fonksiyon", "function", "class", "sınıf", "metot", "method",
    "algoritma", "algorithm", "debug", "debugging",
]

# 4. Özet / Summary
SUMMARY_KEYWORDS = [
    "özetle", "özet geç", "özet çıkar", "summarize",
    "kısaca anlat", "kısaca açıkla", "brief",
]

# 5. Açıklama / Explanation
EXPLAIN_KEYWORDS = [
    "açıkla", "açıklar mısın", "explain", "nedir", "ne demek",
    "detaylı anlat", "detaylı açıkla", "anlatır mısın",
]

# 6. Çeviri / Translation
TRANSLATE_KEYWORDS = [
    "çevir", "translate", "ingilizceye çevir", "türkçeye çevir",
]

# 7. Duygusal Destek
EMO_SUPPORT_KEYWORDS = [
    "moralim bozuk", "canım sıkkın", "üzgünüm", "çok kötüyüm",
    "kendimi kötü hissediyorum", "yalnız hissediyorum",
    "kimsem yok", "bunalım", "depresif", "depresyondayım",
    "sinirliyim", "çok sinirliyim", "gerginim", "stresliyim",
]

# 8. Hatırlatma
REMINDER_KEYWORDS = [
    "hatırlat", "bana hatırlat", "alarm kur", "hatırlatıcı",
]

# 9. Profil
PROFILE_KEYWORDS = [
    "beni tanı", "profilimi", "hakkımda", "benimle ilgili",
]

# 10. Doküman
DOCUMENT_KEYWORDS = [
    "yüklediğim dosya", "yüklediğim doküman", "pdf", "belgede", "dokümanda",
]

# 11. Selamlaşma / Small Talk
SMALLTALK_KEYWORDS = [
    "merhaba", "selam", "naber", "nasılsın", "nasilsin", "iyi misin",
    "günaydın", "iyi geceler", "iyi akşamlar", "ne haber",
    "hoş geldin", "hello", "hi", "hey", "good morning",
]

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def _contains_any(text: str, patterns: list[str]) -> bool:
    """Kelime listesinde herhangi biri var mı?"""
    t = text.lower()
    return any(p in t for p in patterns)


def _looks_like_question(text: str) -> bool:
    """Soru gibi görünüyor mu?"""
    t = text.strip().lower()
    
    # Soru işareti var mı?
    if "?" in t:
        return True
    
    # Türkçe soru kelimeleri
    if any(word in t for word in ["nedir", "nasıl", "kimdir", "nerede", "ne zaman", "niçin", "neden"]):
        return True
    
    # Türkçe "mi/mı/mu/mü" soru ekleri
    if re.search(r"\b(mı|mi|mu|mü)\b", t):
        return True
    
    return False


# ============================================================
# ANA INTENT DETECTION FONKSİYONU
# ============================================================

def detect_intent(message: str, mode: ChatMode) -> IntentLabel:
    """
    Mesaj metninden IntentLabel tahmini yapar
    
    ÖNEMLİ: Öncelik sırası önemli!
    1. Recommendation (öneri)
    2. Comparison (karşılaştırma)
    3. Code Help
    4. Summary
    5. Explain
    ... diğerleri
    
    Returns:
        IntentLabel
    """
    text = message.strip().lower()
    
    # ============================================================
    # ÖNCELİK 1: Recommendation (ÖNERİ)
    # ============================================================
    if _contains_any(text, RECOMMENDATION_KEYWORDS):
        return IntentLabel.TASK_REQUEST  # "recommendation" IntentLabel'ı yoksa TASK_REQUEST
    
    # ============================================================
    # ÖNCELİK 2: Comparison (KARŞILAŞTIRMA)
    # ============================================================
    if _contains_any(text, COMPARISON_KEYWORDS):
        return IntentLabel.EXPLAIN  # "compare" IntentLabel'ı yoksa EXPLAIN
    
    # ============================================================
    # ÖNCELİK 3: Hatırlatma
    # ============================================================
    if _contains_any(text, REMINDER_KEYWORDS):
        return IntentLabel.REMINDER_CREATE
    
    # ============================================================
    # ÖNCELİK 4: Duygusal Destek
    # ============================================================
    if _contains_any(text, EMO_SUPPORT_KEYWORDS):
        return IntentLabel.EMOTIONAL_SUPPORT
    
    # ============================================================
    # ÖNCELİK 5: Çeviri
    # ============================================================
    if _contains_any(text, TRANSLATE_KEYWORDS):
        return IntentLabel.TRANSLATE
    
    # ============================================================
    # ÖNCELİK 6: Kod Yardımı
    # ============================================================
    if _contains_any(text, CODE_KEYWORDS) or mode == ChatMode.CODE:
        return IntentLabel.CODE_HELP
    
    # ============================================================
    # ÖNCELİK 7: Özet
    # ============================================================
    if _contains_any(text, SUMMARY_KEYWORDS):
        return IntentLabel.SUMMARIZE
    
    # ============================================================
    # ÖNCELİK 8: Açıklama
    # ============================================================
    if _contains_any(text, EXPLAIN_KEYWORDS):
        return IntentLabel.EXPLAIN
    
    # ============================================================
    # ÖNCELİK 9: Doküman Sorusu
    # ============================================================
    if _contains_any(text, DOCUMENT_KEYWORDS):
        return IntentLabel.DOCUMENT_QUESTION
    
    # ============================================================
    # ÖNCELİK 10: Profil
    # ============================================================
    if _contains_any(text, PROFILE_KEYWORDS):
        return IntentLabel.PROFILE_UPDATE
    
    # ============================================================
    # ÖNCELİK 11: Selamlaşma / Small Talk
    # ============================================================
    if _contains_any(text, SMALLTALK_KEYWORDS):
        return IntentLabel.SMALL_TALK
    
    # ============================================================
    # ÖNCELİK 12: Soru mu?
    # ============================================================
    if _looks_like_question(text):
        return IntentLabel.QUESTION
    
    # ============================================================
    # ÖNCELİK 13: Friend Mode İse Emotional Support
    # ============================================================
    if mode == ChatMode.FRIEND:
        return IntentLabel.EMOTIONAL_SUPPORT
    
    # ============================================================
    # VARSAYILAN
    # ============================================================
    return IntentLabel.QUESTION  # UNKNOWN yerine QUESTION (daha güvenli)


async def detect_intent_async(message: str, mode: ChatMode) -> IntentLabel:
    """
    Async version of detect_intent
    """
    return await asyncio.to_thread(detect_intent, message, mode)