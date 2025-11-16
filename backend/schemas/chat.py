"""
schemas/chat.py - FAS 2 VERSION
----------------
✅ DocumentUploadResponse güncellendi
✅ Diğer şemalar korundu
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from enum import Enum
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
    """Frontend'den /api/chat endpoint'ine gelen istek gövdesi."""
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
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="(Frontend tarafından gönderilen) son konuşma geçmişi. Liste ChatMessage tipinde olmalı."
    )
    safety_level: int = Field(default=0, ge=0, le=2)  # 0=sansürsüz, 1=dengeli, 2=güvenli


class ChatResponse(BaseModel):
    """
    /api/chat cevabı.
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
    """Sohbet oturumlarının listelenmesi için özet bilgi."""
    session_id: str
    title: Optional[str] = Field(
        default=None,
        description="Sohbet başlığı (ilk mesajdan otomatik üretilebilir)."
    )
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    has_web_messages: bool = False
    has_documents: bool = False
    tags: List[str] = Field(default_factory=list)


class ChatSessionDetail(BaseModel):
    """Tek bir sohbet oturumunun detaylı bilgisi."""
    session: ChatSessionSummary
    messages: List[ChatSourceAnnotatedMessage] = Field(
        default_factory=list,
        description="Bu oturumdaki tüm mesajlar (user + assistant)."
    )


class ChatHistoryResponse(BaseModel):
    """/api/sessions/{id} gibi endpoint'ler için standart cevap."""
    session: ChatSessionSummary
    messages: List[ChatMessage] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Doküman yükleme (RAG için) - FAS 2 UPDATED
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    """Yüklenen doküman hakkında ek meta veriler."""
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
    
    Frontend format:
    {
        "content": "dosya içeriği...",
        "filename": "ornek.txt",
        "metadata": {"size": 1234, "type": "text/plain"}
    }
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
    /api/upload-document cevabı - FAS 2 UPDATED
    
    Backend'den dönen format:
    {
        "status": "success" | "error",
        "doc_id": "doc_123...",
        "chunks_count": 15,
        "filename": "ornek.txt",
        "error": "..." (if error)
    }
    """
    status: str = Field(..., description="Upload durumu (success/error)")
    doc_id: Optional[str] = Field(
        default=None,
        description="Kaydedilen dokümanın benzersiz id'si."
    )
    chunks_count: Optional[int] = Field(
        default=None,
        description="Bu dokümandan oluşturulan chunk sayısı."
    )
    filename: str = Field(..., description="Dosya adı")
    error: Optional[str] = Field(
        default=None,
        description="Hata mesajı (eğer status=error ise)"
    )


# ---------------------------------------------------------------------------
# /api/stats için şema
# ---------------------------------------------------------------------------

class StatsResponse(StatsSummary):
    """
    /api/stats endpoint'inde döneceğimiz model.
    """
    pass