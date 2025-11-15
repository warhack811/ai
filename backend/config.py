"""
config.py
---------
Uygulama ayarları ve yollar.

- Ortak Settings nesnesi
- DB, LLM, Web Search, Memory, Safety, Rate Limit ayarları
- get_settings() ile singleton erişim

Pydantic 2.x ile uyumlu, BaseModel tabanlı config.
"""

from __future__ import annotations

import os
from functools import lru_cache 
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, AnyHttpUrl


# ---------------------------------------------------------------------------
# DB Ayarları
# ---------------------------------------------------------------------------

class DBSettings(BaseModel):
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent
    )

    data_dir: Path | None = None
    files_dir: Path | None = None
    cache_dir: Path | None = None

    chat_db_path: Path | None = None
    knowledge_db_path: Path | None = None
    profile_db_path: Path | None = None

    sqlite_timeout: float = 30.0

    def __init__(self, **data):
        super().__init__(**data)

        # Varsayılan klasörler
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.files_dir is None:
            self.files_dir = self.data_dir / "files"
        if self.cache_dir is None:
            self.cache_dir = self.data_dir / "cache"

        # Varsayılan DB yolları
        if self.chat_db_path is None:
            self.chat_db_path = self.data_dir / "chat_history.db"
        if self.knowledge_db_path is None:
            self.knowledge_db_path = self.data_dir / "knowledge.db"
        if self.profile_db_path is None:
            self.profile_db_path = self.data_dir / "profile.db"


# ---------------------------------------------------------------------------
# LLM Ayarları
# ---------------------------------------------------------------------------

class SingleLLMModelSettings(BaseModel):
    name: str
    display_name: str
    provider: Literal["ollama", "openai-compatible", "custom"] = "ollama"
    context_length: int = 4096
    default_temperature: float = 0.4
    default_max_tokens: int = 1024
    is_primary: bool = False


class LLMSettings(BaseModel):
    ollama_base_url: AnyHttpUrl = "http://localhost:11434"

    # Ana modeller (isimler OLLAMA MODEL adlarınla birebir aynı olmalı!)
    qwen: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_QWEN_NAME", "qwen2.5-14b-uncensored-q4_k_m"),
        display_name="Qwen 2.5 14B Uncensored (Ana Asistan)",
        provider="ollama",
        context_length=8192,
        default_temperature=0.5,
        default_max_tokens=2048,
        is_primary=False,   # 🔵 Qwen artık primary değil
    )
    deepseek: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_DEEPSEEK_NAME", "deepseek-r1-8b-uncensored-q4_k_m"),
        display_name="DeepSeek R1 8B Uncensored (Reasoning)",
        provider="ollama",
        context_length=8192,
        default_temperature=0.4,
        default_max_tokens=2048,
        is_primary=False,
    )
    mistral: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_MISTRAL_NAME", "mistral-7b-uncensored-q4_k_m"),
        display_name="Mistral 7B Uncensored (Hızlı)",
        provider="ollama",
        context_length=4096,
        default_temperature=0.5,
        default_max_tokens=1024,
        is_primary=False,   # Mistral da primary DEĞİL
    )
    phi: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_PHI_NAME", "phi-3.5-mini-instruct-q4_k_m"),
        display_name="Phi 3.5 Mini Instruct Q4_K_M",
        provider="ollama",
        context_length=4096,
        default_temperature=0.7,
        default_max_tokens=1024,
        is_primary=True,    # ✅ ANA MODEL ARTIK PHI
    )

class RagSettings(BaseModel):
    # Gerçek zamanlı konular için web aramasını kullan
    enable_for_realtime_topics: bool = True

    # Lokal dokümanlardan maksimum chunk sayısı
    max_local_chunks: int = 8

    # Web sonuçları için maksimum sonuç sayısı
    max_web_results: int = 5

    # Varsayılan koleksiyonlar (knowledge.search_local_chunks_simple için)
    default_collections: list[str] = Field(default_factory=lambda: ["general"])

# ---------------------------------------------------------------------------
# Web Search Ayarları
# ---------------------------------------------------------------------------

class WebSearchSettings(BaseModel):
    enabled: bool = True
    searxng_urls: list[str] = Field(
        default_factory=lambda: [os.getenv("SEARXNG_URL", "http://localhost:8888")]
    )
    default_language: str = "tr"

    # RAG + web_search modüllerinin beklediği alanlar:
    fallback_language: str = "en"
    timeout_seconds: float = 10.0
    blocked_domains: list[str] = Field(
        default_factory=lambda: [
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "tiktok.com",
            "pinterest.com",
        ]
    )

    default_language: str = "tr"


# ---------------------------------------------------------------------------
# Memory Ayarları
# ---------------------------------------------------------------------------

class MemorySettings(BaseModel):
    short_term_window: int = 20
    min_importance_score: float = 0.7


# ---------------------------------------------------------------------------
# Safety Ayarları
# ---------------------------------------------------------------------------

class SafetySettings(BaseModel):
    enabled: bool = False
    profile: Literal["uncensored", "balanced", "safe"] = "uncensored"

    # 'Yumuşak' uyarı mesajlarını aç/kapat
    soft_guardrails: bool = True


# ---------------------------------------------------------------------------
# Rate Limit Ayarları
# ---------------------------------------------------------------------------

class RateLimitSettings(BaseModel):
    enabled: bool = True
    requests_per_minute: int = 30
    burst_size: int = 10
    strategy: Literal["ip", "user", "both"] = "both"


# ---------------------------------------------------------------------------
# Ana Settings
# ---------------------------------------------------------------------------

class Settings(BaseModel):
    app_name: str = "AI Personal Assistant"
    env: Literal["dev", "prod"] = os.getenv("APP_ENV", "dev")
    api_root_path: str = "/api"
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    db: DBSettings = DBSettings()
    llm: LLMSettings = LLMSettings()
    web_search: WebSearchSettings = WebSearchSettings()
    memory: MemorySettings = MemorySettings()
    safety: SafetySettings = SafetySettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    rag: RagSettings = RagSettings()
    class Config:
        arbitrary_types_allowed = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Uygulama boyunca tek bir Settings instance kullanılır.
    """
    return Settings()
