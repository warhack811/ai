"""
schemas/profile.py
-------------------
Kullanıcı profili, mood (duygu durumu) kayıtları, reflection (öz değerlendirme)
ve hatırlatmalar (reminders) ile ilgili Pydantic şemaları.

Bu dosya, kişisel asistan tarafının:
- seni tanıması (profil)
- duygularını ve ruh halini takip etmesi (mood log)
- son günleri/haftayı analiz etmesi (reflection)
- hatırlatmalar planlaması (reminders)

için kullanılacak temel veri yapılarını içerir.
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import EmotionLabel, SentimentLabel


# ---------------------------------------------------------------------------
# Profil ile ilgili tipler
# ---------------------------------------------------------------------------

class FormalityLevel(str, Enum):
    CASUAL = "casual"
    NEUTRAL = "neutral"
    FORMAL = "formal"


class PrivacyLevel(str, Enum):
    """Kullanıcı için hassasiyet seviyesi (ileride kullanabiliriz)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserPreference(BaseModel):
    """
    Kullanıcının tercihleri:
    - hitap şekli
    - ton
    - dil
    - proaktiflik seviyesi, vs.
    """
    language: Optional[str] = Field(
        default="tr",
        description="Tercih edilen dil (tr, en, vb.)."
    )
    formality: FormalityLevel = Field(
        default=FormalityLevel.CASUAL,
        description="Hitap şekli: samimi/normal/resmi."
    )
    allow_proactive_messages: bool = Field(
        default=True,
        description="Asistanın ara sıra kendiliğinden mesaj atmasına izin veriyor mu?"
    )
    allow_emotional_reflection: bool = Field(
        default=True,
        description="Duygusal durum değerlendirmesi yapılmasına izin veriyor mu?"
    )
    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.MEDIUM,
        description="Genel gizlilik/hassasiyet seviyesi."
    )


class UserGoal(BaseModel):
    """
    Kullanıcının hedefleri:
    - daha sağlıklı yaşam
    - düzenli spor
    - ders çalışma
    - alışkanlık bırakma, vb.
    """
    id: Optional[int] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Hedef tipi/kategorisi (sağlık, kariyer, ders, ilişki vs.)
    category: Optional[str] = None

    # Basit durum/ilerleme
    is_active: bool = True
    progress: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="0-1 arası basit progress değeri (opsiyonel)."
    )


class UserProfile(BaseModel):
    """
    Kullanıcının genel profili.
    Bu yapı asistanın seni tanıması ve kişiselleştirilmiş cevaplar vermesi için temel olacak.
    """
    user_id: str = Field(..., description="Backend'de kullanıcıyı tanımlayan id.")
    display_name: Optional[str] = Field(
        default=None,
        description="Asistanın sana nasıl hitap edeceği (adın ya da lakabın)."
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Temel bilgiler (opsiyonel, zorunlu değil)
    age: Optional[int] = None
    gender: Optional[str] = None  # 'erkek', 'kadın', 'non-binary', 'belirtmek istemiyorum', vb.
    location: Optional[str] = None  # Şehir / ülke gibi

    # Yaşam tarzı & durum
    occupation: Optional[str] = Field(
        default=None,
        description="Öğrenci, yazılımcı, işsiz, vb."
    )
    interests: List[str] = Field(
        default_factory=list,
        description="İlgi alanları (spor, oyun, tarih, yapay zeka, vb.)."
    )

    # Tercihler
    preferences: UserPreference = Field(
        default_factory=UserPreference,
        description="Hitap, dil ve gizlilik tercihleri."
    )

    # Hedefler
    goals: List[UserGoal] = Field(
        default_factory=list,
        description="Kullanıcının belirlediği uzun vadeli hedefler."
    )

    # Serbest metin not
    notes: Optional[str] = Field(
        default=None,
        description="Asistanın kullanıcı hakkında tuttuğu özet not (kısa profil özeti gibi)."
    )


# ---------------------------------------------------------------------------
# Mood / Emotion log (duygu günlüğü)
# ---------------------------------------------------------------------------

class MoodLog(BaseModel):
    """
    Tek bir mood/duygu kaydı.
    Mesajlar üzerinden çıkarılan duyguları ve konuları saklar.
    """
    id: Optional[int] = None
    user_id: str
    session_id: Optional[str] = None
    message_id: Optional[int] = None  # Chat mesaj id'sine bağlanabilir

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    sentiment: SentimentLabel = SentimentLabel.UNKNOWN
    emotion: EmotionLabel = EmotionLabel.NONE
    intensity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Duygu yoğunluğu (0-1)."
    )

    # Konu kategorisi (iş, okul, aile, ilişki, sağlık, gelecek, öz-benlik, vb.)
    topic: Optional[str] = None

    # Serbest not: asistan kısa bir özet kaydedebilir
    summary: Optional[str] = Field(
        default=None,
        description="Bu mood kaydının kısa özeti (asistan tarafından üretilebilir)."
    )


