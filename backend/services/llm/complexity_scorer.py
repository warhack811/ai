"""
services/llm/complexity_scorer.py - İYİLEŞTİRİLMİŞ
---------------------------------------------------
✅ Daha hassas skorlama
✅ Öneri/karşılaştırma intent'leri eklendi
✅ Gereksiz QWEN kullanımı azaltıldı
"""

import re
from typing import List
from schemas.common import ChatMode, IntentLabel

class ComplexityScorer:
    """
    Mesajın karmaşıklığını skorlar
    
    Yeni Skorlama:
    0-3:   Basit → Phi
    4-6:   Orta → Mistral (QWEN yerine!)
    7-8:   Karmaşık → Mistral veya QWEN (dikkatli)
    9-10:  Reasoning → DeepSeek
    """
    
    def score(self, query: str, mode: ChatMode, intent: IntentLabel = None) -> int:
        """
        Ana scoring fonksiyonu
        
        Returns:
            0-10 arası complexity score
        """
        score = 0
        query_lower = query.lower()
        
        # ============================================================
        # 1. Basit Selamlaşma / Small Talk (En Düşük Öncelik)
        # ============================================================
        greeting_keywords = [
            'merhaba', 'selam', 'hello', 'hi', 'hey', 'günaydın',
            'iyi günler', 'nasılsın', 'how are you', "naber", "ne haber"
        ]
        word_count = len(query.split())
        
        if any(kw in query_lower for kw in greeting_keywords) and word_count < 8:
            return 1  # Direkt en düşük skor
        
        # ============================================================
        # 2. Uzunluk Bazlı (Temel Skor)
        # ============================================================
        if word_count < 5:
            score += 1
        elif word_count < 12:
            score += 2
        elif word_count < 25:
            score += 4
        else:
            score += 5  # Uzun sorular biraz daha yüksek
        
        # ============================================================
        # 3. Mode Bazlı Ayarlama
        # ============================================================
        mode_scores = {
            ChatMode.NORMAL: 0,
            ChatMode.FRIEND: 0,
            ChatMode.CODE: 2,        # Kod soruları orta seviye
            ChatMode.CREATIVE: 1,    # Yaratıcı içerik orta seviye
            ChatMode.RESEARCH: 3,    # Araştırma biraz daha yüksek
            ChatMode.TURKISH_TEACHER: 2,
        }
        score += mode_scores.get(mode, 0)
        
        # ============================================================
        # 4. Kod İsteği (Orta Seviye - Mistral Yeterli)
        # ============================================================
        code_keywords = [
            'kod', 'code', 'program', 'fonksiyon', 'function', 
            'class', 'sınıf', 'python', 'javascript', 'java',
            'algoritma', 'algorithm', 'debug', 'hata', 'error',
            'yazılım', 'software', 'uygulama', 'app'
        ]
        if any(kw in query_lower for kw in code_keywords):
            score += 2  # 3'ten 2'ye düşürüldü (Mistral yeterli)
            
            # Sadece çok detaylı açıklama istiyorsa +1
            if any(kw in query_lower for kw in ['detaylı açıkla', 'neden böyle', 'mantığı']):
                score += 1
        
        # ============================================================
        # 5. Reasoning / Analiz Gerektiren (Yüksek)
        # ============================================================
        reasoning_keywords = [
            'neden', 'why', 'nasıl çalışır', 'how does it work',
            'analiz et', 'analyze', 'mantığı', 'logic',
            'strateji', 'strategy', 'çöz', 'solve',
            'hesapla', 'calculate', 'kanıtla', 'prove'
        ]
        reasoning_count = sum(1 for kw in reasoning_keywords if kw in query_lower)
        score += min(reasoning_count * 2, 3)  # Max 3 puan
        
        # ============================================================
        # 6. Karşılaştırma / Öneri (Orta-Yüksek)
        # ============================================================
        comparison_keywords = [
            'karşılaştır', 'compare', 'fark', 'difference',
            'hangisi', 'which one', 'vs', 'ile arasında',
            'avantaj', 'dezavantaj', 'pros', 'cons',
            'daha iyi', 'better', 'tercih', 'prefer'
        ]
        if any(kw in query_lower for kw in comparison_keywords):
            score += 2  # Orta seviye (Mistral yeterli)
        
        recommendation_keywords = [
            'öner', 'tavsiye', 'öneri', 'recommend', 'suggest',
            'ne almalıyım', 'what should i', 'seçmeliyim', 'should i choose'
        ]
        if any(kw in query_lower for kw in recommendation_keywords):
            score += 2  # Öneri de orta seviye
        
        # ============================================================
        # 7. Çoklu Soru/Görev
        # ============================================================
        question_marks = query.count('?')
        if question_marks > 1:
            score += 2
        
        # ============================================================
        # 8. Matematiksel / Teknik İçerik
        # ============================================================
        if any(char in query for char in ['∫', '∑', 'π', '√', '≈', '≤', '≥', 'x²', 'f(x)']):
            score += 3  # Matematik yüksek öncelik
        
        # ============================================================
        # 9. Liste/Numaralandırma (Düşük)
        # ============================================================
        list_keywords = ['listele', 'list', 'say', 'enumerate', 'madde', 'örnekler']
        if any(kw in query_lower for kw in list_keywords):
            score += 1  # Liste basit iş
        
        # ============================================================
        # 10. Intent Bazlı Ayarlama (En Önemli!)
        # ============================================================
        if intent:
            intent_adjustments = {
                IntentLabel.SMALL_TALK: -3,           # En düşük
                IntentLabel.TRANSLATE: -1,            # Basit
                IntentLabel.SUMMARIZE: 0,             # Orta
                IntentLabel.QUESTION: 0,              # Orta
                IntentLabel.EXPLAIN: 1,               # Orta-yüksek
                IntentLabel.CODE_HELP: 1,             # Orta (Mistral yeterli)
                IntentLabel.TASK_REQUEST: 2,          # Orta-yüksek
                IntentLabel.DOCUMENT_QUESTION: 2,     # Orta-yüksek
                IntentLabel.WEB_SEARCH: 2,            # Orta-yüksek
                IntentLabel.EMOTIONAL_SUPPORT: 3,     # Yüksek (QWEN lazım)
                IntentLabel.REFLECTION: 3,            # Yüksek (self-reflection)
            }
            score += intent_adjustments.get(intent, 0)
        
        # ============================================================
        # 11. Final: 0-10 Arası Sınırla
        # ============================================================
        final_score = max(0, min(10, score))
        
        return final_score
    
    def get_recommended_model(self, score: int) -> str:
        """
        Complexity score'a göre model önerisi
        
        UPDATED: Mistral daha çok kullanılıyor
        """
        if score <= 3:
            return "phi"
        elif score <= 6:
            return "mistral"  # QWEN yerine Mistral!
        elif score <= 8:
            return "mistral"  # Hala Mistral (QWEN sadece 9-10'da)
        else:
            return "qwen"     # Sadece çok karmaşık durumlarda
    
    def explain_score(self, score: int) -> str:
        """
        Score'u açıkla (debug için)
        """
        if score <= 3:
            return "Basit soru - Phi yeterli"
        elif score <= 6:
            return "Orta zorluk - Mistral yeterli"
        elif score <= 8:
            return "Karmaşık - Mistral veya QWEN"
        else:
            return "Çok karmaşık - QWEN veya DeepSeek"


# Global instance
_complexity_scorer = ComplexityScorer()

def score_complexity(query: str, mode: ChatMode, intent: IntentLabel = None) -> int:
    """Utility function"""
    return _complexity_scorer.score(query, mode, intent)

def get_model_for_complexity(score: int) -> str:
    """Utility function"""
    return _complexity_scorer.get_recommended_model(score)