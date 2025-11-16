"""
config.py - DÜZELTİLMİŞ VERSİYON
---------------------------------
✅ DeepSeek model adı düzeltildi
✅ QWEN context size optimize edildi
✅ Model öncelikleri ayarlandı
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

        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.files_dir is None:
            self.files_dir = self.data_dir / "files"
        if self.cache_dir is None:
            self.cache_dir = self.data_dir / "cache"

        if self.chat_db_path is None:
            self.chat_db_path = self.data_dir / "chat_history.db"
        if self.knowledge_db_path is None:
            self.knowledge_db_path = self.data_dir / "knowledge.db"
        if self.profile_db_path is None:
            self.profile_db_path = self.data_dir / "profile.db"


# ---------------------------------------------------------------------------
# LLM Ayarları - OPTİMİZE EDİLMİŞ
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

    # ============================================================
    # MODEL TANIMLARI (Ollama List ile Eşleşmeli!)
    # ============================================================
    
    # 1. PHI - Birincil Model (Hızlı + Hafif)
    phi: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_PHI_NAME", "phi-3.5-mini-instruct-q4_k_m"),
        display_name="Phi 3.5 Mini (Hızlı Asistan)",
        provider="ollama",
        context_length=4096,
        default_temperature=0.7,
        default_max_tokens=1024,
        is_primary=True,  # ✅ Ana model (basit sorular için)
    )
    
    # 2. MISTRAL - İkincil Model (Kod + Orta Seviye)
    mistral: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_MISTRAL_NAME", "mistral-7b-uncensored-q4_k_m"),
        display_name="Mistral 7B (Dengeli)",
        provider="ollama",
        context_length=4096,
        default_temperature=0.5,
        default_max_tokens=1536,  # Biraz artırıldı
        is_primary=False,
    )
    
    # 3. QWEN - Kalite Odaklı (Sadece Gerektiğinde)
    qwen: SingleLLMModelSettings = SingleLLMModelSettings(
        name=os.getenv("LLM_QWEN_NAME", "qwen2.5-14b-uncensored-q4_k_m"),
        display_name="Qwen 2.5 14B (Detaylı Asistan)",
        provider="ollama",
        context_length=8192,
        default_temperature=0.6,  # Biraz düşürüldü (hız için)
        default_max_tokens=2048,
        is_primary=False,
    )
    
    # 4. DEEPSEEK - Reasoning (Çok Nadir)
    deepseek: SingleLLMModelSettings = SingleLLMModelSettings(
        # ⚠️ BURADA DÜZELTME YAPILDI - Ollama list'teki tam ad
        name=os.getenv("LLM_DEEPSEEK_NAME", "deepseek-r1-8b-uncensored-q4_k_m"),
        display_name="DeepSeek R1 8B (Reasoning)",
        provider="ollama",
        context_length=8192,
        default_temperature=0.4,
        default_max_tokens=2048,
        is_primary=False,
    )


class RagSettings(BaseModel):
    enable_for_realtime_topics: bool = True
    max_local_chunks: int = 8
    max_web_results: int = 5
    default_collections: list[str] = Field(default_factory=lambda: ["general"])
    
    # ✅ Model bazlı dinamik context (QWEN için azaltıldı)
    context_sizes: dict = Field(default_factory=lambda: {
        "phi": {
            "max_history": 2, 
            "max_chunks": 2, 
            "max_web": 2
        },
        "mistral": {
            "max_history": 4,  # Artırıldı
            "max_chunks": 4,   # Artırıldı
            "max_web": 3
        },
        "qwen": {
            "max_history": 4,  # 5'ten 4'e düşürüldü (hız için)
            "max_chunks": 4,   # 5'ten 4'e düşürüldü
            "max_web": 3       # 4'ten 3'e düşürüldü
        },
        "deepseek": {
            "max_history": 6, 
            "max_chunks": 6, 
            "max_web": 4
        },
    })
    
    def get_context_size(self, model_key: str) -> dict:
        """Model için optimal context size"""
        return self.context_sizes.get(model_key, self.context_sizes["mistral"])


# ---------------------------------------------------------------------------
# Web Search Ayarları
# ---------------------------------------------------------------------------

class WebSearchSettings(BaseModel):
    enabled: bool = True
    searxng_urls: list[str] = Field(
        default_factory=lambda: [os.getenv("SEARXNG_URL", "http://localhost:8888")]
    )
    default_language: str = "tr"
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