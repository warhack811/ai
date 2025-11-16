"""
schemas/common.py
------------------
Projede tekrar tekrar kullanılacak ortak Pydantic şemaları ve enum benzeri tipler:

- Rol tipleri (user / assistant / system)
- Modlar (normal, research, creative, code, teacher, friend vs.)
- Mesaj, kaynak (source), hata yapıları
- Basit API cevap şablonları
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Temel Enum / Literal Tipleri
# ---------------------------------------------------------------------------

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMode(str, Enum):
    NORMAL = "normal"
    RESEARCH = "research"
    CREATIVE = "creative"
    CODE = "code"
    TEACHER = "teacher"
    FRIEND = "friend"
    TURKISH_TEACHER = "turkish_teacher"  # TR dil bilgisi modu


class MessageOrigin(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"  # ileride tool çağrıları için


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class EmotionLabel(str, Enum):
    """Daha detaylı duygu etiketleri."""
    NONE = "none"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    TIRED = "tired"
    STRESSED = "stressed"
    RELIEVED = "relieved"
    LONELY = "lonely"
    EXCITED = "excited"
    BORED = "bored"
    CONFUSED = "confused"


class IntentLabel(str, Enum):
    """Mesajın temel niyeti / amacı."""
    SMALL_TALK = "small_talk"
    QUESTION = "question"
    TASK_REQUEST = "task_request"
    EXPLAIN = "explain"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    CODE_HELP = "code_help"
    EMOTIONAL_SUPPORT = "emotional_support"
    REFLECTION = "reflection"
    REMINDER_CREATE = "reminder_create"
    REMINDER_QUERY = "reminder_query"
    PROFILE_UPDATE = "profile_update"
    DOCUMENT_QUESTION = "document_question"
    WEB_SEARCH = "web_search"
    
    # ============ YENİ EKLEMELER (Semantic Intent Detector için) ============
    CLARIFICATION_REQUEST = "clarification_request"  # "Anlamadım, açıklar mısın?"
    FOLLOW_UP = "follow_up"                          # "Peki, o zaman..."
    COMPARE = "compare"                              # "X ile Y arasındaki fark?"
    RECOMMENDATION = "recommendation"                # "Ne önerirsin?"
    CREATIVE = "creative"                            # Yaratıcı içerik isteği
    
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Cevapta kullanılan kaynak tipleri."""
    WEB = "web"
    DOCUMENT = "document"
    MEMORY = "memory"
    PROFILE = "profile"
    CHAT_HISTORY = "chat_history"
    TOOL = "tool"
    OTHER = "other"


class SafetyLevel(str, Enum):
    """Cevabın güvenlik açısından sınıflandırılması (ileri kullanım için)."""
    OK = "ok"
    SENSITIVE = "sensitive"
    RISKY = "risky"
    BLOCKED = "blocked"


# ---------------------------------------------------------------------------
# Ortak Şema Nesneleri
# ---------------------------------------------------------------------------

class SourceInfo(BaseModel):
    """
    Cevapta kullanılan tek bir kaynağın meta verisi.
    Frontend bu bilgiyi 'Kaynaklar' bölümünde gösterir.
    """
    type: SourceType = Field(default=SourceType.OTHER)
    title: str = Field(..., max_length=200)
    url: Optional[HttpUrl] = None
    snippet: Optional[str] = Field(
        default=None,
        description="Kaynaktan kısa bir alıntı/özet (opsiyonel)."
    )
    score: Optional[float] = Field(
        default=None,
        description="RAG / web search skorlaması (0-1 arası)."
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Ek meta veriler (document_id, page_number vs.)"
    )


class MessageMetadata(BaseModel):
    """
    Mesajla ilgili ek bilgiler; hafıza, niyet, mood sistemi için kullanılır.
    """
    mode: Optional[ChatMode] = None
    intent: Optional[IntentLabel] = None
    sentiment: Optional[SentimentLabel] = None
    emotion: Optional[EmotionLabel] = None

    # Duygu yoğunluğu (0-1)
    emotion_intensity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    # Bu mesajdan profil/hafıza çıkarımı yapmak için önem skoru (0-1)
    importance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    # Mesajın kullanıcı için hassas olup olmadığı
    is_sensitive: Optional[bool] = None

    # Konu kategorisi (iş, sağlık, ilişkiler, kod, vb.)
    topic: Optional[str] = None


class ChatMessage(BaseModel):
    """
    Sohbet içindeki tek bir mesaj.
    DB'de ve API'de kullanılacak temel format.
    """
    id: Optional[int] = Field(
        default=None,
        description="DB'de kayıtlıysa mesaj id'si."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Ait olduğu sohbet oturumunun kimliği."
    )
    role: Role
    content: str = Field(..., description="Mesaj metni.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC zaman damgası."
    )

    # Backend tarafından eklenen meta veriler
    metadata: Optional[MessageMetadata] = None

    # ✅ Pydantic v2 uyumlu config
    model_config = {
        "from_attributes": True
    }


class ChatSourceAnnotatedMessage(ChatMessage):
    """
    Özellikle asistan mesajları için:
    - Hangi kaynaklardan beslendiği
    - Güvenlik seviyesi
    gibi ek bilgiler.
    """
    sources: List[SourceInfo] = Field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.OK


# ---------------------------------------------------------------------------
# Basit API Cevap Şablonları
# ---------------------------------------------------------------------------

class APIError(BaseModel):
    """
    Hata durumunda döneceğimiz standart JSON cevap formatı.
    """
    detail: str
    code: Optional[str] = Field(
        default=None,
        description="İsteğe bağlı hata kodu (ör. RATE_LIMITED, LLM_ERROR, VALIDATION_ERROR)."
    )


class HealthStatus(BaseModel):
    """Health check endpoint cevabı."""
    status: Literal["ok", "degraded", "error"] = "ok"
    message: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[dict] = None


class StatsSummary(BaseModel):
    """
    /api/stats endpoint'i için özet istatistikler.
    Frontend'deki StatsPanel bunu kullanacak.
    """
    total_queries: int = 0
    total_documents: int = 0
    db_size: int = 0  # kayıt sayısı veya KB/MB cinsinden de yorumlanabilir
    total_scraped_sites: int = 0

    # ✅ Model bazlı istatistikler (isim değişti: model_usage → llm_usage)
    llm_usage: Optional[dict] = Field(
        default=None,
        description="{'qwen': 123, 'deepseek': 45, ...}"
    )

    # Ortalama cevap süresi (ms veya sn)
    avg_response_time_ms: Optional[float] = None
    
    # ✅ Pydantic v2 namespace uyarısını kapat
    model_config = {
        "protected_namespaces": ()
    }


# ---------------------------------------------------------------------------
# Ortak Yardımcı Fonksiyonlar (Basit)
# ---------------------------------------------------------------------------

def current_utc_timestamp() -> datetime:
    """Tek bir yerden UTC timestamp almak için yardımcı."""
    return datetime.utcnow()