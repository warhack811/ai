"""
services/profile_service.py
---------------------------
Kullanıcı profilini yönetir:

- user_profiles tablosuyla çalışır
- Kullanıcı profilini getirir/oluşturur
- Mesajlardan profil güncellemeleri çıkarır (ad, yaş, şehir, ilgi alanları)
- Profil özet metni üretir (memory.build_long_term_context_text için)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Optional

from schemas.profile import (
    UserProfile,
    UserPreference,
    UserGoal,
)
from schemas.common import SentimentLabel, EmotionLabel, IntentLabel, ChatMessage
from services.db import fetch_one, execute


# ---------------------------------------------------------------------------
# Yardımcı Dönüşümler
# ---------------------------------------------------------------------------

def _row_to_profile(row: dict) -> UserProfile:
    interests = []
    if row.get("interests"):
        try:
            interests = json.loads(row["interests"])
        except Exception:
            interests = []

    prefs = UserPreference()
    if row.get("preferences_json"):
        try:
            prefs = UserPreference.parse_raw(row["preferences_json"])
        except Exception:
            prefs = UserPreference()

    profile = UserProfile(
        user_id=row["user_id"],
        display_name=row.get("display_name"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        age=row.get("age"),
        gender=row.get("gender"),
        location=row.get("location"),
        occupation=row.get("occupation"),
        interests=interests,
        preferences=prefs,
        notes=row.get("notes"),
        goals=[],
    )
    return profile


# ---------------------------------------------------------------------------
# Get / Create / Save
# ---------------------------------------------------------------------------

def get_profile(user_id: str) -> Optional[UserProfile]:
    row = fetch_one(
        "SELECT * FROM user_profiles WHERE user_id = ?;",
        params=[user_id],
        db="profile",
    )
    if not row:
        return None
    return _row_to_profile(row)


def create_profile(user_id: str) -> UserProfile:
    now = datetime.utcnow().isoformat()
    prefs = UserPreference()
    execute(
        """
        INSERT INTO user_profiles (
            user_id, display_name, created_at, updated_at,
            age, gender, location, occupation,
            interests, preferences_json, notes
        )
        VALUES (?, NULL, ?, ?, NULL, NULL, NULL, NULL, ?, ?, NULL);
        """,
        params=[
            user_id,
            now,
            now,
            json.dumps([]),
            prefs.json(),
        ],
        db="profile",
    )
    row = fetch_one(
        "SELECT * FROM user_profiles WHERE user_id = ?;",
        params=[user_id],
        db="profile",
    )
    return _row_to_profile(row)


def get_or_create_profile(user_id: str) -> UserProfile:
    profile = get_profile(user_id)
    if profile:
        return profile
    return create_profile(user_id)


def save_profile(profile: UserProfile) -> None:
    now = datetime.utcnow().isoformat()
    interests_json = json.dumps(profile.interests or [])
    prefs_json = profile.preferences.json()

    execute(
        """
        UPDATE user_profiles
        SET
            display_name = ?,
            updated_at = ?,
            age = ?,
            gender = ?,
            location = ?,
            occupation = ?,
            interests = ?,
            preferences_json = ?,
            notes = ?
        WHERE user_id = ?;
        """,
        params=[
            profile.display_name,
            now,
            profile.age,
            profile.gender,
            profile.location,
            profile.occupation,
            interests_json,
            prefs_json,
            profile.notes,
            profile.user_id,
        ],
        db="profile",
    )


# ---------------------------------------------------------------------------
# Profil Özeti
# ---------------------------------------------------------------------------

def get_profile_summary(user_id: str) -> str:
    """
    Kullanıcı profilini kısa bir metin olarak özetler.
    """
    profile = get_profile(user_id)
    if not profile:
        return ""

    parts = []
    if profile.display_name:
        parts.append(f"İsim: {profile.display_name}")
    if profile.age:
        parts.append(f"Yaş: {profile.age}")
    if profile.location:
        parts.append(f"Konum: {profile.location}")
    if profile.occupation:
        parts.append(f"Durum: {profile.occupation}")
    if profile.interests:
        parts.append("İlgi alanları: " + ", ".join(profile.interests[:8]))

    if profile.notes:
        parts.append("Notlar: " + profile.notes[:300])

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Mesajlardan Profil Güncelleme
# ---------------------------------------------------------------------------

def _extract_name(text: str) -> Optional[str]:
    """
    'Benim adım Ahmet', 'Adım Murat' gibi kalıplardan isim çekmeye çalışır.
    Çok kaba ama başlangıç için yeterli.
    """
    m = re.search(r"adım\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()
    return None


def _extract_age(text: str) -> Optional[int]:
    m = re.search(r"(\d{1,2})\s*yaşındayım", text)
    if m:
        try:
            val = int(m.group(1))
            if 5 < val < 100:
                return val
        except Exception:
            return None
    return None


def _extract_location(text: str) -> Optional[str]:
    m = re.search(r"(.+?)\s*(\'de|de|da|\'da)\s+yaşıyorum", text)
    if m:
        loc = m.group(1).strip()
        if len(loc) < 40:
            return loc.title()
    return None


def update_profile_from_message(
    user_id: str,
    message: ChatMessage,
    intent: IntentLabel,
    sentiment: SentimentLabel,
    emotion: EmotionLabel,
) -> None:
    """
    Kullanıcının mesajından profil için anlamlı bilgiler çıkarır.
    """
    text = message.content.strip()
    if not text:
        return

    profile = get_or_create_profile(user_id)
    changed = False

    # İsim
    name = _extract_name(text)
    if name and not profile.display_name:
        profile.display_name = name
        changed = True

    # Yaş
    age = _extract_age(text)
    if age and not profile.age:
        profile.age = age
        changed = True

    # Konum
    loc = _extract_location(text)
    if loc and not profile.location:
        profile.location = loc
        changed = True

    # İlgi alanları: intent/document vs. ile tahminen eklenebilir
    # Basitçe: kod sorularında "yazılım" ilgisi ekleyelim
    if intent == IntentLabel.CODE_HELP and "yazılım" not in profile.interests:
        profile.interests.append("yazılım")
        changed = True

    if changed:
        save_profile(profile)


# ---------------------------------------------------------------------------
# Profil Notlarını Zenginleştirme (Memory için)
# ---------------------------------------------------------------------------

def maybe_enrich_profile_notes(
    user_id: str,
    user_message: ChatMessage,
    assistant_message: ChatMessage,
) -> None:
    """
    Zamanla profil.notes alanını doğal bir "kısa biyografi" gibi doldurur.
    Burada sadece çok kaba bir yaklaşım uyguluyoruz.
    """
    profile = get_or_create_profile(user_id)

    # Çok uzun olmasını istemiyoruz
    if profile.notes and len(profile.notes) > 1500:
        return

    # Önemli sayılabilecek mesajlar için not al
    if user_message.metadata and (user_message.metadata.importance_score or 0) > 0.7:
        snippet = user_message.content.strip()
        snippet = snippet.replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."

        note_line = f"- Kullanıcı bir noktada şöyle demişti: \"{snippet}\""
        if profile.notes:
            profile.notes += "\n" + note_line
        else:
            profile.notes = note_line

        save_profile(profile)
