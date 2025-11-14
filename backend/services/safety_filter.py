"""
services/safety_filter.py
-------------------------
Yumuşak (soft) güvenlik / güvence filtresi.

Not:
- settings.safety.enabled varsayılan olarak False, yani filtre devre dışı.
- 'uncensored' profilde sadece aşırı uç durumlarda uyarı mesajı ekleyebiliriz.
- Bu modülün amacı: özellikle sağlık/psikoloji/finans gibi alanlarda
  kullanıcıyı bilgilendirmek, tamamen kesmek değil.
"""

from __future__ import annotations

from typing import Tuple

from config import get_settings
from schemas.common import SafetyLevel
from schemas.common import ChatMode, IntentLabel

settings = get_settings()


# Basit anahtar kelime listeleri (çok kaba, sadece örnek)
SELF_HARM_KEYWORDS = [
    "intihar", "kendimi öldürmek", "yaşamak istemiyorum", "bıçaklamak",
]

HEALTH_RISK_KEYWORDS = [
    "ilaç dozunu artırayım", "doktor yerine", "doktor yerine sen", "tıbbi tavsiye",
]

FINANCE_RISK_KEYWORDS = [
    "tüm paramı yatırayım", "tüm paramı basayım", "garanti kazanç", "kesin kazanırım",
]


def _contains_any(text: str, words: list[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def apply_safety(
    answer: str,
    user_id: str,
    mode: ChatMode,
    intent: IntentLabel,
) -> Tuple[str, SafetyLevel]:
    """
    Cevabı yumuşak bir güvenlik filtresinden geçirir.

    - settings.safety.enabled False ise direkt cevap döner.
    - 'uncensored' profilde sadece çok riskli konularda uyarı ekler.
    """
    if not settings.safety.enabled:
        return answer, SafetyLevel.OK

    text = answer.strip().lower()
    level = SafetyLevel.OK
    modified = answer

    # Self-harm
    if _contains_any(text, SELF_HARM_KEYWORDS):
        level = SafetyLevel.RISKY
        if settings.safety.soft_guardrails:
            modified += (
                "\n\n⚠️ **Not:** Eğer kendine zarar verme düşüncelerin varsa, "
                "lütfen güvendiğin bir yakınından veya bir uzmandan destek al. "
                "Ben yardımcı olmaya çalışırım ama gerçek hayattaki destek çok daha önemli."
            )

    # Sağlık / ilaç
    elif _contains_any(text, HEALTH_RISK_KEYWORDS):
        level = SafetyLevel.SENSITIVE
        if settings.safety.soft_guardrails:
            modified += (
                "\n\nℹ️ **Tıbbi uyarı:** Sağlıkla ilgili konularda en doğru karar için "
                "mutlaka bir doktora veya sağlık profesyoneline danışmalısın. "
                "Benim verdiğim bilgiler genel niteliktedir."
            )

    # Finans
    elif _contains_any(text, FINANCE_RISK_KEYWORDS):
        level = SafetyLevel.SENSITIVE
        if settings.safety.soft_guardrails:
            modified += (
                "\n\nℹ️ **Finansal uyarı:** Tüm paranı tek bir yere yatırmak ciddi risk taşır. "
                "Lütfen detaylı araştırma yapmadan ve gerekirse bir uzmana danışmadan "
                "büyük kararlar verme."
            )

    return modified, level
