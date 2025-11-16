"""
backend/services/reasoning_engine.py
====================================
DÜŞÜNME SİSTEMİ - DeepSeek-R1 Tarzı Reasoning

Görev:
- Karmaşık soruları adım adım çöz
- Chain-of-thought reasoning
- Self-verification
- Sadece gerektiğinde kullan (hız optimizasyonu)

Özellikler:
✅ Akıllı reasoning tetikleme
✅ Multi-step düşünme
✅ Self-correction
✅ Reasoning log'lama
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass
from schemas.common import IntentLabel, ChatMode


@dataclass
class ReasoningResult:
    """Düşünme sonucu"""
    needs_reasoning: bool  # Reasoning gerekli mi?
    reasoning_steps: List[str]  # Düşünme adımları
    final_answer: str  # Final cevap
    confidence: float  # Güven skoru (0-1)
    reasoning_time_ms: float  # Düşünme süresi


class ReasoningEngine:
    """
    Düşünme motoru - Karmaşık problemler için
    """
    
    def __init__(self):
        # Reasoning gerektiren durumlar
        self.reasoning_triggers = {
            'high_complexity': 8,  # Complexity > 8
            'intents': [
                IntentLabel.CODE_HELP,
                IntentLabel.EXPLAIN,
                IntentLabel.COMPARE,
                IntentLabel.RECOMMENDATION,
            ],
            'keywords': [
                'neden', 'nasıl çalışır', 'açıkla',
                'karşılaştır', 'analiz et', 'çöz',
                'kanıtla', 'hesapla', 'tasarla',
            ]
        }
    
    def should_use_reasoning(
        self,
        query: str,
        intent: IntentLabel,
        complexity: int,
        mode: ChatMode
    ) -> bool:
        """
        Reasoning gerekli mi karar ver
        
        HIZLI CEVAP: Basit sorular için FALSE dön!
        """
        # Koşul 1: Çok basit sorular → NO
        if complexity <= 4:
            return False
        
        # Koşul 2: Small talk → NO
        if intent == IntentLabel.SMALL_TALK:
            return False
        
        # Koşul 3: Yüksek complexity → YES
        if complexity >= self.reasoning_triggers['high_complexity']:
            return True
        
        # Koşul 4: Özel intent'ler → YES
        if intent in self.reasoning_triggers['intents']:
            return True
        
        # Koşul 5: Keyword check
        query_lower = query.lower()
        if any(kw in query_lower for kw in self.reasoning_triggers['keywords']):
            return True
        
        # Koşul 6: Code mode → YES
        if mode == ChatMode.CODE:
            return True
        
        return False
    
    def build_reasoning_prompt(
        self,
        query: str,
        context: str,
        base_instructions: str
    ) -> str:
        """
        Düşünme sistemi için özel prompt oluştur
        
        DeepSeek-R1 tarzı format
        """
        reasoning_template = f"""
{base_instructions}

ÖNEMLİ: Bu karmaşık bir soru. Adım adım düşünmen gerekiyor.

DÜŞÜNME SÜRECİ:
1. Önce soruyu analiz et
2. Çözüm stratejisi belirle
3. Adım adım ilerle
4. Her adımı doğrula
5. Final cevabı ver

{context}

Kullanıcı sorusu: {query}

Şimdi düşünmeye başla (düşüncelerini açıkça yaz):
<thinking>
[Burada adım adım düşün]
</thinking>

<answer>
[Final cevabını buraya yaz]
</answer>
"""
        return reasoning_template
    
    def extract_reasoning_and_answer(
        self,
        model_output: str
    ) -> Tuple[List[str], str]:
        """
        Model output'undan düşünme ve cevabı ayır
        
        Format:
        <thinking>düşünme</thinking>
        <answer>cevap</answer>
        """
        import re
        
        # Thinking section'ı çıkar
        thinking_match = re.search(
            r'<thinking>(.*?)</thinking>',
            model_output,
            re.DOTALL | re.IGNORECASE
        )
        
        # Answer section'ı çıkar
        answer_match = re.search(
            r'<answer>(.*?)</answer>',
            model_output,
            re.DOTALL | re.IGNORECASE
        )
        
        reasoning_steps = []
        final_answer = ""
        
        if thinking_match:
            thinking_text = thinking_match.group(1).strip()
            # Adımlara böl
            reasoning_steps = [
                step.strip()
                for step in thinking_text.split('\n')
                if step.strip()
            ]
        
        if answer_match:
            final_answer = answer_match.group(1).strip()
        else:
            # Eğer <answer> tag'i yoksa, tüm output'u kullan
            final_answer = model_output
        
        return reasoning_steps, final_answer
    
    def verify_reasoning(
        self,
        reasoning_steps: List[str],
        final_answer: str,
        original_query: str
    ) -> Tuple[bool, float]:
        """
        Düşünme sürecini doğrula
        
        Returns:
            (is_valid, confidence_score)
        """
        confidence = 0.5  # Base confidence
        
        # 1. Reasoning adımları var mı?
        if reasoning_steps and len(reasoning_steps) >= 2:
            confidence += 0.2
        
        # 2. Final answer var mı?
        if final_answer and len(final_answer) > 20:
            confidence += 0.2
        
        # 3. Reasoning alakalı mı?
        if reasoning_steps:
            # Query'den keyword'ler
            query_words = set(original_query.lower().split())
            
            # Reasoning'de geçiyor mu?
            reasoning_text = ' '.join(reasoning_steps).lower()
            common_words = query_words & set(reasoning_text.split())
            
            if len(common_words) >= 2:
                confidence += 0.1
        
        is_valid = confidence >= 0.6
        
        return is_valid, min(1.0, confidence)


# ========================================
# GLOBAL INSTANCE
# ========================================

_reasoning_engine = ReasoningEngine()


def should_use_reasoning(
    query: str,
    intent: IntentLabel,
    complexity: int,
    mode: ChatMode
) -> bool:
    """Utility: Reasoning gerekli mi?"""
    return _reasoning_engine.should_use_reasoning(query, intent, complexity, mode)


def build_reasoning_prompt(
    query: str,
    context: str,
    base_instructions: str
) -> str:
    """Utility: Reasoning prompt oluştur"""
    return _reasoning_engine.build_reasoning_prompt(query, context, base_instructions)


def extract_reasoning_and_answer(model_output: str) -> Tuple[List[str], str]:
    """Utility: Reasoning ve cevabı ayır"""
    return _reasoning_engine.extract_reasoning_and_answer(model_output)


def verify_reasoning(
    reasoning_steps: List[str],
    final_answer: str,
    original_query: str
) -> Tuple[bool, float]:
    """Utility: Reasoning'i doğrula"""
    return _reasoning_engine.verify_reasoning(reasoning_steps, final_answer, original_query)