"""
services/emotion_detector.py
----------------------------
Kullanıcının mesajındaki genel duygu durumunu tahmin eden modül.

Tam bir derin öğrenme modeli yerine:
- Türkçe pozitif/negatif kelime listeleri
- Duyguya özgü ifadeler (üzgün, sinirli, yalnız, vs.)
- Noktalama (!!!, ??), büyük harf, vb.

Bu sayede:
- Sadece "üzgünüm" demediğinde bile, "hiç iyi hissetmiyorum" gibi
  dolaylı ifadelerden de çıkarım yapmaya çalışır.
"""

from __future__ import annotations
import asyncio
from typing import Tuple
import re
from typing import Tuple

from schemas.common import EmotionLabel, SentimentLabel


POSITIVE_WORDS = [
    "mutluyum", "harika", "süper", "iyi hissediyorum", "keyfim yerinde",
    "mükemmel", "şahane", "süperim", "çok iyiyim", "heyecanlıyım",
]

NEGATIVE_WORDS = [
    "kötüyüm", "çok kötüyüm", "berbat", "rezalet", "hiç iyi değilim",
    "berbat hissediyorum", "sıkıldım", "bıktım", "tükendim", "yorgunum",
    "yorgun hissediyorum", "hiç enerjim yok",
]

SAD_WORDS = [
    "üzgün", "üzgünüm", "canım sıkkın", "moralim bozuk", "mutsuzum",
    "ağlamak istiyorum", "depresif", "boşlukta hissediyorum",
]

ANGRY_WORDS = [
    "sinirliyim", "çok sinirliyim", "öfkeli", "öfkeliyim", "kafayı yiyeceğim",
    "çok gerginim", "gerildim", "delireceğim", "sinir oldum",
]

ANXIOUS_WORDS = [
    "kaygılıyım", "kaygı", "endişeliyim", "korkuyorum", "endişe ediyorum",
    "panik", "panik atak", "içim içimi yiyor",
]

LONELY_WORDS = [
    "yalnızım", "yalnız hissediyorum", "kimsem yok", "yapayalnızım",
]

TIRED_WORDS = [
    "yorgunum", "çok yorgunum", "bitkinim", "tükendim", "uykum var",
]

EXCITED_WORDS = [
    "heyecanlıyım", "sabırsızlanıyorum", "dört gözle bekliyorum",
]


def _score_emotion(text: str, keywords: list[str]) -> int:
    """Verilen keyword listesi için basit skor."""
    t = text.lower()
    score = 0
    for k in keywords:
        if k in t:
            score += 2
    return score


def _basic_sentiment(text: str) -> SentimentLabel:
    """
    Basit pozitif/negatif kelime sayımı ile sentiment.
    """
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)

    # Çok kaba ama başlangıç için yeterli
    if pos > neg and pos > 0:
        return SentimentLabel.POSITIVE
    if neg > pos and neg > 0:
        return SentimentLabel.NEGATIVE
    if pos == 0 and neg == 0:
        return SentimentLabel.UNKNOWN
    return SentimentLabel.MIXED


def analyze_emotion(message: str) -> Tuple[SentimentLabel, EmotionLabel, float, str]:
    """
    Mesaj için:
      - SentimentLabel (positive/negative/neutral/mixed/unknown)
      - EmotionLabel (happy, sad, angry, anxious, lonely, tired, excited, none)
      - intensity (0-1 arası basit bir normalizasyon)
      - topic (şimdilik boş string veya 'general')

    intensity:
      - güçlü kelimeler + ünlem sayısı + küfür vs. ile kabaca ölçeklenir.
    """
    text = message.strip().lower()

    sentiment = _basic_sentiment(text)

    # Duygu skorları
    scores = {
        EmotionLabel.HAPPY: _score_emotion(text, POSITIVE_WORDS),
        EmotionLabel.SAD: _score_emotion(text, SAD_WORDS),
        EmotionLabel.ANGRY: _score_emotion(text, ANGRY_WORDS),
        EmotionLabel.ANXIOUS: _score_emotion(text, ANXIOUS_WORDS),
        EmotionLabel.LONELY: _score_emotion(text, LONELY_WORDS),
        EmotionLabel.TIRED: _score_emotion(text, TIRED_WORDS),
        EmotionLabel.EXCITED: _score_emotion(text, EXCITED_WORDS),
    }

    # Büyük harf ve ünlem / soru yoğunluğu da intensiteyi etkilesin
    exclamations = text.count("!")
    questions = text.count("?")
    caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)

    base_intensity = (exclamations * 0.1) + (questions * 0.05) + (caps_ratio * 0.5)

    # En yüksek skorlu duyguyu bul
    best_emotion = EmotionLabel.NONE
    best_score = 0
    for emo, sc in scores.items():
        if sc > best_score:
            best_score = sc
            best_emotion = emo

    # Skoru 0-1 arası kaba normalizasyon
    final_intensity = min(1.0, max(0.0, base_intensity + best_score * 0.2))

    # Topic (şimdilik sadece 'general')
    topic = "general"

    # Eğer hiçbir belirgin duygu yoksa:
    if best_emotion == EmotionLabel.NONE and sentiment == SentimentLabel.UNKNOWN:
        final_intensity = 0.0

    return sentiment, best_emotion, final_intensity, topic
async def analyze_emotion_async(message: str) -> Tuple[SentimentLabel, EmotionLabel, float, str]:
    """
    Async version of analyze_emotion
    Parallel processing için
    """
    # Zaten hızlı bir fonksiyon, basit async wrap yeterli
    return await asyncio.to_thread(analyze_emotion, message)
