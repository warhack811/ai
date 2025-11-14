"""
services/rate_limit.py
----------------------
Basit bir rate limiting mekanizması.

- Config:
    settings.rate_limit.enabled
    settings.rate_limit.requests_per_minute
    settings.rate_limit.burst_size
    settings.rate_limit.strategy  -> "ip" | "user" | "both"

- Amaç:
    /api/chat ve /api/upload-document gibi endpoint'lerde
    kötüye kullanımı (spam, aşırı istek) sınırlamak.

- Uygulama:
    rate_limiter_dependency, FastAPI dependency olarak kullanılır.
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, List

from fastapi import HTTPException, Request, status

from config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# In-Memory Rate Limit Deposu
# ---------------------------------------------------------------------------

# key -> [timestamp1, timestamp2, ...]  (son 60 saniyedeki istek zamanları)
_request_log: Dict[str, List[float]] = {}
_lock = asyncio.Lock()


def _get_client_ip(request: Request) -> str:
    """
    İstemcinin IP adresini basit şekilde çıkarır.
    Prod'da X-Forwarded-For gibi header'lar da kontrol edilebilir.
    """
    client_host = request.client.host if request.client else "unknown"

    # Proxy arkasında kullanacaksan ileride buraya X-Forwarded-For kontrolü ekleyebilirsin.
    return client_host


async def _get_user_id_from_request(request: Request) -> str:
    """
    Rate limit stratejisi 'user' veya 'both' olduğunda,
    istekten user_id çıkarmaya çalışır.

    Şu an için:
    - /api/chat ve /api/upload-document body içinde "user_id" alanını kullanıyoruz.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    user_id = body.get("user_id")
    if not user_id:
        # User id yoksa IP bazlı bir fallback kullanabiliriz,
        # ama burada None döndürüp sadece IP ile de sınırlayabiliriz.
        return ""
    return str(user_id)


def _build_keys(ip: str, user_id: str) -> List[str]:
    """
    Config'teki stratejiye göre kullanılacak rate limit key'lerini üretir.
    - "ip"    -> sadece IP bazlı
    - "user"  -> sadece user_id bazlı
    - "both"  -> hem IP hem user_id için ayrı ayrı limiter çalıştırılır
    """
    strategy = settings.rate_limit.strategy

    keys: List[str] = []
    if strategy in ("ip", "both"):
        keys.append(f"ip:{ip}")

    if strategy in ("user", "both") and user_id:
        keys.append(f"user:{user_id}")

    # User id yoksa ve strateji "user" ise, IP fallback olarak kullanılabilir:
    if strategy == "user" and not user_id:
        keys.append(f"ip:{ip}")

    return keys


# ---------------------------------------------------------------------------
# Rate Limiter Ana Mantığı
# ---------------------------------------------------------------------------

async def _check_and_update_rate_limit(keys: List[str]) -> None:
    """
    Verilen anahtarlar (ip/user) için rate limit kontrolünü yapar.
    - Son 60 saniyede yapılan istekleri sayar
    - Limit aşılmışsa HTTPException fırlatır
    """
    if not settings.rate_limit.enabled:
        return

    # limits
    per_minute = settings.rate_limit.requests_per_minute
    burst = settings.rate_limit.burst_size
    # Basit yaklaşım: dakikada per_minute + burst istek hakkı
    limit = per_minute + burst

    now = time.time()
    window = 60.0  # saniye

    async with _lock:
        for key in keys:
            timestamps = _request_log.get(key, [])

            # Sadece son 60 saniyedeki istekler
            valid_since = now - window
            timestamps = [t for t in timestamps if t >= valid_since]

            if len(timestamps) >= limit:
                # Limit aşıldı
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please slow down.",
                )

            # İstek hakkımız varsa, bu isteği kayda ekleyelim
            timestamps.append(now)
            _request_log[key] = timestamps


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

async def rate_limiter_dependency(request: Request) -> None:
    """
    FastAPI endpoint'lerinde dependency olarak kullanılacak fonksiyon.

    Örnek:
        @app.post("/api/chat")
        async def chat_endpoint(
            payload: ChatRequest,
            _: None = Depends(rate_limiter_dependency),
        ):
            ...

    Eğer rate limit aşılırsa HTTP_429 hatası fırlatılır.
    """
    if not settings.rate_limit.enabled:
        return

    client_ip = _get_client_ip(request)
    user_id = await _get_user_id_from_request(request)

    keys = _build_keys(client_ip, user_id)
    if not keys:
        # Her ihtimale karşı, anahtar yoksa sadece IP bazlı bir tane kullanalım
        keys = [f"ip:{client_ip}"]

    await _check_and_update_rate_limit(keys)
