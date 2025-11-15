"""
services/knowledge.py - FAS 2 VERSION
---------------------
✅ ChromaDB entegrasyonu
✅ Document upload & processing
✅ Semantic search
✅ PDF & TXT support
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
import hashlib
from pathlib import Path

from schemas.common import SourceInfo, SourceType
from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Document Upload & Processing
# ---------------------------------------------------------------------------

def add_document_to_knowledge(
    filename: str,
    content: str,
    metadata: Optional[Dict] = None,
    user_id: str = "default",
) -> Dict:
    """
    Yeni doküman ekle ve öğren
    
    Args:
        filename: Dosya adı
        content: Doküman içeriği (text)
        metadata: Ek metadata
        user_id: Kullanıcı ID
    
    Returns:
        {
            "doc_id": str,
            "status": str,
            "chunks_added": int,
            "filename": str
        }
    """
    logger.info(f"Processing document: {filename} ({len(content)} chars)")
    
    # Unique doc ID oluştur (filename + timestamp + hash)
    timestamp = int(datetime.utcnow().timestamp())
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    doc_id = f"{user_id}_{timestamp}_{content_hash}"
    
    # Metadata hazırla
    doc_metadata = {
        "filename": filename,
        "user_id": user_id,
        "added_at": datetime.utcnow().isoformat(),
        "file_size": len(content),
        "type": _detect_file_type(filename),
    }
    
    if metadata:
        doc_metadata.update(metadata)
    
    # Vector store'a ekle
    vector_store = get_vector_store()
    
    try:
        result = vector_store.add_document(
            doc_id=doc_id,
            text=content,
            metadata=doc_metadata,
            chunk_size=512,  # Her chunk max 512 kelime
            chunk_overlap=50,  # 50 kelime overlap
        )
        
        logger.info(f"✓ Document added: {doc_id} ({result['chunks_added']} chunks)")
        
        return {
            "doc_id": doc_id,
            "status": "success",
            "chunks_added": result['chunks_added'],
            "filename": filename,
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {e}", exc_info=True)
        return {
            "doc_id": doc_id,
            "status": "error",
            "error": str(e),
            "filename": filename,
        }


def _detect_file_type(filename: str) -> str:
    """Dosya türünü tespit et"""
    ext = Path(filename).suffix.lower()
    
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.txt':
        return 'text'
    elif ext in ['.doc', '.docx']:
        return 'word'
    elif ext in ['.py', '.js', '.cpp', '.java', '.ts']:
        return 'code'
    else:
        return 'unknown'


# ---------------------------------------------------------------------------
# Document Search (Semantic)
# ---------------------------------------------------------------------------

def search_local_documents(
    query: str,
    max_results: int = 5,
    user_id: Optional[str] = None,
    doc_types: Optional[List[str]] = None,
) -> List[SourceInfo]:
    """
    Yerel dokümanlardan semantic arama
    
    Args:
        query: Arama sorgusu
        max_results: Max sonuç sayısı
        user_id: Sadece bu kullanıcının dokümanları (opsiyonel)
        doc_types: Sadece bu tiplerde ara (opsiyonel)
    
    Returns:
        List of SourceInfo
    """
    vector_store = get_vector_store()
    
    # Metadata filter (opsiyonel)
    metadata_filter = {}
    if user_id:
        metadata_filter['user_id'] = user_id
    
    try:
        # Semantic search
        results = vector_store.search(
            query=query,
            top_k=max_results,
            filter_metadata=metadata_filter if metadata_filter else None,
        )
        
        # SourceInfo'ya çevir
        sources = []
        for r in results:
            # Relevance threshold (minimum 0.3 similarity)
            if r['score'] < 0.3:
                continue
            
            meta = r['metadata']
            
            # Doc type filter
            if doc_types and meta.get('type') not in doc_types:
                continue
            
            source = SourceInfo(
                type=SourceType.DOCUMENT,
                title=meta.get('filename', 'Unknown Document'),
                url=None,
                snippet=r['text'][:300],  # İlk 300 karakter
                score=r['score'],
                metadata={
                    "doc_id": meta.get('doc_id'),
                    "chunk_index": meta.get('chunk_index'),
                    "added_at": meta.get('added_at'),
                }
            )
            sources.append(source)
        
        logger.info(f"Found {len(sources)} relevant documents for query")
        return sources
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return []


# ---------------------------------------------------------------------------
# Document Management
# ---------------------------------------------------------------------------

def delete_document(doc_id: str) -> Dict:
    """
    Dokümanı sil
    
    Args:
        doc_id: Document ID
    
    Returns:
        {"status": str, "deleted_chunks": int}
    """
    vector_store = get_vector_store()
    
    try:
        result = vector_store.delete_document(doc_id)
        logger.info(f"✓ Document deleted: {doc_id}")
        return result
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        return {"status": "error", "error": str(e)}


def list_all_documents(user_id: Optional[str] = None) -> List[Dict]:
    """
    Tüm dokümanları listele
    
    Args:
        user_id: Sadece bu kullanıcının dokümanları (opsiyonel)
    
    Returns:
        List of document info
    """
    vector_store = get_vector_store()
    
    try:
        docs = vector_store.list_documents()
        
        # User filter
        if user_id:
            docs = [d for d in docs if d.get('user_id') == user_id]
        
        return docs
    except Exception as e:
        logger.error(f"Document listing error: {e}")
        return []


def get_knowledge_stats() -> Dict:
    """
    Knowledge base istatistikleri
    
    Returns:
        Statistics dict
    """
    vector_store = get_vector_store()
    
    try:
        return vector_store.get_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# UTILITY: Process file content
# ---------------------------------------------------------------------------

def process_file_content(file_path: str) -> str:
    """
    Dosya içeriğini oku ve işle
    
    Supports: .txt, .pdf
    
    Args:
        file_path: Dosya yolu
    
    Returns:
        İşlenmiş text içeriği
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = path.suffix.lower()
    
    # TXT
    if ext == '.txt':
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # PDF
    elif ext == '.pdf':
        try:
            import PyPDF2
            
            text = []
            with open(path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            
            return '\n\n'.join(text)
        except ImportError:
            raise ImportError("PyPDF2 required for PDF processing. Install: pip install PyPDF2")
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")