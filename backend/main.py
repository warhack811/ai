# -*- coding: utf-8 -*-
"""
main.py - UTF-8 ENCODING FIXED
-------------------------------
✅ UTF-8 encoding eklendi
✅ Türkçe karakter sorunu çözüldü
"""

import logging
from typing import Any
import uuid
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from services.ultimate_chat_engine import get_chat_engine, ChatMode
from config import get_settings
from schemas.chat import (
    ChatRequest,
    ChatResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    StatsResponse,
)
from schemas.common import APIError, HealthStatus
from services.db import init_databases
from services.pipeline import process_chat
from services.rate_limit import rate_limiter_dependency
from services.stats_service import get_stats_summary
from services import upload_service

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.env == "dev" else None,
    redoc_url="/redoc" if settings.env == "dev" else None,
    openapi_url="/openapi.json" if settings.env == "dev" else None,
)

API_PREFIX = settings.api_root_path or "/api"

# ============================================
# LOGGER KURULUMU
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS Ayarları
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Any, exc: HTTPException) -> JSONResponse:
    """HTTPException için standart JSON hata cevabı."""
    error = APIError(detail=exc.detail, code=str(exc.status_code))
    return JSONResponse(
        status_code=exc.status_code,
        content=error.dict(),
        media_type="application/json; charset=utf-8",  # ✅ UTF-8 eklendi
    )


# ---------------------------------------------------------------------------
# Uygulama Başlangıcı / Kapanışı
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Uygulama başlarken veritabanlarını oluştur"""
    init_databases()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Uygulama kapanırken yapılacak işler"""
    pass


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Basit health check endpoint'i"""
    return HealthStatus(status="ok", message="Service is running")


# ---------------------------------------------------------------------------
# /api/chat - Ana Sohbet Endpoint'i (FIXED)
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    ANA CHAT ENDPOINT
    """
    try:
        # Session ID oluştur
        session_id = request.session_id or str(uuid.uuid4())
        
        # Mode dönüşümü
        mode_map = {
            "normal": ChatMode.NORMAL,
            "research": ChatMode.RESEARCH,
            "creative": ChatMode.CREATIVE,
            "code": ChatMode.CODE,
            "friend": ChatMode.FRIEND,
            "uncensored": ChatMode.UNCENSORED  # YENİ: Sansürsüz mod
        }
        mode = mode_map.get(request.mode, ChatMode.NORMAL)
        
        # Engine'i al
        engine = get_chat_engine()
        
        # Chat işle
        logger.info(f"Chat isteği: {request.message[:50]}... (mode: {mode})")
        
        response = await engine.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id,
            mode=mode,
            history=request.conversation_history
        )
        
        logger.info(f"Chat tamamlandı: {response.time:.2f}s, model: {response.model}")
        
        # Response döndür
        return ChatResponse(
            response=response.content,
            session_id=session_id,
            model_used=response.model,
            processing_time=response.time,
            quality_score=response.quality_score,
            intent=response.intent
        )
    
    except Exception as e:
        logger.error(f"❌ Chat hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /api/upload-document - Doküman Yükleme (TEXT/BASE64)
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/upload-document", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    payload: DocumentUploadRequest,
    _: None = Depends(rate_limiter_dependency),
) -> DocumentUploadResponse:
    """
    Doküman yükleme endpoint'i (text veya base64)
    """
    try:
        metadata = payload.metadata or {}
        content_type = metadata.get('type', 'text/plain')
        user_id = payload.user_id or "default"
        
        result = upload_service.process_document_upload(
            filename=payload.filename,
            content=payload.content,
            content_type=content_type,
            user_id=user_id,
            is_base64=False,
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
        
        return DocumentUploadResponse(
            status=result['status'],
            doc_id=result.get('doc_id'),
            chunks_count=result.get('chunks_added', 0),
            filename=result['filename'],
            error=result.get('error'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}") from e


# ---------------------------------------------------------------------------
# /api/upload-document-file - Doküman Yükleme (FILE)
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/upload-document-file")
async def upload_document_file(
    file: UploadFile = File(...),
    user_id: str = "default",
    _: None = Depends(rate_limiter_dependency),
):
    """
    Doküman yükleme endpoint'i (multipart/form-data)
    """
    try:
        content_bytes = await file.read()
        
        try:
            content_text = content_bytes.decode('utf-8')
            is_base64 = False
        except:
            import base64
            content_text = base64.b64encode(content_bytes).decode('ascii')
            is_base64 = True
        
        result = upload_service.process_document_upload(
            filename=file.filename,
            content=content_text,
            content_type=file.content_type or 'application/octet-stream',
            user_id=user_id,
            is_base64=is_base64,
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload error: {e}") from e


# ---------------------------------------------------------------------------
# /api/documents - Doküman Listesi
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/documents")
async def list_documents(
    user_id: str = "default",
    _: None = Depends(rate_limiter_dependency),
):
    """Kullanıcının dokümanlarını listele"""
    try:
        documents = upload_service.list_user_documents(user_id)
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {e}") from e


# ---------------------------------------------------------------------------
# /api/documents/{doc_id} - Doküman Sil
# ---------------------------------------------------------------------------

@app.delete(f"{API_PREFIX}/documents/{{doc_id}}")
async def delete_document(
    doc_id: str,
    _: None = Depends(rate_limiter_dependency),
):
    """Doküman sil"""
    try:
        result = upload_service.delete_document_by_id(doc_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=404, detail="Document not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {e}") from e


# ---------------------------------------------------------------------------
# /api/knowledge/stats - Knowledge Base İstatistikleri
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/knowledge/stats")
async def knowledge_stats():
    """Knowledge base istatistikleri"""
    try:
        stats = upload_service.get_knowledge_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e


# ---------------------------------------------------------------------------
# /api/stats - Genel İstatistikler
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    """Genel istatistik endpoint'i"""
    try:
        stats = get_stats_summary()
        return StatsResponse(**stats.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e

@app.get("/api/learning/stats")
async def learning_stats():
    """Learning system stats"""
    try:
        from services.adaptive_learning_system import get_learning_stats
        stats = get_learning_stats()
        return stats
    except Exception as e:
        logger.error(f"Learning stats error: {e}")
        return {
            "total_events": 0,
            "positive": 0,
            "negative": 0,
            "by_model": {},
            "error": str(e)
        }
# ---------------------------------------------------------------------------
# Direkt çalıştırma
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.env == "dev" else False,
    )
