"""
schemas/chat.py
----------------
Sohbet (chat) API'si, oturum yönetimi ve doküman yükleme ile ilgili
Pydantic şemaları.

Frontend ile uyumlu olacak şekilde tasarlandı:
- /api/chat POST body:
    {
      "message": "...",
      "mode": "normal" | "research" | ...,
      "use_web_search": true/false,
      "max_sources": 5,
      "temperature": 0.5,
      "max_tokens": 1500,
      "user_id": "user_...",
      "session_id": "session_..."
    }

- /api/chat response:
    {
      "response": "...",
      "sources": [...],
      "timestamp": "...",
      "mode": "...",
      "used_model": "...",
      "session_id": "...",
      "metadata": {...}
    }

Ayrıca:
- sohbet oturumu özetleri
- sohbet geçmişi
- doküman upload istek/cevap şemaları
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import (
    ChatMode,
    ChatSourceAnnotatedMessage,
    ChatMessage,
    SourceInfo,
    StatsSummary,
)


# ---------------------------------------------------------------------------
# /api/chat istek ve cevap şemaları
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """
    Frontend'den /api/chat endpoint'ine gelen istek gövdesi.
    """
    message: str = Field(..., description="Kullanıcının gönderdiği mesaj.")
    mode: ChatMode = Field(
        ChatMode.NORMAL,
        description="Sohbet modu (normal, research, creative, code, ...)."
    )
    use_web_search: bool = Field(
        True,
        description="Bu mesaj için web araması kullanılmalı mı?"
    )
    max_sources: int = Field(
        5,
        ge=0,
        le=10,
        description="Cevapta en fazla kaç kaynak (web+doküman) kullanılacak."
    )
    temperature: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="LLM temperature değeri."
    )
    max_tokens: int = Field(
        1500,
        ge=100,
        le=4096,
        description="Maksimum üretilecek token sayısı."
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Kullanıcıyı tanımlamak için istemcinin gönderdiği id."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Sohbet oturum id'si. Gönderilmezse backend yeni bir session oluşturabilir."
    )


class ChatResponse(BaseModel):
    """
    /api/chat cevabı.

    Frontend şu alanları kullanacak:
    - response (ana cevap metni)
    - sources (kaynak listesi)
    - timestamp (cevap zamanı)
    """
    response: str = Field(..., description="Asistanın cevabı (markdown destekli).")
    sources: List[SourceInfo] = Field(
        default_factory=list,
        description="Cevap için kullanılan kaynaklar (web, doküman, hafıza vs.)."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC zaman damgası."
    )

    # Ek meta alanlar (frontend isterse kullanır)
    mode: ChatMode = Field(
        default=ChatMode.NORMAL,
        description="Bu cevap hangi modda üretildi?"
    )
    used_model: Optional[str] = Field(
        default=None,
        description="Kullanılan LLM model adı (ör: qwen2.5-14b-instruct)."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Bu cevabın ait olduğu sohbet oturum id'si."
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Gelişmiş kullanım için ek meta veriler."
    )


# ---------------------------------------------------------------------------
# Sohbet oturumları ve geçmişi
# ---------------------------------------------------------------------------

class ChatSessionSummary(BaseModel):
    """
    Sohbet oturumlarının listelenmesi için özet bilgi.
    /api/sessions gibi endpoint'lerde kullanılabilir.
    """
    session_id: str
    title: Optional[str] = Field(
        default=None,
        description="Sohbet başlığı (ilk mesajdan otomatik üretilebilir)."
    )
    created_at: datetime
    updated_at: datetime

    # İstatistikler
    message_count: int = 0
    has_web_messages: bool = False
    has_documents: bool = False

    # İleride kategorileme için
    tags: List[str] = Field(default_factory=list)


class ChatSessionDetail(BaseModel):
    """
    Tek bir sohbet oturumunun detaylı bilgisi.
    """
    session: ChatSessionSummary
    messages: List[ChatSourceAnnotatedMessage] = Field(
        default_factory=list,
        description="Bu oturumdaki tüm mesajlar (user + assistant)."
    )


class ChatHistoryResponse(BaseModel):
    """
    /api/sessions/{id} gibi endpoint'ler için standart cevap.
    """
    session: ChatSessionSummary
    messages: List[ChatMessage] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Doküman yükleme (RAG için)
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    """
    Yüklenen doküman hakkında ek meta veriler.
    Ör: dosya boyutu, mime-type, koleksiyon etiketi (tarih, hukuk, kişisel vs.)
    """
    size: Optional[int] = Field(
        default=None,
        description="Dosya boyutu (byte cinsinden)."
    )
    type: Optional[str] = Field(
        default=None,
        description="İçerik türü veya MIME type (text/plain, application/pdf vs.)."
    )
    collection: Optional[str] = Field(
        default="general",
        description="RAG içinde kullanılacak koleksiyon adı (örn. TR_GRAMMAR)."
    )
    language: Optional[str] = Field(
        default=None,
        description="Dokümanın dili (örn. tr, en)."
    )


class DocumentUploadRequest(BaseModel):
    """
    /api/upload-document için istek gövdesi.
    Frontend şu anda:
      { content: text, filename: file.name, metadata: { size, type } }
    formatında gönderiyor.
    """
    content: str = Field(..., description="Dokümanın ham metin içeriği.")
    filename: str = Field(..., description="Orijinal dosya adı.")
    metadata: Optional[DocumentMetadata] = None
    user_id: Optional[str] = Field(
        default=None,
        description="İleride çok kullanıcılı senaryolar için."
    )


class DocumentUploadResponse(BaseModel):
    """
    /api/upload-document cevabı.
    """
    document_id: str = Field(..., description="Kaydedilen dokümanın benzersiz id'si.")
    chunks_created: int = Field(
        ...,
        description="Bu dokümandan oluşturulan metin parçacığı (chunk) sayısı."
    )
    collection: str = Field(..., description="Dokümanın ait olduğu koleksiyon adı.")
    message: str = Field(
        default="Doküman başarıyla yüklendi ve indekse eklendi.",
        description="Kullanıcıya gösterilecek kısa mesaj."
    )


# ---------------------------------------------------------------------------
# /api/stats için şema (common.StatsSummary kullanarak)
# ---------------------------------------------------------------------------

class StatsResponse(StatsSummary):
    """
    /api/stats endpoint'inde döneceğimiz model.
    Şimdilik StatsSummary'i direkt extend ediyoruz,
    gerekirse backend'e özel alanlar ekleyebiliriz.
    """
    pass
