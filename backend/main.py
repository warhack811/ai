"""
main.py - ULTIMATE FIX
-------
✅ OPTIONS handler route sıralaması düzeltildi
✅ Startup mesajı düzeltildi
✅ CORS kesinlikle çözüldü
"""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Request
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
from services.enhanced_pipeline import process_chat_enhanced
from services.rate_limit import rate_limiter_dependency
from services.stats_service import get_stats_summary
from services import upload_service
from starlette.middleware.base import BaseHTTPMiddleware
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
# CORS Middleware - EN ÖNCE!
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)
class CORSOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            return JSONResponse(
                content={"ok": True},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        return await call_next(request)

# CORS middleware'den SONRA ekle
app.add_middleware(CORSOptionsMiddleware)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Any, exc: HTTPException) -> JSONResponse:
    """HTTPException için standart JSON hata cevabı."""
    error = APIError(detail=exc.detail, code=str(exc.status_code))
    return JSONResponse(
        status_code=exc.status_code,
        content=error.dict(),
        headers={
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Genel exception handler"""
    import traceback
    print("=" * 60)
    print("❌ UNHANDLED ERROR:")
    print(f"Path: {request.url.path}")
    print(f"Method: {request.method}")
    print(f"Error: {exc}")
    traceback.print_exc()
    print("=" * 60)
    
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
        }
    )


# ---------------------------------------------------------------------------
# Startup/Shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Uygulama başlarken veritabanlarını oluştur"""
    init_databases()
    print("=" * 60)
    print("✅ Backend Started Successfully!")
    print(f"📡 API: http://127.0.0.1:{settings.api_port}{API_PREFIX}")
    print(f"🌐 CORS: Enabled for ALL origins")
    print(f"🚀 Enhanced Pipeline v4.0 Active")
    print("=" * 60)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    pass


# ---------------------------------------------------------------------------
# KRITIK: OPTIONS HANDLER - BÜTÜN ROUTE'LARDAN ÖNCE!
# ---------------------------------------------------------------------------

@app.api_route("/{path:path}", methods=["OPTIONS"])
async def options_handler(path: str):
    """
    CORS Preflight için OPTIONS handler
    ÖNEMLİ: Bu handler tüm route'lardan önce tanımlanmalı!
    """
    return JSONResponse(
        content={"ok": True},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Health check"""
    return HealthStatus(status="ok", message="Service is running")


@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    _: None = Depends(rate_limiter_dependency),
) -> ChatResponse:
    """
    Ana sohbet endpoint'i - Ultimate Hybrid Pipeline v4.0
    """
    print("=" * 60)
    print(f"📩 NEW CHAT REQUEST")
    print(f"Message: {payload.message[:50]}...")
    print(f"Mode: {payload.mode}")
    print("=" * 60)
    
    try:
        response = await process_chat_enhanced(payload)
        print(f"✅ Response generated: {len(response.response)} chars")
        return response
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("=" * 60)
        print("❌ CHAT ERROR:")
        print(f"Message: {e}")
        print(f"Type: {type(e).__name__}")
        traceback.print_exc()
        print("=" * 60)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e


@app.post(f"{API_PREFIX}/upload-document", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    payload: DocumentUploadRequest,
    _: None = Depends(rate_limiter_dependency),
) -> DocumentUploadResponse:
    """Doküman yükleme endpoint'i"""
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


@app.post(f"{API_PREFIX}/upload-document-file")
async def upload_document_file(
    file: UploadFile = File(...),
    user_id: str = "default",
    _: None = Depends(rate_limiter_dependency),
):
    """Doküman yükleme (file)"""
    try:
        content_bytes = await file.read()
        
        try:
            content_text = content_bytes.decode('utf-8')
        except:
            import base64
            content_text = base64.b64encode(content_bytes).decode('ascii')
            is_base64 = True
        else:
            is_base64 = False
        
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


@app.get(f"{API_PREFIX}/documents")
async def list_documents(
    user_id: str = "default",
    _: None = Depends(rate_limiter_dependency),
):
    """Doküman listesi"""
    try:
        documents = upload_service.list_user_documents(user_id)
        
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {e}") from e


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


@app.get(f"{API_PREFIX}/knowledge/stats")
async def knowledge_stats():
    """Knowledge base istatistikleri"""
    try:
        stats = upload_service.get_knowledge_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e


@app.get(f"{API_PREFIX}/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    """Genel istatistikler"""
    try:
        stats = get_stats_summary()
        return StatsResponse(**stats.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.env == "dev" else False,
    )