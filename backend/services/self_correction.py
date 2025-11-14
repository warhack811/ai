"""
services/self_correction.py
---------------------------
Self-correction (öz-düzeltme) katmanı.

Amaç:
- Modelin ilk cevabı çok kısa, anlamsız veya düşük kaliteli ise
  ikinci bir mini-pass ile cevabı iyileştirmek.
- Gereksiz yere her cevapta ekstra süre harcamamak için
  sadece bazı durumlarda devreye girer.
"""

from __future__ import annotations

from typing import Optional

from schemas.common import ChatMode, IntentLabel
from config import get_settings
from services.llm.model_manager import generate_with_model

settings = get_settings()


def _needs_refinement(
    answer: str,
    intent: IntentLabel,
    mode: ChatMode,
) -> bool:
    """
    Cevabın kalitesi ve bağlama göre düzeltme ihtiyacını tahmin eder.
    """
    text = answer.strip().lower()

    # Çok kısa cevaplar (özellikle soru/kod isteği ise)
    if len(text) < 25 and intent in (IntentLabel.QUESTION, IntentLabel.CODE_HELP):
        return True

    # Hata mesajı gibi görünen cevaplar
    if "cevap üretilemedi" in text or "model hatası" in text or "ollama" in text:
        return True

    # Boş veya neredeyse boş
    if not text or text in ("bilmiyorum", "emin değilim"):
        return True

    # Research modunda çok kısa cevap verilmişse
    if mode == ChatMode.RESEARCH and len(text) < 80:
        return True

    return False


async def maybe_refine_answer(
    answer: str,
    user_message: str,
    intent: IntentLabel,
    mode: ChatMode,
    context_text: str,
) -> str:
    """
    Eğer gerekli görürsek Qwen ile cevabı bir kez daha refine eder.

    - Extra bir model çağrısı olduğundan her zaman çalışmaz, sadece
      _needs_refinement True dönerse devreye girer.
    """
    if not _needs_refinement(answer, intent, mode):
        return answer

    # Maksimum ekstra token'i sınırlı tutalım (performans için)
    max_tokens = 512

    prompt = f"""
[USER MESSAGE]
{user_message}

[INITIAL ANSWER]
{answer}

[OPTIONAL CONTEXT]
{context_text[:2000]}

[TASK]
Yukarıdaki cevabı KULLANICI için daha anlaşılır, daha detaylı ve daha kaliteli hale getir.
Türkçe olarak cevap ver. Kısa ama doyurucu bir açıklama yap. Kullanıcıya odaklan.
""".strip()

    refined = await generate_with_model(
        model_key="qwen",
        prompt=prompt,
        system_prompt=(
            "You are an answer-refinement assistant. Improve the given answer "
            "while staying truthful and concise. Respond in Turkish."
        ),
        temperature=0.4,
        max_tokens=max_tokens,
    )

    # Eğer refined cevap da sorunluysa, ilk cevabı koru
    refined = refined.strip()
    if not refined:
        return answer

    return refined
