"""
services/reflection_engine.py
-----------------------------
Reflection / öz değerlendirme sistemi.

Şu an için:
- Mesaj sonrasında basit bir "belki reflection lazım mı?" kararı verir
- Gerçek ReflectionEntry oluşturma işini daha sonraya bırakıyoruz
  (tablo hazır, API hazır; detaylı mantık eklemek kolay olacak).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from schemas.common import SentimentLabel, EmotionLabel, ChatMessage
from services.db import fetch_one, execute


def _get_last_reflection_time(user_id: str) -> Optional[datetime]:
    row = fetch_one(
        """
        SELECT created_at
        FROM reflections
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        params=[user_id],
        db="chat",
    )
    if not row:
        return None
    try:
        return datetime.fromisoformat(row["created_at"])
    except Exception:
        return None


def maybe_schedule_reflection(
    user_id: str,
    last_message: ChatMessage,
    sentiment: SentimentLabel,
    emotion: EmotionLabel,
    intensity: float,
) -> None:
    """
    Çok basit bir strateji:
    - Eğer kullanıcı bir süredir olumsuz duygular paylaşıyorsa
      ve son reflection üzerinden 3+ gün geçmişse,
      reflections tablosuna bir "todo" kaydı atabiliriz.

    Şimdilik reflection metnini üretmiyoruz, sadece boş iskelet bırakıyoruz.
    """
    # Düşük intensite veya pozitif/mixed sentiment ise hiç uğraşma
    if intensity < 0.6 or sentiment in (SentimentLabel.POSITIVE, SentimentLabel.MIXED):
        return

    last_ref = _get_last_reflection_time(user_id)
    if last_ref and (datetime.utcnow() - last_ref) < timedelta(days=3):
        return

    now = datetime.utcnow().isoformat()

    execute(
        """
        INSERT INTO reflections (
            user_id,
            reflection_type,
            created_at,
            period_start,
            period_end,
            observation,
            suggestions,
            user_feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        params=[
            user_id,
            "weekly",
            now,
            None,
            None,
            "Reflection placeholder - ileride ayrıntılı analiz eklenecek.",
            None,
            None,
        ],
        db="chat",
    )
