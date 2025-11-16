"""
services/quality_validator.py - DAHA ESNEK VERSİYON
---------------------------------------------------
✅ Daha toleranslı kalite kontrolü
✅ Timeout sorunlarını azaltır
✅ "Alakasız" hatasını azaltır
"""

import re
from typing import Tuple, List


class QualityValidator:
    """
    Output kalite kontrolü - Esnek versiyon
    """
    
    def validate(self, output: str, user_query: str) -> Tuple[bool, float]:
        """
        Kaliteyi 0-1 arası skorla (DAHA ESNEK)
        
        Returns:
            (is_valid, quality_score)
        """
        if not output or len(output.strip()) < 5:
            return False, 0.0
        
        score = 0.0
        issues: List[str] = []
        
        # ============================================================
        # 1. Uzunluk Kontrolü (Daha esnek)
        # ============================================================
        length = len(output)
        if 30 <= length <= 5000:
            score += 0.25  # Geniş range, yüksek skor
        elif 10 <= length < 30:
            score += 0.15  # Kısa ama kabul edilebilir
        elif length > 5000:
            score += 0.20
        
        # ============================================================
        # 2. Soru-Cevap İlgisi (Daha toleranslı)
        # ============================================================
        relevance_score = self._calculate_relevance(user_query, output)
        score += relevance_score * 0.25  # %25 ağırlık (düşürüldü)
        
        if relevance_score < 0.2:  # 0.3'ten 0.2'ye düşürüldü
            issues.append("Cevap soruyla zayıf ilişkili")
        
        # ============================================================
        # 3. Türkçe Kalitesi (Daha esnek)
        # ============================================================
        turkish_quality = self._check_turkish_quality(output, user_query)
        score += turkish_quality * 0.2
        
        # ============================================================
        # 4. Cümle Yapısı
        # ============================================================
        has_structure = self._has_sentence_structure(output)
        if has_structure:
            score += 0.15
        
        # ============================================================
        # 5. Meta Tag Kontrolü
        # ============================================================
        has_no_tags = not self._has_meta_tags(output)
        if has_no_tags:
            score += 0.1
        else:
            issues.append("Meta tag bulundu")
        
        # ============================================================
        # 6. Tekrar Kontrolü (Daha esnek)
        # ============================================================
        no_repetition = not self._has_repetition(output)
        if no_repetition:
            score += 0.05
        
        # ============================================================
        # ÖNEMLI: Threshold 0.4'e düşürüldü (0.5'ten)
        # ============================================================
        is_valid = score >= 0.4  # Daha toleranslı
        
        return is_valid, score
    
    def _calculate_relevance(self, query: str, output: str) -> float:
        """
        Soru-cevap ilgisi (DAHA TOLERANSLI)
        """
        # Çok kısa sorular için yüksek skor
        if len(query) < 15:
            return 0.9  # 0.8'den 0.9'a artırıldı
        
        query_lower = query.lower()
        output_lower = output.lower()
        
        # Basit kelime karşılaştırması
        query_words = set(self._clean_words(query_lower))
        output_words = set(self._clean_words(output_lower))
        
        if len(query_words) == 0:
            return 0.7  # 0.5'ten 0.7'ye artırıldı
        
        # Ortak kelime oranı
        common_words = query_words & output_words
        overlap_ratio = len(common_words) / len(query_words)
        
        # Bonus puanlar (daha cömert)
        bonus = 0.0
        
        # 1. Kod sorusu
        if any(kw in query_lower for kw in ['kod', 'code', 'python', 'javascript', 'fonksiyon']):
            if '```' in output or 'def ' in output or 'function ' in output or 'for ' in output:
                bonus += 0.3  # 0.2'den 0.3'e artırıldı
        
        # 2. Açıklama isteği
        if any(kw in query_lower for kw in ['açıkla', 'explain', 'nedir', 'anlat']):
            if len(output) > 100:  # 200'den 100'e düşürüldü
                bonus += 0.2  # 0.1'den 0.2'ye artırıldı
        
        # 3. Soru kelimesi varsa cevap kabul edilebilir
        if any(kw in query_lower for kw in ['nedir', 'ne', 'nasıl', 'neden', 'kim', 'ne zaman']):
            bonus += 0.2
        
        # Final skor (minimum 0.3 garantili)
        final_score = max(0.3, min(1.0, overlap_ratio + bonus))
        
        return final_score
    
    def _clean_words(self, text: str) -> List[str]:
        """Kelimeleri temizle"""
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Stop words (azaltıldı)
        stop_words = {'bir', 've', 'mi', 'mı', 'mu', 'mü', 'the', 'a', 'is'}
        
        cleaned = [w for w in words if len(w) > 2 and w not in stop_words]
        return cleaned
    
    def _check_turkish_quality(self, output: str, query: str) -> float:
        """
        Türkçe kalite skoru (DAHA ESNEK)
        """
        query_has_turkish = self._has_turkish_chars(query)
        output_has_turkish = self._has_turkish_chars(output)
        
        if query_has_turkish:
            if output_has_turkish:
                return 1.0
            else:
                # İngilizce teknik terimler tamamen kabul edilir
                return 0.8  # 0.7'den 0.8'e artırıldı
        else:
            return 0.9  # 0.8'den 0.9'a artırıldı
    
    def _has_turkish_chars(self, text: str) -> bool:
        """Türkçe karakter var mı?"""
        turkish_chars = 'çğıöşüÇĞİÖŞÜ'
        return any(c in text for c in turkish_chars)
    
    def _has_sentence_structure(self, text: str) -> bool:
        """Cümle yapısı var mı?"""
        return any(p in text for p in '.!?:')  # ':' eklendi
    
    def _has_meta_tags(self, text: str) -> bool:
        """Meta tag var mı?"""
        meta_patterns = [
            r'\[USER\]', r'\[ASSISTANT\]', r'\[INST\]', r'\[/INST\]',
            r'<\|im_start\|>', r'<\|im_end\|>',
            r'<\|system\|>', r'<\|user\|>', r'<\|assistant\|>',
        ]
        
        for pattern in meta_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _has_repetition(self, text: str) -> bool:
        """Tekrar var mı? (Daha esnek)"""
        sentences = re.split(r'[.!?]\s+', text)
        
        if len(sentences) < 3:  # 2'den 3'e artırıldı
            return False
        
        seen = set()
        for sent in sentences:
            sent_clean = sent.strip().lower()
            
            # Çok kısa cümleler kontrole dahil edilmez
            if len(sent_clean) < 15:  # 10'dan 15'e artırıldı
                continue
            
            if sent_clean in seen:
                return True
            seen.add(sent_clean)
        
        return False


# Global instance
_quality_validator = QualityValidator()


def validate_quality(output: str, user_query: str) -> Tuple[bool, float]:
    """Utility function"""
    return _quality_validator.validate(output, user_query)