class MoodSummary(BaseModel):
    """
    Belirli bir tarih aralığı için mood özeti.
    Örneğin reflection engine haftalık analiz yaparken bunu kullanabilir.
    """
    user_id: str
    from_date: date
    to_date: date

    # Basit istatistikler
    total_logs: int = 0
    dominant_emotions: Dict[str, int] = Field(
        default_factory=dict,
        description="EmotionLabel -> adet"
    )
    dominant_topics: Dict[str, int] = Field(
        default_factory=dict,
        description="Konu -> adet"
    )

    # Genel yorum/özet
    overall_sentiment: SentimentLabel = SentimentLabel.UNKNOWN
    notes: Optional[str] = Field(
        default=None,
        description="Asistanın bu dönem için ürettiği kısa özet."
    )


# ---------------------------------------------------------------------------
# Reflection (öz değerlendirme) şemaları
# ---------------------------------------------------------------------------

class ReflectionType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ReflectionEntry(BaseModel):
    """
    Kullanıcıyla paylaşılan tek bir reflection (öz değerlendirme) kaydı.
    Asistan belirli aralıklarla 'Bu hafta böyle hissediyor gibisin' gibi
    gözlemlerini buraya kaydedebilir.
    """
    id: Optional[int] = None
    user_id: str

    reflection_type: ReflectionType = ReflectionType.WEEKLY
    created_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Mood/goal kaynaklı bulgular
    mood_summary: Optional[MoodSummary] = None

    # Asistanın kullanıcıya sunduğu gözlem ve öneriler
    observation: str = Field(
        ...,
        description="Asistanın genel gözlemi (nasıl bir period geçti, neler dikkat çekti)."
    )
    suggestions: Optional[str] = Field(
        default=None,
        description="Kullanıcıya verilen öneriler (daha fazla dinlen, plan yap, vb.)."
    )

    # Kullanıcının reflection'a verdiği tepki/yanıt (isterse doldurur)
    user_feedback: Optional[str] = None


# ---------------------------------------------------------------------------
# Hatırlatmalar (Reminders)
# ---------------------------------------------------------------------------

class ReminderStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"
    CANCELLED = "cancelled"


class Reminder(BaseModel):
    """
    Basit bir hatırlatma kaydı.
    Örn: 'Her gün 22:00'de kitap oku' / 'Yarın 14:00'te doktor randevun var'.
    """
    id: Optional[int] = None
    user_id: str

    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Ne zaman tetiklenecek?
    # Basit ilk versiyon: single datetime
    trigger_at: Optional[datetime] = Field(
        default=None,
        description="Tek seferlik hatırlatma zamanı."
    )

    # İleri seviye: tekrar eden (cron benzeri) hatırlatmalar için
    recurrence: Optional[str] = Field(
        default=None,
        description="Tekrarlama kuralı (örneğin: 'daily', 'weekly', 'cron:0 21 * * *')."
    )

    status: ReminderStatus = ReminderStatus.ACTIVE

    # Hangi kategoriye ait?
    category: Optional[str] = Field(
        default=None,
        description="Hedef/alan bazlı kategori: sağlık, ders, iş, kişisel, vb."
    )


class ReminderCreateRequest(BaseModel):
    """
    Hatırlatma oluşturma isteği için şema.
    Bu API'yi hem sohbet içinden hem ayarlar panelinden kullanabiliriz.
    """
    user_id: str
    title: str
    description: Optional[str] = None

    trigger_at: Optional[datetime] = None
    recurrence: Optional[str] = None
    category: Optional[str] = None


class ReminderListResponse(BaseModel):
    """
    /api/reminders gibi bir endpoint'te dönebileceğimiz liste formatı.
    """
    reminders: List[Reminder] = Field(default_factory=list)
