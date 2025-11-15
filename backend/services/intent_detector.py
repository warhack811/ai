"""
services/intent_detector.py
---------------------------
Kullanıcının mesajından temel "niyet"i (intent) çıkarmaya yarayan modül.

Tam bir ML modeli yerine, şu an için iyi tasarlanmış heuristic kurallar kullanıyoruz:
- Soru mu, sohbet mi, özet isteği mi, kod yardımı mı, duygu paylaşımı mı, hatırlatma mı, vb.
- Türkçe odaklı kelime ve kalıp analizi

İleride buraya:
- hafif bir sınıflandırıcı model
- veya LLM tabanlı sınıflandırma
eklenebilir, ancak pipeline tarafındaki API aynı kalır.
"""

from __future__ import annotations
import asyncio
import re
from typing import Tuple

from schemas.common import ChatMode, IntentLabel


QUESTION_PATTERNS = [
    r"\bmi\b", r"\bmu\b", r"\bmü\b", r"\bmu\?\b",
    r"\bne\b", r"\nasil\b", r"nedir", r"kimdir", r"nerede", r"ne zaman",
    r"mıdır", r"midir", r"midır", r"midir",
]

SUMMARY_KEYWORDS = [
    "özetle", "özet geç", "özet çıkar", "kısaca anlat", "kısaca açıkla",
]

EXPLAIN_KEYWORDS = [
    "açıkla", "detaylı anlat", "detaylı açıkla", "nedir", "anlatır mısın",
]

CODE_KEYWORDS = [
    "kod yaz", "python", "javascript", "react", "fastapi", "hata alıyorum",
    "error", "exception", "fonksiyon", "class", "metot", "algoritma",
]

TRANSLATE_KEYWORDS = [
    "çevir", "translate", "ingilizceye çevir", "türkçeye çevir",
]

EMO_SUPPORT_KEYWORDS = [
    "moralim bozuk", "canım sıkkın", "üzgünüm", "çok kötüyüm", "kendimi kötü hissediyorum",
    "yalnız hissediyorum", "kimsem yok", "bunalım", "depresif hissediyorum",
    "sinirliyim", "çok sinirliyim", "çok gerginim", "stresliyim",
]

REMINDER_KEYWORDS = [
    "hatırlat", "bana hatırlat", "alarm kur", "bana yarın", "bana saat",
]

PROFILE_KEYWORDS = [
    "beni tanı", "profilimi", "hakkımda", "benimle ilgili",
]

DOCUMENT_KEYWORDS = [
    "yüklediğim dosya", "yüklediğim doküman", "pdf", "belgede", "dokümanda",
]

SMALLTALK_KEYWORDS = [
    "merhaba", "selam", "naber", "nasılsın", "nasilsin", "iyi misin",
    "günaydın", "iyi geceler", "iyi akşamlar", "ne haber",
]


def _contains_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(p in t for p in patterns)


def _looks_like_question(text: str) -> bool:
    t = text.strip().lower()
    if "?" in t:
        return True
    if any(word in t for word in ["nedir", "nasıl", "kimdir", "nerede", "ne zaman"]):
        return True
    # Türkçe "mi/mı/mu/mü" soru ekleri
    if re.search(r"\b(mı|mi|mu|mü)\b", t):
        return True
    return False


def detect_intent(message: str, mode: ChatMode) -> IntentLabel:
    """
    Mesaj metninden IntentLabel tahmini yapar.

    Basit heuristik:
      - Kod kelimeleri -> CODE_HELP
      - Özet kelimeleri -> SUMMARIZE
      - Çeviri -> TRANSLATE
      - Hatırlatma kelimeleri -> REMINDER_CREATE
      - Duygu / moral bozukluğu -> EMOTIONAL_SUPPORT
      - Yüklenen dokümanlardan bahsediyorsa -> DOCUMENT_QUESTION
      - Soru gibi görünüyorsa -> QUESTION
      - Sıradan selamlaşma / muhabbet -> SMALL_TALK
      - Diğer -> UNKNOWN (ama mode'a göre yorumlanabilir)
    """
    text = message.strip().lower()

    # Önce çok bariz alanlar
    if _contains_any(text, REMINDER_KEYWORDS):
        return IntentLabel.REMINDER_CREATE

    if _contains_any(text, EMO_SUPPORT_KEYWORDS):
        return IntentLabel.EMOTIONAL_SUPPORT

    if _contains_any(text, TRANSLATE_KEYWORDS):
        return IntentLabel.TRANSLATE

    if _contains_any(text, CODE_KEYWORDS) or mode == ChatMode.CODE:
        return IntentLabel.CODE_HELP

    if _contains_any(text, SUMMARY_KEYWORDS):
        return IntentLabel.SUMMARIZE

    if _contains_any(text, EXPLAIN_KEYWORDS):
        return IntentLabel.EXPLAIN

    if _contains_any(text, DOCUMENT_KEYWORDS):
        return IntentLabel.DOCUMENT_QUESTION

    if _contains_any(text, PROFILE_KEYWORDS):
        return IntentLabel.PROFILE_UPDATE

    # Küçük sohbet / selamlama
    if _contains_any(text, SMALLTALK_KEYWORDS):
        return IntentLabel.SMALL_TALK

    # Soru mu?
    if _looks_like_question(text):
        return IntentLabel.QUESTION

    # Mode FRIEND ise ve açık bir soru değilse, muhtemelen sohbet veya duygu paylaşımı
    if mode == ChatMode.FRIEND:
        return IntentLabel.EMOTIONAL_SUPPORT

    # Varsayılan
    return IntentLabel.UNKNOWN
async def detect_intent_async(message: str, mode: ChatMode) -> IntentLabel:
    """
    Async version of detect_intent
    Parallel processing için
    """
    # Zaten hızlı bir fonksiyon, basit async wrap yeterli
    return await asyncio.to_thread(detect_intent, message, mode)
    