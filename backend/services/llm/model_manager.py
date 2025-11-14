"""
services/llm/model_manager.py
-----------------------------
LLM modellerinin merkezi yönetimi.

- config.LLMSettings üzerinden model bilgilerini okur
- Ollama ile konuşmak için genel bir HTTP client sağlar
- Farklı modeller (qwen, deepseek, mistral, phi) için ortak generate fonksiyonları sunar

Bu katman:
- Model adlarını / endpoint'leri tek yerde tutar
- Sağlam hata yönetimi ve logging yapar
- İleride farklı provider'lara (OpenAI-compatible, custom HTTP API vs.) açılmamızı kolaylaştırır
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Model Tanımı
# ---------------------------------------------------------------------------

@dataclass
class LLMModelInfo:
    key: str              # "qwen", "deepseek", "mistral", "phi"
    name: str             # Ollama/sağlayıcı üzerindeki model adı
    display_name: str     # UI için görünen ad
    provider: str         # "ollama" | "openai-compatible" | "custom"
    context_length: int
    default_temperature: float
    default_max_tokens: int
    is_primary: bool = False


def _load_models_from_settings() -> Dict[str, LLMModelInfo]:
    """
    config.LLMSettings içinden tüm modelleri okuyup
    key -> LLMModelInfo sözlüğüne çevirir.
    """
    llm_conf = settings.llm

    models: Dict[str, LLMModelInfo] = {}

    models["qwen"] = LLMModelInfo(
        key="qwen",
        name=llm_conf.qwen.name,
        display_name=llm_conf.qwen.display_name,
        provider=llm_conf.qwen.provider,
        context_length=llm_conf.qwen.context_length,
        default_temperature=llm_conf.qwen.default_temperature,
        default_max_tokens=llm_conf.qwen.default_max_tokens,
        is_primary=llm_conf.qwen.is_primary,
    )
    models["deepseek"] = LLMModelInfo(
        key="deepseek",
        name=llm_conf.deepseek.name,
        display_name=llm_conf.deepseek.display_name,
        provider=llm_conf.deepseek.provider,
        context_length=llm_conf.deepseek.context_length,
        default_temperature=llm_conf.deepseek.default_temperature,
        default_max_tokens=llm_conf.deepseek.default_max_tokens,
        is_primary=llm_conf.deepseek.is_primary,
    )
    models["mistral"] = LLMModelInfo(
        key="mistral",
        name=llm_conf.mistral.name,
        display_name=llm_conf.mistral.display_name,
        provider=llm_conf.mistral.provider,
        context_length=llm_conf.mistral.context_length,
        default_temperature=llm_conf.mistral.default_temperature,
        default_max_tokens=llm_conf.mistral.default_max_tokens,
        is_primary=llm_conf.mistral.is_primary,
    )
    models["phi"] = LLMModelInfo(
        key="phi",
        name=llm_conf.phi.name,
        display_name=llm_conf.phi.display_name,
        provider=llm_conf.phi.provider,
        context_length=llm_conf.phi.context_length,
        default_temperature=llm_conf.phi.default_temperature,
        default_max_tokens=llm_conf.phi.default_max_tokens,
        is_primary=llm_conf.phi.is_primary,
    )

    return models


# Global model kaydı (config'e göre)
_MODEL_REGISTRY: Dict[str, LLMModelInfo] = _load_models_from_settings()


# ---------------------------------------------------------------------------
# Ollama Client
# ---------------------------------------------------------------------------

class OllamaClient:
    """
    Ollama HTTP API üzerinden text generation yapan basit client.

    /api/generate endpoint'i kullanılır:
      POST /api/generate
      {
        "model": "qwen2.5-14b-instruct",
        "prompt": "...",
        "system": "...",
        "stream": false,
        "options": {...}
      }
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> Dict[str, bool]:
        """
        Ollama üzerinde mevcut modelleri listeler.
        Dönüş: { "model_adı": True, ... }
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.error("Ollama /tags HTTP %s: %s", resp.status_code, resp.text)
                    return {}
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return {m: True for m in models}
        except Exception as e:
            logger.error("Ollama /tags isteği başarısız: %s", e)
            return {}

    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        num_ctx: Optional[int] = None,
    ) -> str:
        """
        Verilen model adıyla Ollama'dan cevap üretir.
        Hatalı durumda anlamlı mesaj/log döner.
        """
        url = f"{self.base_url}/api/generate"

        # Varsayılanları ayarla
        temp = temperature if temperature is not None else 0.3
        num_predict = max_tokens if max_tokens is not None else 512
        ctx = num_ctx if num_ctx is not None else 4096

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(temp),
                "num_predict": int(num_predict),
                "num_ctx": int(ctx),
                # Buraya gerekiyorsa top_k, top_p, repeat_penalty, vs. eklenebilir.
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=settings.llm.qwen.context_length) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException:
            logger.error("Ollama generate timeout (model=%s)", model_name)
            return "⏱️ Model çok yavaş yanıt verdi (timeout)."
        except Exception as e:
            logger.error("Ollama generate hatası (model=%s): %s", model_name, e)
            return f"❌ Model hatası: {e}"

        if resp.status_code == 404:
            logger.error("Ollama: model bulunamadı: %s", model_name)
            return (
                f"❌ Model bulunamadı: '{model_name}'\n"
                f"Lütfen 'ollama list' ile mevcut modelleri kontrol et."
            )

        if resp.status_code != 200:
            logger.error(
                "Ollama HTTP %s (model=%s): %s",
                resp.status_code,
                model_name,
                resp.text,
            )
            return f"❌ Ollama HTTP {resp.status_code}: {resp.text}"

        try:
            data = resp.json()
        except Exception as e:
            logger.error("Ollama JSON parse hatası: %s", e)
            return f"❌ Model cevabı parse edilemedi: {e}"

        text = data.get("response") or ""
        if not text.strip():
            logger.warning("Ollama boş yanıt döndürdü (model=%s)", model_name)
            return "Cevap üretilemedi."

        return text.strip()


# Global Ollama client
_ollama_client = OllamaClient(base_url=str(settings.llm.ollama_base_url))


# ---------------------------------------------------------------------------
# Model Manager Ana Fonksiyonları
# ---------------------------------------------------------------------------

def get_model_info(key: str) -> Optional[LLMModelInfo]:
    """
    "qwen", "deepseek", "mistral", "phi" gibi anahtarlarla
    model bilgisine ulaşmak için.
    """
    return _MODEL_REGISTRY.get(key)


def get_primary_model() -> Optional[LLMModelInfo]:
    """
    Varsayılan (primary) sohbet modeli.
    Genelde qwen2.5 14B olacak.
    """
    for info in _MODEL_REGISTRY.values():
        if info.is_primary:
            return info
    # Hiçbiri primary işaretli değilse, qwen'e düş
    return _MODEL_REGISTRY.get("qwen")


def list_all_models() -> Dict[str, LLMModelInfo]:
    """
    Kayıtlı tüm modelleri döner.
    """
    return dict(_MODEL_REGISTRY)


async def test_llm_health() -> Dict[str, any]:
    """
    LLM katmanının genel sağlık durumunu test eder:
    - Ollama bağlantısı
    - Kayıtlı modellerin Ollama'da bulunup bulunmadığı
    """
    available = await _ollama_client.list_models()

    models_health = {}
    for key, info in _MODEL_REGISTRY.items():
        if info.provider != "ollama":
            models_health[key] = {
                "status": "unknown",
                "reason": f"provider={info.provider} için health check implemente edilmedi",
            }
            continue

        exists = info.name in available
        models_health[key] = {
            "status": "ok" if exists else "missing",
            "model_name": info.name,
        }

    status = "ok"
    if not available:
        status = "error"
    elif any(v["status"] != "ok" for v in models_health.values()):
        status = "degraded"

    return {
        "status": status,
        "ollama_base_url": settings.llm.ollama_base_url,
        "models": models_health,
    }


async def generate_with_model(
    model_key: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Verilen model key'i ile (qwen, deepseek, mistral, phi)
    prompt'tan bir cevap üretir.

    - Doğru provider'a göre uygun client seçer (şimdilik sadece Ollama).
    - Ayar olarak config'teki default temperature / max_tokens değerlerini kullanır,
      parametre verilmişse override eder.
    """
    info = get_model_info(model_key)
    if info is None:
        logger.error("Bilinmeyen model key: %s", model_key)
        return f"❌ Tanımsız model: {model_key}"

    # Varsayılanları ayarla
    temp = temperature if temperature is not None else info.default_temperature
    max_toks = max_tokens if max_tokens is not None else info.default_max_tokens

    if info.provider == "ollama":
        return await _ollama_client.generate(
            model_name=info.name,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temp,
            max_tokens=max_toks,
            num_ctx=info.context_length,
        )

    # Diğer provider tipleri için ileride genişletebiliriz:
    # - openai-compatible
    # - custom HTTP
    logger.error("Desteklenmeyen provider: %s (model=%s)", info.provider, info.name)
    return f"❌ Desteklenmeyen model sağlayıcısı: {info.provider}"
