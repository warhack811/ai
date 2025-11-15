"""
services/llm/model_manager.py - İYİLEŞTİRİLMİŞ VERSİYON
-----------------------------
Daha iyi varsayılan ayarlar ve hata yönetimi
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from .prompt_templates import get_prompt_builder
import httpx
from schemas.common import ChatMode
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LLMModelInfo:
    key: str
    name: str
    display_name: str
    provider: str
    context_length: int
    default_temperature: float
    default_max_tokens: int
    is_primary: bool = False


def _load_models_from_settings() -> Dict[str, LLMModelInfo]:
    """Config'den modelleri yükle."""
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


_MODEL_REGISTRY: Dict[str, LLMModelInfo] = _load_models_from_settings()


class OllamaClient:
    """Ollama HTTP API client."""
    
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
    
    async def list_models(self) -> Dict[str, bool]:
        """Mevcut modelleri listele."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.error("Ollama /tags HTTP %s", resp.status_code)
                    return {}
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return {m: True for m in models}
        except Exception as e:
            logger.error("Ollama /tags hatası: %s", e)
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
        """Model ile cevap üret - İYİLEŞTİRİLMİŞ AYARLAR."""
        url = f"{self.base_url}/api/generate"
        
        # DAHA İYİ VARSAYILANLAR
        temp = temperature if temperature is not None else 0.7  # 0.3 -> 0.7
        num_predict = max_tokens if max_tokens is not None else 2048  # 512 -> 2048
        ctx = num_ctx if num_ctx is not None else 8192  # 4096 -> 8192
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(temp),
                "num_predict": int(num_predict),
                "num_ctx": int(ctx),
                # İyileştirilmiş sampling parametreleri
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "stop": ["[USER]", "[ASSISTANT]", "[INST]", "[/INST]"],  # Meta tag'leri durdur
            },
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        logger.info(f"Ollama request: model={model_name}, temp={temp}, max_tokens={num_predict}")
        
        try:
            # Timeout'u artır (60 saniye)
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException:
            logger.error("Ollama timeout (model=%s)", model_name)
            return "⏱️ Model çok yavaş yanıt verdi. Lütfen daha kısa soru sorun."
        except Exception as e:
            logger.error("Ollama bağlantı hatası: %s", e)
            return f"❌ Ollama'ya bağlanılamadı: {e}"
        
        if resp.status_code == 404:
            logger.error("Model bulunamadı: %s", model_name)
            return (
                f"❌ Model '{model_name}' bulunamadı.\n"
                f"Çözüm: ollama pull {model_name}"
            )
        
        if resp.status_code != 200:
            logger.error("Ollama HTTP %s: %s", resp.status_code, resp.text)
            return f"❌ Ollama hatası (HTTP {resp.status_code})"
        
        try:
            data = resp.json()
        except Exception as e:
            logger.error("JSON parse hatası: %s", e)
            return "❌ Model cevabı okunamadı."
        
        text = data.get("response", "").strip()
        
        if not text:
            logger.warning("Boş cevap (model=%s)", model_name)
            return "Üzgünüm, cevap üretemedim. Lütfen sorunuzu farklı şekilde sorun."
        
        logger.info(f"Ollama response length: {len(text)} chars")
        
        return text


_ollama_client = OllamaClient(base_url=str(settings.llm.ollama_base_url))


def get_model_info(key: str) -> Optional[LLMModelInfo]:
    """Model bilgisini al."""
    return _MODEL_REGISTRY.get(key)


def get_primary_model() -> Optional[LLMModelInfo]:
    """Primary modeli al."""
    for info in _MODEL_REGISTRY.values():
        if info.is_primary:
            return info
    return _MODEL_REGISTRY.get("qwen")


def list_all_models() -> Dict[str, LLMModelInfo]:
    """Tüm modelleri listele."""
    return dict(_MODEL_REGISTRY)


async def test_llm_health() -> Dict[str, any]:
    """LLM sağlık kontrolü."""
    available = await _ollama_client.list_models()
    
    models_health = {}
    for key, info in _MODEL_REGISTRY.items():
        if info.provider != "ollama":
            models_health[key] = {
                "status": "unknown",
                "reason": f"provider={info.provider}",
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
    prompt: str,  # Artık kullanılmayacak (deprecated)
    system_prompt: str,  # Artık kullanılmayacak (deprecated)
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    # YENİ PARAMETRELER:
    user_message: str = "",
    context: str = "",
    mode: ChatMode = ChatMode.NORMAL,
) -> str:
    """
    Model ile cevap üret - YENİ VERSİYON
    Artık native prompt templates kullanıyor
    """
    info = get_model_info(model_key)
    if info is None:
        logger.error("Bilinmeyen model: %s", model_key)
        return f"❌ Tanımsız model: {model_key}"
    
    # Varsayılanları kullan
    temp = temperature if temperature is not None else info.default_temperature
    max_toks = max_tokens if max_tokens is not None else info.default_max_tokens
    
    # YENİ: Prompt template builder kullan
    from .prompt_templates import get_prompt_builder
    builder = get_prompt_builder(model_key, mode)
    
    # Eğer user_message verilmişse native template kullan
    if user_message:
        final_prompt = builder.build_user_prompt(
            user_message=user_message,
            context=context
        )
    else:
        # Backward compatibility: Eski kod için
        final_prompt = prompt
    
    logger.debug(
        "Generate with model: %s, temp=%.2f, max_tokens=%d",
        model_key,
        temp,
        max_toks,
    )
    
    if info.provider == "ollama":
        return await _ollama_client.generate(
            model_name=info.name,
            prompt=final_prompt,
            system_prompt="",  # Artık system prompt template içinde
            temperature=temp,
            max_tokens=max_toks,
            num_ctx=info.context_length,
        )
    
    logger.error("Desteklenmeyen provider: %s", info.provider)
    return f"❌ Desteklenmeyen provider: {info.provider}"