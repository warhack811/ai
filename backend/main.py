"""
main.py - FAS 2 COMPLETE VERSION
-------
✅ Tüm import hataları düzeltildi
✅ Upload endpoint'leri eklendi
✅ Mevcut endpoint'ler korundu
"""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from fastapi.responses import StreamingResponse
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.env == "dev" else None,
    redoc_url="/redoc" if settings.env == "dev" else None,
    openapi_url="/openapi.json" if settings.env == "dev" else None,
)

API_PREFIX = settings.api_root_path or "/api"


# ---------------------------------------------------------------------------
# CORS Ayarları
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: prod'da daralt
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
# /api/chat - Ana Sohbet Endpoint'i
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    _: None = Depends(rate_limiter_dependency),
) -> ChatResponse:
    """
    Ana sohbet endpoint'i
    """
    try:
        response = await process_chat(payload)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e


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
    
    Frontend'den gelen format:
    {
        "content": "dosya içeriği...",
        "filename": "ornek.txt",
        "metadata": {"size": 1234, "type": "text/plain"}
    }
    """
    try:
        # Metadata'dan bilgileri çek
        metadata = payload.metadata or {}
        content_type = metadata.get('type', 'text/plain')
        user_id = payload.user_id or "default"
        
        # Process document
        result = upload_service.process_document_upload(
            filename=payload.filename,
            content=payload.content,
            content_type=content_type,
            user_id=user_id,
            is_base64=False,  # Frontend text olarak gönderiyor
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
    
    Frontend'den file input ile gönderilir
    """
    try:
        # File content oku
        content_bytes = await file.read()
        
        # Text olarak decode et
        try:
            content_text = content_bytes.decode('utf-8')
        except:
            # Binary ise base64'e çevir
            import base64
            content_text = base64.b64encode(content_bytes).decode('ascii')
            is_base64 = True
        else:
            is_base64 = False
        
        # Process
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
    """
    Kullanıcının dokümanlarını listele
    """
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
    """
    Doküman sil
    """
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
    """
    Knowledge base istatistikleri
    """
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
    """
    Genel istatistik endpoint'i
    """
    try:
        stats = get_stats_summary()
        return StatsResponse(**stats.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e


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