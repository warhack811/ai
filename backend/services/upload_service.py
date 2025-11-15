"""
services/upload_service.py - FAS 2 VERSION
--------------------------
✅ Document upload processing
✅ PDF & TXT support
✅ Base64 decoding
✅ ChromaDB integration
"""

import logging
import base64
from typing import Dict, Optional
from pathlib import Path
import tempfile

from services import knowledge

logger = logging.getLogger(__name__)


def process_document_upload(
    filename: str,
    content: str,
    content_type: str,
    user_id: str = "default",
    is_base64: bool = False,
) -> Dict:
    """
    Doküman upload işlemi
    
    Args:
        filename: Dosya adı
        content: Dosya içeriği (text veya base64)
        content_type: MIME type (application/pdf, text/plain, etc.)
        user_id: Kullanıcı ID
        is_base64: Content base64 mi?
    
    Returns:
        {
            "status": "success" | "error",
            "doc_id": str,
            "chunks_added": int,
            "filename": str,
            "error": str (if error)
        }
    """
    logger.info(f"Processing upload: {filename} (type={content_type})")
    
    try:
        # ============================================
        # 1. CONTENT DECODE (if base64)
        # ============================================
        
        if is_base64:
            try:
                content_bytes = base64.b64decode(content)
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Base64 decode error: {e}",
                    "filename": filename,
                }
        else:
            # Text olarak gelmiş
            content_bytes = content.encode('utf-8')
        
        # ============================================
        # 2. FILE TYPE DETECTION & PROCESSING
        # ============================================
        
        file_ext = Path(filename).suffix.lower()
        
        # TXT
        if file_ext == '.txt' or content_type == 'text/plain':
            text_content = content_bytes.decode('utf-8', errors='ignore')
        
        # PDF
        elif file_ext == '.pdf' or content_type == 'application/pdf':
            text_content = _extract_text_from_pdf(content_bytes)
        
        # DOCX (future support)
        elif file_ext == '.docx':
            return {
                "status": "error",
                "error": "DOCX support coming soon",
                "filename": filename,
            }
        
        else:
            return {
                "status": "error",
                "error": f"Unsupported file type: {file_ext}",
                "filename": filename,
            }
        
        # ============================================
        # 3. VALIDATION
        # ============================================
        
        if not text_content or len(text_content.strip()) < 50:
            return {
                "status": "error",
                "error": "Document too short or empty",
                "filename": filename,
            }
        
        # Max size check (500 sayfa = ~1M karakter)
        max_chars = 1_000_000
        if len(text_content) > max_chars:
            return {
                "status": "error",
                "error": f"Document too large (max {max_chars} chars)",
                "filename": filename,
            }
        
        logger.info(f"Extracted text: {len(text_content)} chars")
        
        # ============================================
        # 4. ADD TO KNOWLEDGE BASE
        # ============================================
        
        result = knowledge.add_document_to_knowledge(
            filename=filename,
            content=text_content,
            metadata={
                "content_type": content_type,
                "file_size": len(content_bytes),
            },
            user_id=user_id,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Upload processing error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "filename": filename,
        }


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    PDF'den text çıkar
    
    Args:
        pdf_bytes: PDF binary data
    
    Returns:
        Extracted text
    """
    try:
        import PyPDF2
        import io
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = '\n\n'.join(text_parts)
        
        logger.info(f"PDF extraction: {len(pdf_reader.pages)} pages, {len(full_text)} chars")
        
        return full_text
        
    except ImportError:
        raise ImportError("PyPDF2 required. Install: pip install PyPDF2")
    except Exception as e:
        raise Exception(f"PDF extraction error: {e}")


def delete_document_by_id(doc_id: str) -> Dict:
    """
    Dokümanı sil
    
    Args:
        doc_id: Document ID
    
    Returns:
        {"status": str, "deleted_chunks": int}
    """
    return knowledge.delete_document(doc_id)


def list_user_documents(user_id: str) -> list:
    """
    Kullanıcının dokümanlarını listele
    
    Args:
        user_id: Kullanıcı ID
    
    Returns:
        List of documents
    """
    return knowledge.list_all_documents(user_id=user_id)


def get_knowledge_statistics() -> Dict:
    """
    Knowledge base istatistikleri
    
    Returns:
        Stats dict
    """
    return knowledge.get_knowledge_stats()