"""
services/llm/model_router_optimizer.py
---------------------------------------
MODEL ROUTER OPTIMIZER
Basit sorular → PHI (1-3s)
Orta sorular → MISTRAL (3-6s)
Karmaşık sorular → QWEN (6-10s)
Çok karmaşık → DEEPSEEK (10-15s)
"""

import logging
from typing import Tuple, Optional

from schemas.common import ChatMode, IntentLabel

logger = logging.getLogger(__name__)


# ============================================
# MODEL SEÇİM LOJİĞİ
# ============================================

def select_optimal_model(
    complexity: int,
    intent: IntentLabel,
    mode: ChatMode,
    message_length: int,
    force_model: Optional[str] = None
) -> Tuple[str, str]:
    """
    Optimal model seç (hız ve kalite dengesine göre)
    
    Args:
        complexity: Soru karmaşıklığı (1-10)
        intent: Intent label
        mode: Chat modu
        message_length: Mesaj uzunluğu (kelime sayısı)
        force_model: Zorla kullanılacak model
        
    Returns:
        (model_key, reasoning)
    """
    
    # Force model varsa kullan
    if force_model:
        return force_model, f"Forced: {force_model}"
    
    # ============================================
    # 1. BASIT SORULAR → PHI (Süper hızlı)
    # ============================================
    
    # Small talk HEMEN PHI
    if intent == IntentLabel.SMALL_TALK:
        return "phi", "Small talk → PHI (fastest)"
    
    # Çok kısa mesajlar → PHI
    if message_length <= 5:
        return "phi", f"Very short message ({message_length} words) → PHI"
    
    # Complexity 1-3 VE basit intent → PHI
    if complexity <= 3 and intent in [IntentLabel.QUESTION, IntentLabel.SMALL_TALK]:
        return "phi", f"Simple question (complexity={complexity}) → PHI"
    
    # ============================================
    # 2. ORTA SORULAR → MISTRAL (Hızlı ve kaliteli)
    # ============================================
    
    # Complexity 4-6 → MISTRAL
    if 4 <= complexity <= 6:
        return "mistral", f"Medium complexity ({complexity}) → MISTRAL"
    
    # Code help ama basit → MISTRAL
    if intent == IntentLabel.CODE_HELP and complexity <= 6:
        return "mistral", "Simple code help → MISTRAL"
    
    # Kısa mesajlar (6-15 kelime) → MISTRAL
    if 6 <= message_length <= 15:
        return "mistral", f"Short message ({message_length} words) → MISTRAL"
    
    # ============================================
    # 3. KARMAŞIK SORULAR → QWEN (Akıllı ve dengeli)
    # ============================================
    
    # Complexity 7-8 → QWEN
    if 7 <= complexity <= 8:
        return "qwen", f"Complex question ({complexity}) → QWEN"
    
    # Explanation veya Compare → QWEN
    if intent in [IntentLabel.EXPLAIN, IntentLabel.COMPARE]:
        return "qwen", f"Detailed intent ({intent.value}) → QWEN"
    
    # Orta-uzun mesajlar (16-30 kelime) → QWEN
    if 16 <= message_length <= 30:
        return "qwen", f"Medium-long message ({message_length} words) → QWEN"
    
    # Research mode → QWEN
    if mode == ChatMode.RESEARCH:
        return "qwen", "Research mode → QWEN"
    
    # ============================================
    # 4. ÇOK KARMAŞIK SORULAR → DEEPSEEK (En güçlü)
    # ============================================
    
    # Complexity 9-10 → DEEPSEEK
    if complexity >= 9:
        return "deepseek", f"Very complex ({complexity}) → DEEPSEEK (reasoning)"
    
    # Çok uzun mesajlar (30+ kelime) → DEEPSEEK
    if message_length > 30:
        return "deepseek", f"Very long message ({message_length} words) → DEEPSEEK"
    
    # Karmaşık kod soruları → DEEPSEEK
    if intent == IntentLabel.CODE_HELP and complexity >= 7:
        return "deepseek", "Complex code question → DEEPSEEK"
    
    # ============================================
    # 5. FALLBACK
    # ============================================
    
    # Default: complexity'ye göre karar ver
    if complexity <= 4:
        return "phi", f"Fallback simple ({complexity}) → PHI"
    elif complexity <= 7:
        return "mistral", f"Fallback medium ({complexity}) → MISTRAL"
    else:
        return "qwen", f"Fallback complex ({complexity}) → QWEN"


