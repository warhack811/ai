"""
services/reminders_service.py
-----------------------------
Hatırlatma servisi.

Şimdilik:
- Eğer intent REMINDER_CREATE ise,
  mesajı basit bir Reminder kaydına dönüştürür.
- Tarih/saat parser'ı çok basit; ileride doğal dil tarih-parsere
  geçmek kolay olsun diye API sade tutuldu.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from schemas.profile import Reminder, ReminderStatus
from schemas.common import IntentLabel
from services.db import execute


def _create_basic_reminder(
    user_id: str,
    session_id: str,
    message_text: str,
) -> None:
    """
    Doğrudan mesajı açıklama olarak kullanan basit bir reminder oluşturur.
    Zaman/tarih bilgisi şu an için yok (trigger_at NULL).
    """
    now = datetime.utcnow().isoformat()

    title = "Yeni hatırlatma"
    description = message_text.strip()

    execute(
        """
        INSERT INTO reminders (
            user_id, title, description,
            created_at, updated_at,
            trigger_at, recurrence,
            status, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        params=[
            user_id,
            title,
            description,
            now,
            now,
            None,
            None,
            ReminderStatus.ACTIVE.value,
            None,
        ],
        db="chat",
    )


def maybe_handle_reminder_intent(
    user_id: str,
    message_text: str,
    intent: IntentLabel,
    session_id: str,
) -> None:
    """
    intent REMINDER_CREATE ise, basit bir reminder kaydı oluşturur.
    İleride:
    - tarih/saat parsing
    - tekrar eden hatırlatmalar
    - mobil bildirim entegrasyonu
    eklenebilir.
    """
    if intent != IntentLabel.REMINDER_CREATE:
        return

    _create_basic_reminder(
        user_id=user_id,
        session_id=session_id,
        message_text=message_text,
    )
