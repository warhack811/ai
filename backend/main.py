"""
main.py
-------
FastAPI uygulamasının giriş noktası.

- Uygulama ve CORS ayarları
- Health check
- /api/chat   -> sohbet endpoint'i
- /api/stats  -> istatistikler
- /api/upload-document -> doküman yükleme (RAG için)

Frontend ile uyumlu olacak şekilde tasarlanmıştır.
"""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException
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
from services.upload_service import process_uploaded_document

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.env == "dev" else None,
    redoc_url="/redoc" if settings.env == "dev" else None,
    openapi_url="/openapi.json" if settings.env == "dev" else None,
)

# FastAPI root_path ile API'yi /api altına almak yerine,
# router path'lerinde /api prefix kullanacağız.
API_PREFIX = settings.api_root_path or "/api"


# ---------------------------------------------------------------------------
# CORS Ayarları
# ---------------------------------------------------------------------------

# Şimdilik her yerden erişime izin veriyoruz (geliştirme için).
# İleride sadece belirli origin'lere izin verebilirsin (örn: http://localhost:3000, Android app vs.).
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
    """
    Uygulama başlarken:
    - Veritabanlarını oluştur
    - Gerekli klasörleri hazırla (config.get_settings zaten klasörleri yaratıyor)
    """
    init_databases()
    # İleride: model health check, web_search health check vs. eklenebilir.


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    Uygulama kapanırken yapılacak işler (şimdilik boş).
    İleride:
    - açık bağlantıları kapatma
    - log flush, vs.
    için kullanılabilir.
    """
    pass


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Basit health check endpoint'i.
    Frontend veya monitoring aracı 'servis ayakta mı?' diye sorabilir.
    """
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
    Ana sohbet endpoint'i.

    Frontend halihazırda bu formda istek atıyor:
    {
      "message": "...",
      "mode": "normal",
      "use_web_search": true,
      "max_sources": 5,
      "temperature": 0.5,
      "max_tokens": 1500,
      "user_id": "user_...",
      "session_id": "session_..."
    }
    """
    try:
        response = await process_chat(payload)
        return response
    except HTTPException:
        # Global handler yakalayacak
        raise
    except Exception as e:
        # Beklenmeyen hatalar için 500 dön
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e


# ---------------------------------------------------------------------------
# /api/upload-document - Doküman Yükleme Endpoint'i
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/upload-document", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    payload: DocumentUploadRequest,
    _: None = Depends(rate_limiter_dependency),
) -> DocumentUploadResponse:
    """
    Doküman yükleme endpoint'i.

    Frontend şu anda:
      {
        "content": "dosyanın metni...",
        "filename": "ornek.txt",
        "metadata": {
          "size": 1234,
          "type": "text/plain"
        }
      }
    formatında istek gönderiyor.
    """
    try:
        result = await process_uploaded_document(payload)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}") from e


# ---------------------------------------------------------------------------
# /api/stats - İstatistik Endpoint'i
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    """
    İstatistik endpoint'i.

    Frontend StatsPanel, burada dönen değerleri gösteriyor:
    - total_queries
    - total_documents
    - db_size
    - total_scraped_sites
    - model_usage (opsiyonel)
    """
    try:
        stats = get_stats_summary()
        # StatsService StatsSummary döndürecek, biz direkt StatsResponse'e uyuyoruz
        return StatsResponse(**stats.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e


# ---------------------------------------------------------------------------
# Eğer direkt 'python main.py' ile çalıştırmak istersen:
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.env == "dev" else False,
    )
