"""
services/cache_manager.py
-------------------------
Smart caching layer - Pahalı operasyonları cache'ler
"""

import time
import hashlib
import json
from typing import Optional, Any, Dict
from functools import lru_cache

class CacheManager:
    """
    Multi-level caching:
    - Memory cache (in-process)
    - LRU cache (function level)
    """
    
    def __init__(self):
        self.memory_cache: Dict[str, tuple] = {}  # {key: (value, expires_at)}
        self.default_ttl = 3600  # 1 hour
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Cache key oluştur"""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den değer al"""
        if key in self.memory_cache:
            value, expires_at = self.memory_cache[key]
            if time.time() < expires_at:
                return value
            else:
                # Expired, sil
                del self.memory_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Cache'e değer yaz"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        self.memory_cache[key] = (value, expires_at)
    
    def delete(self, key: str):
        """Cache'den sil"""
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    def clear(self):
        """Tüm cache'i temizle"""
        self.memory_cache.clear()
    
    # ============================================
    # SPECIFIC CACHE METHODS
    # ============================================
    
    def get_cached_intent(self, query: str, mode: str) -> Optional[Any]:
        """Intent detection cache"""
        key = self._make_key("intent", f"{query}:{mode}")
        return self.get(key)
    
    def cache_intent(self, query: str, mode: str, intent: Any, ttl: int = 3600):
        """Intent'i cache'le"""
        key = self._make_key("intent", f"{query}:{mode}")
        self.set(key, intent, ttl)
    
    def get_cached_emotion(self, query: str) -> Optional[Any]:
        """Emotion analysis cache"""
        key = self._make_key("emotion", query)
        return self.get(key)
    
    def cache_emotion(self, query: str, emotion_data: Any, ttl: int = 3600):
        """Emotion'ı cache'le"""
        key = self._make_key("emotion", query)
        self.set(key, emotion_data, ttl)
    
    def get_cached_rag(self, query: str) -> Optional[tuple]:
        """RAG results cache"""
        key = self._make_key("rag", query)
        return self.get(key)
    
    def cache_rag(self, query: str, context_text: str, sources: list, ttl: int = 3600):
        """RAG sonuçlarını cache'le"""
        key = self._make_key("rag", query)
        self.set(key, (context_text, sources), ttl)
    
    def get_cached_profile(self, user_id: str) -> Optional[str]:
        """Profile summary cache"""
        key = self._make_key("profile", user_id)
        return self.get(key)
    
    def cache_profile(self, user_id: str, profile_summary: str, ttl: int = 1800):
        """Profile'ı cache'le (30 min)"""
        key = self._make_key("profile", user_id)
        self.set(key, profile_summary, ttl)
    
    def invalidate_user_cache(self, user_id: str):
        """Kullanıcıya ait tüm cache'i temizle"""
        keys_to_delete = [k for k in self.memory_cache.keys() if user_id in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
    
    # ============================================
    # STATS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri"""
        now = time.time()
        active_count = sum(1 for _, expires in self.memory_cache.values() if expires > now)
        
        return {
            "total_keys": len(self.memory_cache),
            "active_keys": active_count,
            "expired_keys": len(self.memory_cache) - active_count,
        }
    
    def cleanup_expired(self):
        """Expired cache'leri temizle"""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self.memory_cache.items() if exp <= now]
        for key in expired_keys:
            del self.memory_cache[key]
        return len(expired_keys)


# Global instance
_cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Singleton cache manager"""
    return _cache_manager