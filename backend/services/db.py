"""
services/db.py
--------------
SQLite veritabanı yardımcıları.

- 3 ayrı DB dosyası:
    * chat_history.db   (chat, mood, reminders, reflections)
    * knowledge.db      (dokümanlar ve chunk'lar)
    * profile.db        (kullanıcı profili ve hedefler)

Sağlanan fonksiyonlar:
- init_databases()
- execute, executemany
- fetch_one, fetch_all, fetch_val
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, List, Optional

from config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------
def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_def: str) -> None:
    """
    Var olan tabloda eksik kolon varsa ALTER TABLE ile ekler.
    Örn: _ensure_column(conn, "chat_messages", "mode", "TEXT")
    """
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = [row["name"] for row in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def};")

def _get_db_path(db: str) -> Path:
    """
    db parametresi:
      - "chat"
      - "knowledge"
      - "profile"
    """
    if db == "chat":
        return settings.db.chat_db_path
    if db == "knowledge":
        return settings.db.knowledge_db_path
    if db == "profile":
        return settings.db.profile_db_path
    # Varsayılan: chat
    return settings.db.chat_db_path


def _get_connection(db: str) -> sqlite3.Connection:
    path = _get_db_path(db)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, timeout=settings.db.sqlite_timeout)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Genel SQL yardımcıları
# ---------------------------------------------------------------------------

def execute(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    db: str = "chat",
) -> None:
    """
    INSERT/UPDATE/DELETE işlemleri için.
    """
    conn = _get_connection(db)
    try:
        with conn:
            if params is None:
                conn.execute(sql)
            else:
                conn.execute(sql, list(params))
    finally:
        conn.close()


def executemany(
    sql: str,
    seq_of_params: Iterable[Iterable[Any]],
    db: str = "chat",
) -> None:
    """
    Çoklu INSERT/UPDATE için.
    """
    conn = _get_connection(db)
    try:
        with conn:
            conn.executemany(sql, [list(p) for p in seq_of_params])
    finally:
        conn.close()


def fetch_one(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    db: str = "chat",
) -> Optional[sqlite3.Row]:
    """
    Tek bir satır döndürür (veya None).
    """
    conn = _get_connection(db)
    try:
        cur = conn.cursor()
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql, list(params))
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def fetch_all(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    db: str = "chat",
) -> List[sqlite3.Row]:
    """
    Çoklu satır döndürür (liste).
    """
    conn = _get_connection(db)
    try:
        cur = conn.cursor()
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql, list(params))
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def fetch_val(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    db: str = "chat",
) -> Optional[Any]:
    """
    Tek bir hücre (ilk satırın ilk kolonu) döndürür.
    """
    row = fetch_one(sql, params=params, db=db)
    if not row:
        return None
    # row[0] ile ilk kolonu alıyoruz
    return row[0]
    

# ---------------------------------------------------------------------------
# DB Şema oluşturma
# ---------------------------------------------------------------------------

def _init_chat_db() -> None:
    """
    chat_history.db şeması.
    """
    conn = _get_connection("chat")
    try:
        cur = conn.cursor()

        # Mesajlar
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                role TEXT,
                mode TEXT,
                intent TEXT,
                sentiment TEXT,
                emotion TEXT,
                emotion_intensity REAL,
                importance_score REAL,
                is_sensitive INTEGER,
                topic TEXT,
                content TEXT,
                created_at TEXT,
                metadata_json TEXT
            );
            """
        )

        # Eski şemadan gelen tablolar için güvenlik:
        # Önceden oluşturulmuş tablolarda eksik kolon varsa tek seferde hepsini ekle
        _ensure_column(conn, "chat_messages", "mode", "TEXT")
        _ensure_column(conn, "chat_messages", "intent", "TEXT")
        _ensure_column(conn, "chat_messages", "sentiment", "TEXT")
        _ensure_column(conn, "chat_messages", "emotion", "TEXT")
        _ensure_column(conn, "chat_messages", "emotion_intensity", "REAL")
        _ensure_column(conn, "chat_messages", "importance_score", "REAL")
        _ensure_column(conn, "chat_messages", "is_sensitive", "INTEGER")
        _ensure_column(conn, "chat_messages", "topic", "TEXT")
        _ensure_column(conn, "chat_messages", "metadata_json", "TEXT")

        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);"
        )

        # Mood log
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                message_id INTEGER,
                timestamp TEXT,
                sentiment TEXT,
                emotion TEXT,
                intensity REAL,
                topic TEXT,
                summary TEXT
            );
            """
        )

        # Reflections
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                reflection_type TEXT,
                created_at TEXT,
                period_start TEXT,
                period_end TEXT,
                observation TEXT,
                suggestions TEXT,
                user_feedback TEXT
            );
            """
        )

        # Hatırlatmalar
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                trigger_at TEXT,
                recurrence TEXT,
                status TEXT,
                category TEXT
            );
            """
        )

        conn.commit()
    finally:
        conn.close()



def _init_knowledge_db() -> None:
    """
    knowledge.db şeması.
    """
    conn = _get_connection("knowledge")
    try:
        cur = conn.cursor()

        # Dokümanlar
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                filename TEXT,
                collection TEXT,
                language TEXT,
                size INTEGER,
                content_type TEXT,
                created_at TEXT
            );
            """
        )

        # Metin chunk'ları
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT,
                chunk_index INTEGER,
                text TEXT,
                language TEXT,
                created_at TEXT,
                embedding BLOB
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);"
        )

        # Basit key-value istatistik
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )

        conn.commit()
    finally:
        conn.close()


def _init_profile_db() -> None:
    """
    profile.db şeması.
    """
    conn = _get_connection("profile")
    try:
        cur = conn.cursor()

        # Kullanıcı profilleri
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                created_at TEXT,
                updated_at TEXT,
                age INTEGER,
                gender TEXT,
                location TEXT,
                occupation TEXT,
                interests TEXT,
                preferences_json TEXT,
                notes TEXT
            );
            """
        )

        # Kullanıcı hedefleri
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                category TEXT,
                is_active INTEGER,
                progress REAL
            );
            """
        )

        conn.commit()
    finally:
        conn.close()


def init_databases() -> None:
    """
    Uygulama başlarken çağrılır (main.py içinde).
    Gerekli klasörleri ve tabloları oluşturur.
    """
    # Klasörleri oluştur
    settings.db.data_dir.mkdir(parents=True, exist_ok=True)
    settings.db.files_dir.mkdir(parents=True, exist_ok=True)
    settings.db.cache_dir.mkdir(parents=True, exist_ok=True)

    _init_chat_db()
    _init_knowledge_db()
    _init_profile_db()