# ============================================
# PERFORMANCe MONİTÖRÜ
# ============================================

class ModelPerformanceMonitor:
    """Model performansını izle"""
    
    def __init__(self):
        self.stats = {
            'phi': {'count': 0, 'total_time': 0, 'avg_time': 0},
            'mistral': {'count': 0, 'total_time': 0, 'avg_time': 0},
            'qwen': {'count': 0, 'total_time': 0, 'avg_time': 0},
            'deepseek': {'count': 0, 'total_time': 0, 'avg_time': 0},
        }
    
    def record(self, model_key: str, response_time_ms: float):
        """Performans kaydı tut"""
        if model_key in self.stats:
            self.stats[model_key]['count'] += 1
            self.stats[model_key]['total_time'] += response_time_ms
            self.stats[model_key]['avg_time'] = (
                self.stats[model_key]['total_time'] / 
                self.stats[model_key]['count']
            )
    
    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        return self.stats
    
    def get_fastest_model(self) -> str:
        """En hızlı modeli bul"""
        valid_models = {k: v for k, v in self.stats.items() if v['count'] > 0}
        if not valid_models:
            return "phi"
        
        fastest = min(valid_models.items(), key=lambda x: x[1]['avg_time'])
        return fastest[0]


# Global monitor instance
_performance_monitor = ModelPerformanceMonitor()


def get_performance_stats() -> dict:
    """Performance istatistiklerini al"""
    return _performance_monitor.get_stats()


def record_model_performance(model_key: str, response_time_ms: float):
    """Model performansını kaydet"""
    _performance_monitor.record(model_key, response_time_ms)


# ============================================
# HYBRİD YAKLAŞIM (Öğrenerek İyileşen)
# ============================================

def select_model_with_learning(
    complexity: int,
    intent: IntentLabel,
    mode: ChatMode,
    message_length: int,
    previous_model: Optional[str] = None,
    previous_quality: Optional[float] = None
) -> Tuple[str, str]:
    """
    Öğrenerek model seç
    
    Eğer önceki model iyi performans gösterdiyse, benzer sorularda onu kullan
    """
    
    # İlk seçim
    model, reasoning = select_optimal_model(
        complexity, intent, mode, message_length, None
    )
    
    # Önceki model başarılıysa ve benzer bir soru ise, aynı modeli kullan
    if previous_model and previous_quality and previous_quality > 0.8:
        stats = _performance_monitor.get_stats()
        prev_stats = stats.get(previous_model, {})
        
        # Önceki model hızlıysa ve kaliteliyse tercih et
        if prev_stats.get('avg_time', 9999) < 8000:  # 8 saniyeden hızlıysa
            logger.info(f"Using previous successful model: {previous_model} (quality={previous_quality:.2f})")
            return previous_model, f"Learned: {previous_model} worked well before"
    
    return model, reasoning


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    # Test cases
    test_cases = [
        # (complexity, intent, mode, msg_len, expected_model)
        (2, IntentLabel.SMALL_TALK, ChatMode.FRIEND, 3, "phi"),
        (5, IntentLabel.QUESTION, ChatMode.NORMAL, 8, "mistral"),
        (8, IntentLabel.EXPLAIN, ChatMode.NORMAL, 20, "qwen"),
        (9, IntentLabel.CODE_HELP, ChatMode.CODE, 35, "deepseek"),
        (4, IntentLabel.CODE_HELP, ChatMode.CODE, 10, "mistral"),
    ]
    
    print("Model Selection Tests:")
    print("=" * 80)
    
    for complexity, intent, mode, msg_len, expected in test_cases:
        model, reasoning = select_optimal_model(complexity, intent, mode, msg_len, None)
        status = "✅" if model == expected else "⚠️"
        print(f"{status} Complexity={complexity}, Intent={intent.value}, Len={msg_len}")
        print(f"   Selected: {model.upper()} (expected: {expected.upper()})")
        print(f"   Reasoning: {reasoning}")
        print()