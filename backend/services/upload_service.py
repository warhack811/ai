"""
services/upload_service.py
--------------------------
Doküman yükleme ve indeksleme servisi.

Akış:
1. Frontend'ten DocumentUploadRequest gelir (content + filename + metadata).
2. Benzersiz bir document_id oluşturulur.
3. knowledge servisine indeksleme için paslanır:
   - doküman meta kaydı
   - chunk'lara bölme
   - embedding hesaplama (knowledge modülünde)
4. Kullanıcıya DocumentUploadResponse dönülür.
"""

from __future__ import annotations

from datetime import datetime
from typing import Tuple
from uuid import uuid4

from schemas.chat import DocumentUploadRequest, DocumentUploadResponse
from schemas.chat import DocumentMetadata  # type: ignore
from services import knowledge


async def process_uploaded_document(
    payload: DocumentUploadRequest,
) -> DocumentUploadResponse:
    """
    Doküman yükleme iş akışı.
    """
    user_id = payload.user_id or "anonymous"
    metadata = payload.metadata or DocumentMetadata()
    collection = metadata.collection or "general"
    language = metadata.language or "tr"

    document_id = uuid4().hex

    # knowledge servisine indeksleme için pasla
    # Bu fonksiyonun imzasını knowledge.py tarafında buna göre tasarlayacağız:
    #   async def index_document(
    #       document_id: str,
    #       user_id: str,
    #       filename: str,
    #       content: str,
    #       collection: str,
    #       language: str,
    #       size: int | None,
    #       content_type: str | None,
    #   ) -> int:  # chunks_created
    size = metadata.size if metadata.size is not None else len(payload.content.encode("utf-8"))
    content_type = metadata.type or "text/plain"

    chunks_created = await knowledge.index_document(
        document_id=document_id,
        user_id=user_id,
        filename=payload.filename,
        content=payload.content,
        collection=collection,
        language=language,
        size=size,
        content_type=content_type,
    )

    # Kullanıcıya cevap
    return DocumentUploadResponse(
        document_id=document_id,
        chunks_created=chunks_created,
        collection=collection,
        message="Doküman başarıyla yüklendi ve indekse eklendi.",
    )
