"""
services/llm/complexity_scorer.py
----------------------------------
Query complexity scoring - Sorunu analiz edip 0-10 arası zorluk skoru verir
"""

import re
from typing import List
from schemas.common import ChatMode, IntentLabel

class ComplexityScorer:
    """
    Mesajın karmaşıklığını skorlar ve uygun modeli seçmeye yardımcı olur
    
    Skorlama:
    0-3:   Basit (Phi yeterli)
    4-6:   Orta (Mistral)
    7-8:   Karmaşık (Qwen)
    9-10:  Reasoning gerektiren (DeepSeek)
    """
    
    def score(self, query: str, mode: ChatMode, intent: IntentLabel = None) -> int:
        """
        Ana scoring fonksiyonu
        
        Returns:
            0-10 arası complexity score
        """
        score = 0
        query_lower = query.lower()
        
        # 1. Uzunluk bazlı skorlama
        word_count = len(query.split())
        if word_count < 5:
            score += 0
        elif word_count < 15:
            score += 2
        elif word_count < 30:
            score += 4
        else:
            score += 6
        
        # 2. Mode bazlı skorlama
        mode_scores = {
            ChatMode.NORMAL: 0,
            ChatMode.FRIEND: 0,
            ChatMode.CODE: 3,
            ChatMode.CREATIVE: 2,
            ChatMode.RESEARCH: 4,
            ChatMode.TURKISH_TEACHER: 2,
        }
        score += mode_scores.get(mode, 0)
        
        # 3. Kod isteği kontrolü
        code_keywords = [
            'kod', 'code', 'program', 'fonksiyon', 'function', 
            'class', 'sınıf', 'python', 'javascript', 'java',
            'algoritma', 'algorithm', 'debug', 'hata', 'error'
        ]
        if any(kw in query_lower for kw in code_keywords):
            score += 3
            # Kod + açıklama istiyorsa daha yüksek
            if any(kw in query_lower for kw in ['açıkla', 'explain', 'neden', 'why']):
                score += 2
        
        # 4. Analiz/düşünme gerektiren kelimeler
        reasoning_keywords = [
            'neden', 'why', 'nasıl', 'how', 'açıkla', 'explain',
            'analiz', 'analyze', 'karşılaştır', 'compare', 'fark',
            'difference', 'avantaj', 'dezavantaj', 'pros', 'cons',
            'strateji', 'strategy', 'plan', 'çöz', 'solve'
        ]
        reasoning_count = sum(1 for kw in reasoning_keywords if kw in query_lower)
        score += min(reasoning_count * 2, 4)  # Max 4 puan
        
        # 5. Çoklu soru/görev
        question_marks = query.count('?')
        if question_marks > 1:
            score += 2
        
        # 6. Özel karakterler / matematiksel içerik
        if any(char in query for char in ['∫', '∑', 'π', '√', '≈', '≤', '≥']):
            score += 2
        
        # 7. Liste/numaralandırma isteği
        list_keywords = ['listele', 'list', 'say', 'enumerate', 'madde', 'örnekler']
        if any(kw in query_lower for kw in list_keywords):
            score += 1
        
        # 8. Selamlama/small talk (düşük skor)
        greeting_keywords = [
            'merhaba', 'selam', 'hello', 'hi', 'hey', 'günaydın',
            'iyi günler', 'nasılsın', 'how are you', "naber", "naber"
        ]
        if any(kw in query_lower for kw in greeting_keywords) and word_count < 10:
            return 1  # Direkt en düşük skor
        
        # 9. Intent bazlı ayarlama (varsa)
        if intent:
            intent_adjustments = {
                IntentLabel.SMALL_TALK: -2,
                IntentLabel.QUESTION: 0,
                IntentLabel.TASK_REQUEST: 1,
                IntentLabel.EXPLAIN: 2,
                IntentLabel.CODE_HELP: 3,
                IntentLabel.SUMMARIZE: 2,
                IntentLabel.TRANSLATE: 1,
                IntentLabel.WEB_SEARCH: 2,
                IntentLabel.DOCUMENT_QUESTION: 3,
            }
            score += intent_adjustments.get(intent, 0)
        
        # Final: 0-10 arası sınırla
        final_score = max(0, min(10, score))
        
        return final_score
    
    def get_recommended_model(self, score: int) -> str:
        """
        Complexity score'a göre model önerisi
        """
        if score <= 3:
            return "phi"
        elif score <= 6:
            return "mistral"
        elif score <= 8:
            return "qwen"
        else:
            return "deepseek"
    
    def explain_score(self, score: int) -> str:
        """
        Score'u açıkla (debug için)
        """
        if score <= 3:
            return "Basit soru - Hızlı cevap yeterli"
        elif score <= 6:
            return "Orta zorluk - Standart işlem"
        elif score <= 8:
            return "Karmaşık - Detaylı analiz gerekli"
        else:
            return "Çok karmaşık - Derin düşünme gerekli"


# Global instance
_complexity_scorer = ComplexityScorer()

def score_complexity(query: str, mode: ChatMode, intent: IntentLabel = None) -> int:
    """Utility function"""
    return _complexity_scorer.score(query, mode, intent)

def get_model_for_complexity(score: int) -> str:
    """Utility function"""
    return _complexity_scorer.get_recommended_model(score)