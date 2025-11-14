"""
services/web_search.py
----------------------
SearxNG üzerinden web araması yapan servis.

- advanced_web_search(query, max_results, language)
    -> RAG için kullanılacak web sonuçlarını döner.

SearxNG ayarları:
- settings.web_search.searxng_urls (list)
- settings.web_search.enabled
"""

from __future__ import annotations

from typing import Dict, List, Optional

import httpx

from config import get_settings

settings = get_settings()

SCRAPE_TIMEOUT = 15.0


async def advanced_web_search(
    query: str,
    max_results: int = 5,
    language: str = "tr",
) -> List[Dict]:
    """
    SearxNG üzerinden gelişmiş web araması.

    Dönüş:
        [
          {
            "title": str,
            "url": str,
            "content": str,
            "quality_score": float,   # şimdilik hep 1.0 (placeholder)
            "domain_trust": float,    # şimdilik hep 0.5 (placeholder)
          },
          ...
        ]
    """
    if not settings.web_search.enabled:
        return []

    searxng_urls = settings.web_search.searxng_urls or []
    if not searxng_urls:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    all_results: List[Dict] = []

    # Basit varyasyonlar (aynı query ile birkaç kez arama)
    search_variations = [
        (query, language),
        (f"{query} 2024", language),
        (f"{query} detaylı", language),
    ]

    async with httpx.AsyncClient(timeout=SCRAPE_TIMEOUT, headers=headers) as client:
        for base_url in searxng_urls:
            base_url = base_url.rstrip("/")
            for search_query, lang in search_variations:
                try:
                    resp = await client.get(
                        f"{base_url}/search",
                        params={
                            "q": search_query,
                            "format": "json",
                            "language": lang,
                            "safesearch": "0",
                        },
                    )

                    if resp.status_code == 403:
                        # SearxNG'de rate limit / bot koruması olabilir
                        # Diğer URL'lere geçmeye devam et
                        print(f"[SEARXNG] ❌ HTTP 403 ({search_query}, lang={lang})")
                        continue

                    if resp.status_code != 200:
                        print(f"[SEARXNG] ❌ HTTP {resp.status_code} ({search_query}, lang={lang})")
                        continue

                    data = resp.json()
                    for item in data.get("results", []):
                        url = item.get("url") or ""
                        title = item.get("title") or url
                        content = item.get("content") or ""

                        if not url or not content:
                            continue

                        # Bazı sosyal medya / spam domainleri atla
                        skip_domains = [
                            "facebook.com",
                            "twitter.com",
                            "instagram.com",
                            "youtube.com",
                            "tiktok.com",
                            "pinterest.com",
                        ]
                        if any(d in url for d in skip_domains):
                            continue

                        snippet = content.strip()
                        if len(snippet) > 1000:
                            snippet = snippet[:1000] + " ..."

                        result = {
                            "title": title[:200],
                            "url": url,
                            "content": snippet,
                            "quality_score": 1.0,   # Şimdilik sabit; ileride gelişmiş kalite değerlendirme eklenebilir
                            "domain_trust": 0.5,    # Placeholder
                        }
                        all_results.append(result)

                        if len(all_results) >= max_results:
                            break

                    if len(all_results) >= max_results:
                        break

                except Exception as e:
                    print(f"[SEARXNG] ❌ {base_url} - {e}")

            if len(all_results) >= max_results:
                break

    print(f"[SEARXNG] ✅ {len(all_results)} sonuç döndü ({query})")
    return all_results
