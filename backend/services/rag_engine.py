"""
services/rag_engine.py - FAS 2 VERSION
----------------------
✅ Local document search integrated
✅ Web search + Local fusion
✅ Smart source ranking
✅ Context optimization
"""

import logging
from typing import List, Tuple, Optional
import asyncio

from schemas.common import (
    SourceInfo, SourceType, IntentLabel, ChatMode
)
from services import knowledge
from services import web_search

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine
    
    Features:
    - Local document search (ChromaDB)
    - Web search (SearXNG)
    - Multi-source fusion
    - Smart ranking
    """
    
    def __init__(self):
        self.max_context_chars = 3000  # Max RAG context
    
    async def build_augmented_context(
        self,
        query: str,
        user_id: str,
        use_web: bool,
        max_sources: int,
        intent: IntentLabel,
        mode: ChatMode,
    ) -> Tuple[str, List[SourceInfo]]:
        """
        RAG pipeline: Local docs + Web search
        
        Args:
            query: Kullanıcı sorusu
            user_id: Kullanıcı ID
            use_web: Web araması yapılsın mı?
            max_sources: Max kaynak sayısı
            intent: Intent label
            mode: Chat mode
        
        Returns:
            (context_text, sources)
        """
        logger.info(f"RAG: query='{query[:50]}...' | web={use_web}")
        
        # ============================================
        # PARALLEL SEARCH: Local + Web
        # ============================================
        
        tasks = []
        
        # 1. Local documents (her zaman ara)
        tasks.append(self._search_local_documents(query, user_id, max_sources))
        
        # 2. Web search (sadece gerekirse)
        if use_web and self._should_use_web(query, intent, mode):
            tasks.append(self._search_web(query, max_sources))
        else:
            # Boş sonuç ekle (parallel olmayan durum için)
            tasks.append(self._empty_search())
        
        # Parallel çalıştır
        local_sources, web_sources = await asyncio.gather(*tasks)
        
        logger.info(f"RAG results: local={len(local_sources)}, web={len(web_sources)}")
        
        # ============================================
        # MERGE & RANK
        # ============================================
        
        all_sources = local_sources + web_sources
        
        if not all_sources:
            return "", []
        
        # Ranking (score'a göre sırala)
        ranked_sources = sorted(
            all_sources,
            key=lambda s: s.score if s.score else 0.0,
            reverse=True
        )[:max_sources]
        
        # ============================================
        # BUILD CONTEXT TEXT
        # ============================================
        
        context_text = self._build_context_text(ranked_sources)
        
        logger.info(f"RAG context: {len(context_text)} chars, {len(ranked_sources)} sources")
        
        return context_text, ranked_sources
    
    async def _search_local_documents(
        self,
        query: str,
        user_id: str,
        max_results: int,
    ) -> List[SourceInfo]:
        """Local document search"""
        try:
            return knowledge.search_local_documents(
                query=query,
                max_results=max_results,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Local search error: {e}")
            return []
    
    async def _search_web(
        self,
        query: str,
        max_results: int,
    ) -> List[SourceInfo]:
        """Web search"""
        try:
            return await web_search.search_web_simple(
                query=query,
                max_results=max_results,
            )
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    async def _empty_search(self) -> List[SourceInfo]:
        """Empty search result (for parallel)"""
        return []
    
    def _should_use_web(
        self,
        query: str,
        intent: IntentLabel,
        mode: ChatMode,
    ) -> bool:
        """
        Web araması gerekli mi?
        
        Kriterler:
        - Realtime keywords (hava, haber, fiyat, bugün)
        - Research mode
        - Web search intent
        """
        # Realtime keywords
        realtime_keywords = [
            'hava', 'weather', 'bugün', 'today', 'son', 'latest',
            'güncel', 'current', 'news', 'haber', 'fiyat', 'price',
            'şimdi', 'now', 'yeni', 'new',
        ]
        
        query_lower = query.lower()
        
        if any(k in query_lower for k in realtime_keywords):
            return True
        
        # Research mode
        if mode == ChatMode.RESEARCH:
            return True
        
        # Web search intent
        if intent == IntentLabel.WEB_SEARCH:
            return True
        
        return False
    
    def _build_context_text(self, sources: List[SourceInfo]) -> str:
        """
        Kaynaklardan context metni oluştur
        
        Format:
        [Kaynak 1: Title]
        Content...
        
        [Kaynak 2: Title]
        Content...
        """
        if not sources:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, source in enumerate(sources, 1):
            # Source header
            header = f"[Kaynak {i}"
            if source.type == SourceType.WEB:
                header += f" - Web: {source.title}]"
            elif source.type == SourceType.DOCUMENT:
                header += f" - Doküman: {source.title}]"
            else:
                header += f": {source.title}]"
            
            # Content
            content = source.snippet.strip()
            
            # Length check
            part_length = len(header) + len(content) + 4  # +4 for newlines
            
            if current_length + part_length > self.max_context_chars:
                # Max context aşılıyor, daha fazla ekleme
                break
            
            context_parts.append(header)
            context_parts.append(content)
            context_parts.append("")  # Boş satır
            
            current_length += part_length
        
        return "\n".join(context_parts)


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_rag_engine = RAGEngine()


async def build_augmented_context(
    query: str,
    user_id: str,
    use_web: bool,
    max_sources: int,
    intent: IntentLabel,
    mode: ChatMode,
) -> Tuple[str, List[SourceInfo]]:
    """
    Global RAG function
    """
    return await _rag_engine.build_augmented_context(
        query=query,
        user_id=user_id,
        use_web=use_web,
        max_sources=max_sources,
        intent=intent,
        mode=mode,
    )