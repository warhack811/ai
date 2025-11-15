"""
services/quality_validator.py
-----------------------------
Cevap kalitesini değerlendirir
"""

import re
from typing import Tuple

class QualityValidator:
    """
    Output kalite kontrolü
    """
    
    def validate(self, output: str, user_query: str) -> Tuple[bool, float]:
        """
        Kaliteyi 0-1 arası skorla
        
        Returns:
            (is_valid, quality_score)
        """
        if not output or len(output.strip()) < 10:
            return False, 0.0
        
        score = 0.0
        
        # 1. Uzunluk kontrolü (10-5000 karakter arası ideal)
        length = len(output)
        if 50 <= length <= 3000:
            score += 0.2
        elif 10 <= length < 50:
            score += 0.1
        elif length > 3000:
            score += 0.15
        
        # 2. Türkçe karakter oranı
        turkish_ratio = self._turkish_char_ratio(output)
        score += turkish_ratio * 0.3
        
        # 3. Cümle yapısı (noktalama var mı?)
        has_structure = self._has_sentence_structure(output)
        if has_structure:
            score += 0.2
        
        # 4. Meta tag yok mu?
        has_no_tags = not self._has_meta_tags(output)
        if has_no_tags:
            score += 0.15
        
        # 5. Tekrar var mı?
        no_repetition = not self._has_repetition(output)
        if no_repetition:
            score += 0.15
        
        # Threshold: 0.5
        is_valid = score >= 0.5
        
        return is_valid, score
    
    def _turkish_char_ratio(self, text: str) -> float:
        """Türkçe karakter oranı"""
        turkish_chars = 'çğıöşüÇĞİÖŞÜ'
        turkish_count = sum(1 for c in text if c in turkish_chars)
        
        # Türkçe karakter varsa yüksek skor
        if turkish_count > 0:
            return min(1.0, turkish_count / 20)  # 20+ Türkçe karakter = 1.0
        
        # Türkçe karakter yoksa İngilizce olabilir (kabul edilir)
        return 0.5
    
    def _has_sentence_structure(self, text: str) -> bool:
        """Cümle yapısı var mı?"""
        # En az 1 noktalama var mı?
        return any(p in text for p in '.!?')
    
    def _has_meta_tags(self, text: str) -> bool:
        """Meta tag var mı?"""
        meta_patterns = [
            r'\[USER\]', r'\[ASSISTANT\]', r'\[INST\]',
            r'<\|im_start\|>', r'<\|im_end\|>',
        ]
        
        for pattern in meta_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _has_repetition(self, text: str) -> bool:
        """Tekrar var mı?"""
        sentences = re.split(r'[.!?]\s+', text)
        
        if len(sentences) < 2:
            return False
        
        # Aynı cümle 2+ kez geçiyor mu?
        seen = set()
        for sent in sentences:
            sent_clean = sent.strip().lower()
            if sent_clean in seen:
                return True
            seen.add(sent_clean)
        
        return False


# Global instance
_quality_validator = QualityValidator()

def validate_quality(output: str, user_query: str) -> Tuple[bool, float]:
    """Utility function"""
    return _quality_validator.validate(output, user_query)