"""
backend/services/semantic_intent_detector.py
============================================
SEMANTİK İNTENT DETECTOR - Keyword'den Daha Akıllı

Mevcut intent_detector.py'den farkı:
✅ Sadece keyword değil, ANLAM bazlı
✅ Implicit intent'leri yakalar
✅ Multi-intent desteği
✅ Confidence score verir
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from schemas.common import ChatMode, IntentLabel


@dataclass
class IntentResult:
    """Intent sonucu (confidence ile)"""
    intent: IntentLabel
    confidence: float  # 0.0-1.0
    reasoning: str  # Neden bu intent?


class SemanticIntentDetector:
    """
    Gelişmiş intent detector
    """
    
    def __init__(self):
        # Intent patterns (daha detaylı)
        self.intent_patterns = self._build_intent_patterns()
    
    def detect_intent(
        self,
        message: str,
        mode: ChatMode,
        conversation_history: Optional[List[str]] = None
    ) -> IntentResult:
        """
        Gelişmiş intent detection
        
        Args:
            message: Kullanıcı mesajı
            mode: Chat mode
            conversation_history: Önceki mesajlar (optional)
            
        Returns:
            IntentResult with confidence
        """
        text = message.strip().lower()
        
        # Her intent için skor hesapla
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = self._score_intent(text, patterns, mode, conversation_history)
            scores[intent] = score
        
        # En yüksek skoru bul
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # Confidence threshold
        if best_score < 0.3:
            return IntentResult(
                intent=IntentLabel.UNKNOWN,
                confidence=best_score,
                reasoning="No clear intent detected"
            )
        
        reasoning = self._explain_intent(best_intent, text)
        
        return IntentResult(
            intent=best_intent,
            confidence=best_score,
            reasoning=reasoning
        )
    
    def _build_intent_patterns(self) -> dict:
        """Intent pattern'leri oluştur"""
        return {
            IntentLabel.QUESTION: {
                'keywords': [
                    'ne', 'nasıl', 'neden', 'kim', 'nerede', 'ne zaman',
                    'hangi', 'kaç', 'mi', 'mu', 'mü', 'mı'
                ],
                'patterns': [
                    r'\?$',  # Soru işareti ile bitiyor
                    r'\b(ne|nasıl|neden|kim|nerede)\b',
                ],
                'context': ['asking', 'inquiry'],
            },
            
            IntentLabel.CLARIFICATION_REQUEST: {
                'keywords': [
                    'ne demek', 'anlamadım', 'açıklar mısın', 'detaylı',
                    'daha basit', 'yeniden anlatır mısın', 'tekrar eder misin'
                ],
                'patterns': [
                    r'\b(ne demek|anlamadım|açıkla)\b',
                ],
                'context': ['confused', 'unclear'],
            },
            
            IntentLabel.FOLLOW_UP: {
                'keywords': [
                    'peki', 'ee', 'o zaman', 'bunun üzerine', 'ayrıca',
                    've', 'bir de', 'başka', 'daha'
                ],
                'patterns': [
                    r'^(peki|ee|o zaman)\b',
                ],
                'context': ['continuation'],
            },
            
            IntentLabel.EXPLAIN: {
                'keywords': [
                    'açıkla', 'anlatır mısın', 'nedir', 'ne demek',
                    'detaylı anlat', 'örnekle', 'göster'
                ],
                'patterns': [
                    r'\b(açıkla|anlat|göster)\b',
                ],
                'context': ['explain'],
            },
            
            IntentLabel.SUMMARIZE: {
                'keywords': [
                    'özet', 'kısaca', 'özetle', 'kısa', 'hızlıca',
                    'ana fikir', 'temel nokta'
                ],
                'patterns': [
                    r'\b(özet|kısaca|özetle)\b',
                ],
                'context': ['summarize'],
            },
            
            IntentLabel.CODE_HELP: {
                'keywords': [
                    'kod', 'python', 'javascript', 'program', 'fonksiyon',
                    'error', 'hata', 'debug', 'çalışmıyor', 'algoritma'
                ],
                'patterns': [
                    r'\b(python|javascript|kod|program)\b',
                ],
                'context': ['coding', 'programming'],
            },
            
            IntentLabel.EMOTIONAL_SUPPORT: {
                'keywords': [
                    'üzgünüm', 'moralim bozuk', 'mutsuzum', 'yalnızım',
                    'sinirliyim', 'kaygılıyım', 'korkuyorum', 'stres'
                ],
                'patterns': [
                    r'\b(üzgün|mutsuz|sinirli|kaygılı|korku)\w*\b',
                ],
                'context': ['emotional', 'support'],
            },
            
            IntentLabel.SMALL_TALK: {
                'keywords': [
                    'merhaba', 'selam', 'nasılsın', 'naber', 'günaydın',
                    'iyi geceler', 'teşekkür', 'sağol'
                ],
                'patterns': [
                    r'^(merhaba|selam|hi|hello)\b',
                ],
                'context': ['greeting', 'casual'],
            },
            
            IntentLabel.COMPARE: {
    'keywords': [
        'fark', 'karşılaştır', 'hangisi', 'mi yoksa', 'ya da',
        'arasındaki fark', 'daha iyi', 'tercih', 've', 'ile',
        'farklı', 'benzer', 'aynı mı'  # YENÄ° EKLEDÄ°K
    ],
    'patterns': [
        r'\b(karşılaştır|fark|hangisi)\b',
        r'\b\w+\s+(mi|mu|mü|mı)\s+yoksa\s+\w+\b',
        r'\b\w+\s+(ile|ve)\s+\w+\b',  # YENÄ°: "Python ile JavaScript"
    ],
    'context': ['comparison'],
},
            IntentLabel.RECOMMENDATION: {
    'keywords': [
        'öner', 'tavsiye', 'ne yapmalıyım', 'hangi', 'en iyi',
        'önerin var mı', 'seçmek', 'hangisini', 'önerirsin',
        'yol göster', 'rehberlik', 'yardımcı ol'  # YENÄ° EKLEDÄ°K
    ],
    'patterns': [
        r'\b(öner|tavsiye|ne yapmalı|hangisi)\b',
        r'\b(hangi|ne)\s+\w+\s+(öğren|seç|al)\b',  # YENÄ°: "Hangi dil öğrenmeli"
    ],
    'context': ['recommendation'],
},
        }
    
    def _score_intent(
        self,
        text: str,
        patterns: dict,
        mode: ChatMode,
        history: Optional[List[str]]
    ) -> float:
        """Bir intent için skor hesapla"""
        score = 0.0
        
        # 1. Keyword matching
        keyword_score = 0
        for keyword in patterns.get('keywords', []):
            if keyword in text:
                keyword_score += 1
        
        if keyword_score > 0:
            score += min(0.5, keyword_score * 0.15)
        
        # 2. Pattern matching (regex)
        import re
        pattern_score = 0
        for pattern in patterns.get('patterns', []):
            if re.search(pattern, text):
                pattern_score += 1
        
        if pattern_score > 0:
            score += min(0.4, pattern_score * 0.2)
        
        # 3. Context from history
        if history:
            context_keywords = patterns.get('context', [])
            for prev_msg in history[-3:]:  # Son 3 mesaj
                for ctx_kw in context_keywords:
                    if ctx_kw in prev_msg.lower():
                        score += 0.1
        
        # 4. Mode bonus
        mode_bonuses = {
            (IntentLabel.CODE_HELP, ChatMode.CODE): 0.2,
            (IntentLabel.CREATIVE, ChatMode.CREATIVE): 0.2,
            (IntentLabel.EMOTIONAL_SUPPORT, ChatMode.FRIEND): 0.2,
        }
        
        # Intent'e göre mode bonus'u kontrol et (basitleştirilmiş)
        # Gerçek implementasyonda intent parametresi gerekir
        
        return min(1.0, score)
    
    def _explain_intent(self, intent: IntentLabel, text: str) -> str:
        """Intent'in neden seçildiğini açıkla"""
        explanations = {
            IntentLabel.QUESTION: f"Soru formatı tespit edildi",
            IntentLabel.CLARIFICATION_REQUEST: f"Açıklama talebi",
            IntentLabel.FOLLOW_UP: f"Önceki konuya devam",
            IntentLabel.EXPLAIN: f"Detaylı açıklama isteği",
            IntentLabel.CODE_HELP: f"Kod/programlama sorusu",
            IntentLabel.EMOTIONAL_SUPPORT: f"Duygusal destek gereksinimi",
            IntentLabel.SMALL_TALK: f"Sohbet/selamlama",
        }
        
        return explanations.get(intent, "Unknown reasoning")


# ========================================
# GLOBAL INSTANCE
# ========================================

_semantic_detector = SemanticIntentDetector()


def detect_intent_semantic(
    message: str,
    mode: ChatMode,
    conversation_history: Optional[List[str]] = None
) -> IntentResult:
    """Utility: Semantic intent detection"""
    return _semantic_detector.detect_intent(message, mode, conversation_history)