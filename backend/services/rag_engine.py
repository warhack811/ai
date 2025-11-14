"""
services/rag_engine.py
----------------------
RAG (Retrieval-Augmented Generation) motoru.

Görev:
- Lokal dokümanlardan (knowledge.py) uygun parçaları getir
- (İsteğe bağlı) web'den SearxNG ile arama yap
- Bu konteksi tek bir metin halinde birleştir
- Ayrıca SourceInfo listesi döndür (frontend "Kaynaklar" paneli için)
"""

from __future__ import annotations

from typing import List, Tuple

import httpx

from config import get_settings
from schemas.common import SourceInfo, SourceType
from schemas.common import IntentLabel, ChatMode
from services import knowledge

settings = get_settings()


# ---------------------------------------------------------------------------
# Web Arama (SearxNG)
# ---------------------------------------------------------------------------

async def _web_search_searxng(
    query: str,
    max_results: int,
) -> List[SourceInfo]:
    """
    SearxNG ile web araması yapar, SourceInfo listesi döner.
    """
    if not settings.web_search.enabled:
        return []

    urls = [str(u) for u in settings.web_search.searxng_urls]
    all_results: List[SourceInfo] = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    languages = [settings.web_search.default_language, settings.web_search.fallback_language]

    async with httpx.AsyncClient(timeout=settings.web_search.timeout_seconds, headers=headers) as client:
        for base in urls:
            for lang in languages:
                try:
                    resp = await client.get(
                        f"{base.rstrip('/')}/search",
                        params={
                            "q": query,
                            "format": "json",
                            "language": lang,
                            "safesearch": "0",
                        },
                    )
                except Exception:
                    continue

                if resp.status_code != 200:
                    continue

                data = resp.json()
                for item in data.get("results", []):
                    url = item.get("url") or ""
                    title = item.get("title") or ""
                    content = item.get("content") or ""

                    # Yasaklı domainler
                    if any(bad in url for bad in settings.web_search.blocked_domains):
                        continue

                    snippet = content[:300] if content else ""
                    src = SourceInfo(
                        type=SourceType.WEB,
                        title=title[:200] or url[:200],
                        url=url or None,
                        snippet=snippet,
                        score=None,
                        metadata={"language": lang},
                    )
                    all_results.append(src)

                    if len(all_results) >= max_results:
                        break
                if len(all_results) >= max_results:
                    break
            if len(all_results) >= max_results:
                break

    return all_results


# ---------------------------------------------------------------------------
# RAG Ana Fonksiyonu
# ---------------------------------------------------------------------------

async def build_augmented_context(
    query: str,
    user_id: str,
    use_web: bool,
    max_sources: int,
    intent: IntentLabel,
    mode: ChatMode,
) -> Tuple[str, List[SourceInfo]]:
    """
    Pipeline'in çağırdığı ana fonksiyon.

    Döndürür:
      - context_text: LLM'e verilecek extra bilgi metni
      - sources: Frontend için kaynak listesi
    """
    # 1) Lokal dokümanlardan uygun parçaları getir
    local_sources = knowledge.search_local_chunks_simple(
        query=query,
        max_results=min(max_sources, settings.rag.max_local_chunks),
        collections=settings.rag.default_collections,
    )

    # 2) Web araması (isteğe bağlı)
    web_sources: List[SourceInfo] = []
    if use_web and settings.web_search.enabled and settings.rag.enable_for_realtime_topics:
        try:
            web_sources = await _web_search_searxng(
                query=query,
                max_results=min(max_sources, settings.rag.max_web_results),
            )
        except Exception:
            web_sources = []

    # 3) Tüm kaynakları birleştir
    sources: List[SourceInfo] = []
    sources.extend(local_sources)
    sources.extend(web_sources)

    # 4) context_text'i oluştur
    lines: List[str] = []

    if local_sources:
        lines.append("[LOCAL DOCUMENTS]")
        for i, s in enumerate(local_sources, start=1):
            snippet = s.snippet or ""
            lines.append(f"({i}) {s.title}: {snippet}")

    if web_sources:
        lines.append("\n[WEB RESULTS]")
        for i, s in enumerate(web_sources, start=1):
            snippet = s.snippet or ""
            url = s.url or ""
            lines.append(f"({i}) {s.title} - {url}\n{snippet}")

    context_text = "\n".join(lines).strip()

    return context_text, sources
