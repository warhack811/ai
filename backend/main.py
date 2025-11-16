"""
main.py - WORKING VERSION WITH CORS
"""

from typing import Any
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from schemas.chat import ChatRequest, ChatResponse, DocumentUploadRequest, DocumentUploadResponse, StatsResponse
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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

API_PREFIX = "/api"

# CORS - MUST BE BEFORE ROUTES
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": str(exc.status_code)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.on_event("startup")
async def on_startup() -> None:
    init_databases()

@app.get(f"{API_PREFIX}/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, _: None = Depends(rate_limiter_dependency)) -> ChatResponse:
    try:
        response = await process_chat(payload)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e

@app.post(f"{API_PREFIX}/upload-document", response_model=DocumentUploadResponse)
async def upload_document_endpoint(payload: DocumentUploadRequest, _: None = Depends(rate_limiter_dependency)) -> DocumentUploadResponse:
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
async def upload_document_file(file: UploadFile = File(...), user_id: str = "default", _: None = Depends(rate_limiter_dependency)):
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

@app.get(f"{API_PREFIX}/documents")
async def list_documents(user_id: str = "default", _: None = Depends(rate_limiter_dependency)):
    try:
        documents = upload_service.list_user_documents(user_id)
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {e}") from e

@app.delete(f"{API_PREFIX}/documents/{{doc_id}}")
async def delete_document(doc_id: str, _: None = Depends(rate_limiter_dependency)):
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
    try:
        stats = upload_service.get_knowledge_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e

@app.get(f"{API_PREFIX}/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    try:
        stats = get_stats_summary()
        return StatsResponse(**stats.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)