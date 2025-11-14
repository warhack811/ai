"""
services/chat_db.py
-------------------
Sohbet, mood (duygu günlüğü) ve temel istatistikler için
SQLite tabanlı veri erişim katmanı.

Tablolar:
- chat_messages (services.db.init_chat_db içinde oluşturuluyor)
- mood_logs
- reflections
- reminders

Bu modül:
- mesaj kaydetme / okuma
- mood log kaydetme / okuma
- basit istatistik sorguları
için kullanılacak.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Tuple

from schemas.common import ChatMessage, MessageMetadata, Role
from schemas.profile import MoodLog
from services.db import fetch_all, fetch_one, fetch_val, execute


# ---------------------------------------------------------------------------
# Yardımcı dönüştürme fonksiyonları
# ---------------------------------------------------------------------------

def _metadata_to_db_columns(meta: Optional[MessageMetadata]) -> Tuple:
    """
    MessageMetadata nesnesini chat_messages tablosundaki ilgili kolonlara çevirir.
    Kolonlar:
        mode, intent, sentiment, emotion, emotion_intensity,
        importance_score, is_sensitive, topic
    """
    if meta is None:
        return (None, None, None, None, None, None, None, None)

    return (
        meta.mode.value if meta.mode else None,
        meta.intent.value if meta.intent else None,
        meta.sentiment.value if meta.sentiment else None,
        meta.emotion.value if meta.emotion else None,
        meta.emotion_intensity,
        meta.importance_score,
        1 if meta.is_sensitive else (0 if meta.is_sensitive is not None else None),
        meta.topic,
    )


def _row_to_chat_message(row: dict) -> ChatMessage:
    """
    chat_messages satırını ChatMessage modeline dönüştürür.
    """
    from schemas.common import MessageMetadata  # circular import riskini azaltmak için local

    metadata = MessageMetadata(
        mode=row.get("mode"),
        intent=row.get("intent"),
        sentiment=row.get("sentiment"),
        emotion=row.get("emotion"),
        emotion_intensity=row.get("emotion_intensity"),
        importance_score=row.get("importance_score"),
        is_sensitive=bool(row["is_sensitive"]) if row.get("is_sensitive") is not None else None,
        topic=row.get("topic"),
    )

    # Bazı alanlar None olabilir, Pydantic uygun casting yapar
    msg = ChatMessage(
        id=row.get("id"),
        session_id=row.get("session_id"),
        role=row.get("role"),
        content=row.get("content"),
        created_at=datetime.fromisoformat(row["created_at"]),
        metadata=metadata,
    )
    return msg


# ---------------------------------------------------------------------------
# Sohbet Mesajları
# ---------------------------------------------------------------------------

def save_chat_message(message: ChatMessage, user_id: Optional[str] = None) -> ChatMessage:
    """
    Tek bir ChatMessage kaydeder ve id'yi doldurup geri döner.

    Not:
    - user_id API'den ayrı gelebilir; mesaj içinde yoksa parametreden alırız.
    - created_at alanı dolu değilse şu anki zamanı kullanırız.
    """
    if message.created_at is None:
        message.created_at = datetime.utcnow()

    db_user_id = user_id
    if message.session_id is None:
        # Session id yoksa da ileride burada üretilebilir,
        # şimdilik client tarafının gönderdiğini varsayıyoruz.
        pass

    meta_cols = _metadata_to_db_columns(message.metadata)

    sql = """
        INSERT INTO chat_messages (
            session_id,
            user_id,
            role,
            content,
            created_at,
            mode,
            intent,
            sentiment,
            emotion,
            emotion_intensity,
            importance_score,
            is_sensitive,
            topic
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    params = (
        message.session_id,
        db_user_id,
        message.role.value if isinstance(message.role, Role) else message.role,
        message.content,
        message.created_at.isoformat(),
        *meta_cols,
    )

    # execute() sadece rowcount döndürüyor; id almak için fetch_val kullanıyoruz
    execute(sql, params, db="chat")

    # Son eklenen id'yi al
    new_id = fetch_val("SELECT last_insert_rowid() AS id;", db="chat")
    message.id = int(new_id) if new_id is not None else None
    return message


def get_session_messages(session_id: str, limit: int = 50) -> List[ChatMessage]:
    """
    Belirli bir session_id'ye ait son N mesajı (tarih sırasına göre) getirir.
    """
    sql = """
        SELECT
            id, session_id, user_id, role, content, created_at,
            mode, intent, sentiment, emotion,
            emotion_intensity, importance_score, is_sensitive, topic
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?;
    """
    rows = fetch_all(sql, params=[session_id, limit], db="chat")
    return [_row_to_chat_message(r) for r in rows]


def get_recent_messages_for_user(user_id: str, limit: int = 100) -> List[ChatMessage]:
    """
    Kullanıcının tüm oturumlarındaki son N mesajı getirir.
    Mood/profil çıkarımı için kullanılabilir.
    """
    sql = """
        SELECT
            id, session_id, user_id, role, content, created_at,
            mode, intent, sentiment, emotion,
            emotion_intensity, importance_score, is_sensitive, topic
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?;
    """
    rows = fetch_all(sql, params=[user_id, limit], db="chat")
    # DESC aldık, ama kronolojik sırayla dönmek istersek ters çevirebiliriz
    rows.reverse()
    return [_row_to_chat_message(r) for r in rows]


# ---------------------------------------------------------------------------
# Mood / Duygu Günlüğü
# ---------------------------------------------------------------------------

def save_mood_log(mood: MoodLog) -> MoodLog:
    """
    MoodLog kaydedip id ile birlikte geri döner.
    """
    if mood.timestamp is None:
        mood.timestamp = datetime.utcnow()

    sql = """
        INSERT INTO mood_logs (
            user_id,
            session_id,
            message_id,
            timestamp,
            sentiment,
            emotion,
            intensity,
            topic,
            summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    params = (
        mood.user_id,
        mood.session_id,
        mood.message_id,
        mood.timestamp.isoformat(),
        mood.sentiment.value if mood.sentiment else None,
        mood.emotion.value if mood.emotion else None,
        mood.intensity,
        mood.topic,
        mood.summary,
    )

    execute(sql, params=params, db="chat")
    new_id = fetch_val("SELECT last_insert_rowid() AS id;", db="chat")
    mood.id = int(new_id) if new_id is not None else None
    return mood


def get_mood_logs_for_period(
    user_id: str,
    from_date: date,
    to_date: date,
) -> List[MoodLog]:
    """
    Belirli tarih aralığı için kullanıcının mood loglarını getirir.
    """
    sql = """
        SELECT
            id,
            user_id,
            session_id,
            message_id,
            timestamp,
            sentiment,
            emotion,
            intensity,
            topic,
            summary
        FROM mood_logs
        WHERE user_id = ?
          AND date(timestamp) BETWEEN date(?) AND date(?)
        ORDER BY timestamp ASC;
    """
    rows = fetch_all(
        sql,
        params=[user_id, from_date.isoformat(), to_date.isoformat()],
        db="chat",
    )

    logs: List[MoodLog] = []
    for r in rows:
        logs.append(
            MoodLog(
                id=r.get("id"),
                user_id=r["user_id"],
                session_id=r.get("session_id"),
                message_id=r.get("message_id"),
                timestamp=datetime.fromisoformat(r["timestamp"]),
                sentiment=r.get("sentiment") or "unknown",
                emotion=r.get("emotion") or "none",
                intensity=r.get("intensity") or 0.0,
                topic=r.get("topic"),
                summary=r.get("summary"),
            )
        )
    return logs


# ---------------------------------------------------------------------------
# Basit İstatistikler
# ---------------------------------------------------------------------------

def get_total_queries() -> int:
    """
    Toplam soru sayısı:
    - 'user' rolündeki mesajları "soru" kabul ediyoruz.
    İstersen bu mantığı ileride geliştirebiliriz (intent=QUESTION vs.).
    """
    sql = "SELECT COUNT(*) AS cnt FROM chat_messages WHERE role = 'user';"
    value = fetch_val(sql, db="chat")
    return int(value or 0)


def get_total_messages() -> int:
    """
    Toplam mesaj sayısı (user + assistant + system).
    """
    sql = "SELECT COUNT(*) AS cnt FROM chat_messages;"
    value = fetch_val(sql, db="chat")
    return int(value or 0)


def get_db_chat_size_rows() -> int:
    """
    Sohbet DB'sinin satır olarak boyutu (chat_messages).
    Frontend'teki 'db_size' için diğer db'lerle birlikte de kullanılabilir.
    """
    sql = "SELECT COUNT(*) AS cnt FROM chat_messages;"
    value = fetch_val(sql, db="chat")
    return int(value or 0)


def get_recent_sessions(limit: int = 20) -> List[str]:
    """
    Son kullanılan session_id'leri döner. İleride session listesi için kullanılabilir.
    """
    sql = """
        SELECT DISTINCT session_id
        FROM chat_messages
        ORDER BY MAX(id) OVER (PARTITION BY session_id) DESC
        LIMIT ?;
    """
    # SQLite'ta WINDOW fonksiyonları her versiyonda yok olabilir,
    # bu yüzden alternatif bir yöntem kullanmak daha güvenli:
    sql_alt = """
        SELECT session_id
        FROM chat_messages
        GROUP BY session_id
        ORDER BY MAX(id) DESC
        LIMIT ?;
    """
    rows = fetch_all(sql_alt, params=[limit], db="chat")
    return [r["session_id"] for r in rows if r.get("session_id")]
