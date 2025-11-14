"""
services/knowledge.py
---------------------
Lokal doküman tabanlı bilgi deposu (RAG için).

Görevler:
- Doküman indeksleme (upload_service burayı kullanıyor)
- Chunk'lara bölme
- Basit arama (şimdilik keyword + LIKE tabanlı)

Not:
Şimdilik embedding hesaplamıyoruz, ama 'chunks.embedding' alanı ileride
vektör eklemek istediğinde hazır.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple, Optional

from config import get_settings
from schemas.common import SourceInfo, SourceType
from services.db import execute, fetch_all, fetch_val

settings = get_settings()


# ---------------------------------------------------------------------------
# Yardımcı: Chunk'lama
# ---------------------------------------------------------------------------

def _split_into_chunks(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """
    Basit metin chunk'lama:
    - Cümle sınırlarına mümkün olduğunca saygı
    - max_chars civarında parçalara böler
    - overlap ile komşu chunk'lar arasında biraz çakışma bırakır
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []

    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            # Çok uzun paragrafları direkt bölelim
            for i in range(0, len(para), max_chars):
                piece = para[i : i + max_chars]
                if current:
                    chunks.append(current.strip())
                    current = ""
                chunks.append(piece.strip())
            continue

        if len(current) + len(para) + 1 <= max_chars:
            current += (" " if current else "") + para
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    # Overlap için basit bir yaklaşım: chunk'ların son k karakterini sonraki chunk'a ekleme
    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks: List[str] = []
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(ch)
            else:
                prev = chunks[i - 1]
                tail = prev[-overlap:]
                merged = (tail + " " + ch).strip()
                overlapped_chunks.append(merged)
        return overlapped_chunks

    return chunks


# ---------------------------------------------------------------------------
# Doküman İndeksleme
# ---------------------------------------------------------------------------

async def index_document(
    document_id: str,
    user_id: str,
    filename: str,
    content: str,
    collection: str,
    language: str,
    size: int,
    content_type: str,
) -> int:
    """
    Dokümanı knowledge.db'ye kaydeder ve chunk'lara böler.

    Dönüş: oluşan chunk sayısı
    """
    created_at = datetime.utcnow().isoformat()

    # 1) documents tablosuna meta kaydet
    execute(
        """
        INSERT INTO documents (
            id, user_id, filename, collection, language, size,
            content_type, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        params=[
            document_id,
            user_id,
            filename,
            collection,
            language,
            size,
            content_type,
            created_at,
        ],
        db="knowledge",
    )

    # 2) Chunk'lara böl
    chunks = _split_into_chunks(content, max_chars=800, overlap=100)

    rows = []
    for idx, ch in enumerate(chunks):
        rows.append(
            (
                document_id,
                idx,
                ch,
                language,
                created_at,
                None,  # embedding
            )
        )

    if rows:
        execute(
            """
            INSERT INTO chunks (
                document_id, chunk_index, text, language, created_at, embedding
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            seq_of_params=rows,
            db="knowledge",
        )
    return len(chunks)


# ---------------------------------------------------------------------------
# Basit Lokal Arama
# ---------------------------------------------------------------------------

def _build_like_pattern(query: str) -> str:
    # Çok kaba: sadece %query%
    return f"%{query.strip()}%"


def search_local_chunks_simple(
    query: str,
    max_results: int = 8,
    collections: Optional[List[str]] = None,
) -> List[SourceInfo]:
    """
    Embedding olmadan, LIKE tabanlı basit arama.

    - 'chunks.text LIKE %query%' ile eşleşen chunk'ları alır
    - İlgili dokümanın meta verileriyle birlikte SourceInfo döner
    """
    like = _build_like_pattern(query)
    params: list = [like, max_results]

    collection_filter = ""
    if collections:
        placeholders = ",".join("?" for _ in collections)
        collection_filter = f"AND d.collection IN ({placeholders})"
        params = [like, *collections, max_results]

    sql = f"""
        SELECT
            c.text AS chunk_text,
            c.document_id,
            c.chunk_index,
            d.filename,
            d.collection,
            d.language
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.text LIKE ?
        {collection_filter}
        ORDER BY c.id DESC
        LIMIT ?;
    """

    rows = fetch_all(sql, params=params, db="knowledge")
    sources: List[SourceInfo] = []

    for r in rows:
        title = f"{r['filename']} [parça {r['chunk_index']}]"
        snippet = r["chunk_text"][:300]
        src = SourceInfo(
            type=SourceType.DOCUMENT,
            title=title,
            url=None,
            snippet=snippet,
            score=None,  # şimdilik boş
            metadata={
                "document_id": r["document_id"],
                "chunk_index": r["chunk_index"],
                "collection": r["collection"],
                "language": r["language"],
            },
        )
        sources.append(src)

    return sources
