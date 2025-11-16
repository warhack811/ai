"""
backend/services/turkish_language_processor.py
===============================================
PROFESYONEL TÜRKÇE İŞLEME MOTORU

Görev:
- Model çıktılarını Türkçe kurallarına göre düzelt
- Kullanıcı girdilerini normalize et
- Kalite kontrolü yap

Özellikler:
✅ Türkçe karakter düzeltmeleri
✅ Dilbilgisi kontrolleri (temel)
✅ Yaygın yazım hatalarını düzelt
✅ "AI/Robot" ifadelerini Türkçeleştir
✅ Cümle yapısını düzelt
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TurkishQualityScore:
    """Türkçe kalite skoru"""
    overall: float  # 0-1 arası genel skor
    grammar: float  # Dilbilgisi skoru
    naturalness: float  # Doğallık skoru
    vocabulary: float  # Kelime seçimi skoru
    issues: List[str]  # Tespit edilen sorunlar


class TurkishLanguageProcessor:
    """
    Profesyonel Türkçe işleme motoru
    """
    
    def __init__(self):
        # Türkçe karakter mapping
        self.char_fixes = {
            'ı': 'ı', 'İ': 'İ', 'ş': 'ş', 'Ş': 'Ş',
            'ğ': 'ğ', 'Ğ': 'Ğ', 'ü': 'ü', 'Ü': 'Ü',
            'ö': 'ö', 'Ö': 'Ö', 'ç': 'ç', 'Ç': 'Ç',
        }
        
        # Yaygın yazım hataları
        self.typo_map = {
            'nasilsin': 'nasılsın',
            'naslsn': 'nasılsın',
            'naber': 'ne haber',
            'mrb': 'merhaba',
            'slm': 'selam',
            'tşk': 'teşekkür',
            'sagol': 'sağol',
            'tesekkur': 'teşekkür',
            'lutfen': 'lütfen',
        }
        
        # Robot/AI ifadeleri -> Türkçe
        self.ai_phrases = {
            r'\bben bir yapay zeka olarak\b': '',
            r'\bben bir ai olarak\b': '',
            r'\bben bir asistan olarak\b': '',
            r'\bsize nasıl yardımcı olabilirim\??\b': '',
            r'\büzgünüm ama ben bir\b': 'üzgünüm,',
            r'\bai\b': 'yapay zeka',
            r'\bartificial intelligence\b': 'yapay zeka',
            r'\bmachine learning\b': 'makine öğrenmesi',
            r'\bcomputer\b': 'bilgisayar',
            r'\bsoftware\b': 'yazılım',
            r'\bhardware\b': 'donanım',
        }
        
        # Gereksiz tekrar cümleler
        self.filler_phrases = [
            'tabii ki', 'elbette', 'kesinlikle',
            'memnuniyetle', 'size yardımcı olmak isterim',
        ]
    
    def normalize_user_input(self, text: str) -> str:
        """
        Kullanıcı girdisini normalize et
        
        Args:
            text: Ham kullanıcı metni
            
        Returns:
            Normalize edilmiş metin
        """
        if not text or not text.strip():
            return text
        
        normalized = text
        
        # 1. Türkçe karakter düzeltmeleri
        normalized = self._fix_turkish_encoding(normalized)
        
        # 2. Yazım hatalarını düzelt (hafif)
        normalized = self._fix_common_typos(normalized)
        
        # 3. Gereksiz boşlukları temizle
        normalized = self._clean_whitespace(normalized)
        
        # 4. Küçük/büyük harf normalize
        # (Çok agresif yapma, kullanıcı vurgu için büyük harf kullanıyor olabilir)
        
        return normalized.strip()
    
    def enhance_model_output(self, text: str, aggressive: bool = False) -> str:
        """
        Model çıktısını Türkçe kurallarına göre iyileştir
        
        Args:
            text: Model'den gelen ham çıktı
            aggressive: Agresif düzeltme mi? (daha fazla değişiklik)
            
        Returns:
            İyileştirilmiş metin
        """
        if not text or not text.strip():
            return text
        
        enhanced = text
        
        # 1. Türkçe karakter düzeltmeleri
        enhanced = self._fix_turkish_encoding(enhanced)
        
        # 2. AI/Robot ifadelerini temizle
        enhanced = self._remove_ai_phrases(enhanced)
        
        # 3. Gereksiz dolgu cümlelerini kaldır
        enhanced = self._remove_filler_phrases(enhanced)
        
        # 4. Noktalama düzeltmeleri
        enhanced = self._fix_punctuation(enhanced)
        
        # 5. Cümle başlarını büyük harfe çevir
        enhanced = self._capitalize_sentences(enhanced)
        
        # 6. Gereksiz boşlukları temizle
        enhanced = self._clean_whitespace(enhanced)
        
        if aggressive:
            # 7. İngilizce kelimeleri Türkçeleştir
            enhanced = self._turkify_english_words(enhanced)
            
            # 8. Temel dilbilgisi kontrolü
            enhanced = self._basic_grammar_check(enhanced)
        
        return enhanced.strip()
    
    def calculate_turkish_quality(self, text: str) -> TurkishQualityScore:
        """
        Metnin Türkçe kalitesini ölç
        
        Returns:
            TurkishQualityScore object
        """
        issues = []
        
        # 1. Türkçe karakter oranı
        turkish_char_score = self._score_turkish_chars(text)
        if turkish_char_score < 0.3:
            issues.append("Çok az Türkçe karakter (İngilizce olabilir)")
        
        # 2. Cümle yapısı
        grammar_score = self._score_grammar(text)
        if grammar_score < 0.5:
            issues.append("Cümle yapısı zayıf")
        
        # 3. Doğallık (robot ifadeleri var mı?)
        naturalness_score = self._score_naturalness(text)
        if naturalness_score < 0.6:
            issues.append("Robot gibi ifadeler var")
        
        # 4. Kelime seçimi (alakasız/garip kelimeler)
        vocab_score = self._score_vocabulary(text)
        if vocab_score < 0.5:
            issues.append("Garip kelime seçimleri")
        
        # Genel skor (ağırlıklı ortalama)
        overall = (
            grammar_score * 0.3 +
            naturalness_score * 0.3 +
            vocab_score * 0.2 +
            turkish_char_score * 0.2
        )
        
        return TurkishQualityScore(
            overall=overall,
            grammar=grammar_score,
            naturalness=naturalness_score,
            vocabulary=vocab_score,
            issues=issues
        )
    
    # ========================================
    # PRIVATE HELPER METHODS
    # ========================================
    
    def _fix_turkish_encoding(self, text: str) -> str:
        """Türkçe karakter encoding sorunlarını düzelt"""
        # Yaygın encoding hataları
        replacements = {
            'Ä±': 'ı', 'Ä°': 'İ',
            'Å\x9f': 'ş', 'Åž': 'Ş',
            'ÄŸ': 'ğ', 'Äž': 'Ğ',
            'Ã¼': 'ü', 'Ãœ': 'Ü',
            'Ã¶': 'ö', 'Ã–': 'Ö',
            'Ã§': 'ç', 'Ã‡': 'Ç',
        }
        
        fixed = text
        for wrong, correct in replacements.items():
            fixed = fixed.replace(wrong, correct)
        
        return fixed
    
    def _fix_common_typos(self, text: str) -> str:
        """Yaygın yazım hatalarını düzelt"""
        fixed = text
        
        # Kelime bazlı düzeltmeler (whole word)
        for typo, correct in self.typo_map.items():
            # Sadece tam kelime eşleşmelerini değiştir
            pattern = r'\b' + re.escape(typo) + r'\b'
            fixed = re.sub(pattern, correct, fixed, flags=re.IGNORECASE)
        
        return fixed
    
    def _remove_ai_phrases(self, text: str) -> str:
        """Robot/AI ifadelerini temizle"""
        cleaned = text
        
        for pattern, replacement in self.ai_phrases.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Fazla boşlukları temizle
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        
        return cleaned
    
    def _remove_filler_phrases(self, text: str) -> str:
        """Gereksiz dolgu cümlelerini kaldır"""
        # Cümle başındaki gereksiz ifadeler
        start_patterns = [
            r'^(tabii ki|elbette|kesinlikle|memnuniyetle)[,\s]+',
        ]
        
        cleaned = text
        for pattern in start_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _fix_punctuation(self, text: str) -> str:
        """Noktalama işaretlerini düzelt"""
        fixed = text
        
        # Nokta/virgül/soru işareti öncesi boşluk kaldır
        fixed = re.sub(r'\s+([.,!?;:])', r'\1', fixed)
        
        # Noktalama sonrası boşluk ekle (yoksa)
        fixed = re.sub(r'([.,!?;:])([A-ZÇĞİÖŞÜa-zçğıöşü])', r'\1 \2', fixed)
        
        # Çift noktalama temizle
        fixed = re.sub(r'\.{2,}', '.', fixed)
        fixed = re.sub(r'\!{2,}', '!', fixed)
        
        return fixed
    
    def _capitalize_sentences(self, text: str) -> str:
        """Cümle başlarını büyük harfe çevir"""
        # Basit implementasyon
        sentences = re.split(r'([.!?]\s+)', text)
        
        capitalized = []
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part:  # Cümle kısmı
                # İlk harfi büyük yap
                part = part[0].upper() + part[1:] if len(part) > 0 else part
            capitalized.append(part)
        
        return ''.join(capitalized)
    
    def _clean_whitespace(self, text: str) -> str:
        """Gereksiz boşlukları temizle"""
        # Çoklu boşlukları tek boşluğa çevir
        cleaned = re.sub(r' {2,}', ' ', text)
        
        # Çoklu satır sonlarını düzelt
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Satır başı/sonu boşluklarını temizle
        lines = [line.strip() for line in cleaned.split('\n')]
        cleaned = '\n'.join(lines)
        
        return cleaned
    
    def _turkify_english_words(self, text: str) -> str:
        """Yaygın İngilizce kelimeleri Türkçeleştir"""
        # Sadece çok yaygın olanlar (agresif değil)
        common_translations = {
            'computer': 'bilgisayar',
            'software': 'yazılım',
            'internet': 'internet',  # Aynı kalabilir
            'email': 'e-posta',
            'website': 'web sitesi',
        }
        
        turkified = text
        for eng, tr in common_translations.items():
            pattern = r'\b' + re.escape(eng) + r'\b'
            turkified = re.sub(pattern, tr, turkified, flags=re.IGNORECASE)
        
        return turkified
    
    def _basic_grammar_check(self, text: str) -> str:
        """Temel dilbilgisi kontrolü"""
        # Çok basit kurallar (derin analiz değil)
        
        fixed = text
        
        # "bir bir" tekrarı
        fixed = re.sub(r'\bbir\s+bir\b', 'bir', fixed, flags=re.IGNORECASE)
        
        # "ve ve" tekrarı
        fixed = re.sub(r'\bve\s+ve\b', 've', fixed, flags=re.IGNORECASE)
        
        return fixed
    
    def _score_turkish_chars(self, text: str) -> float:
        """Türkçe karakter oranı (0-1)"""
        if not text:
            return 0.0
        
        turkish_chars = 'çğıöşüÇĞİÖŞÜ'
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return 0.5  # Sayı/sembol ağırlıklı
        
        turkish_count = sum(1 for c in text if c in turkish_chars)
        
        # En az 1 Türkçe karakter varsa minimum 0.5
        if turkish_count > 0:
            return min(1.0, 0.5 + (turkish_count / total_alpha))
        
        # Hiç Türkçe karakter yoksa (İngilizce olabilir)
        return 0.3
    
    def _score_grammar(self, text: str) -> float:
        """Cümle yapısı skoru (0-1)"""
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        
        # Noktalama var mı?
        if any(p in text for p in '.!?'):
            score += 0.2
        
        # Cümle çok uzun değil mi? (200 kelimeden az)
        word_count = len(text.split())
        if word_count < 200:
            score += 0.15
        
        # Tekrarlayan kelimeler var mı?
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        if unique_ratio > 0.6:
            score += 0.15
        
        return min(1.0, score)
    
    def _score_naturalness(self, text: str) -> float:
        """Doğallık skoru (robot ifadeleri var mı?)"""
        text_lower = text.lower()
        
        # Robot ifadelerini kontrol et
        robot_phrases = [
            'ben bir yapay zeka',
            'ben bir ai',
            'ben bir asistan',
            'size nasıl yardımcı',
            'memnuniyetle yardımcı',
        ]
        
        penalty = 0
        for phrase in robot_phrases:
            if phrase in text_lower:
                penalty += 0.2
        
        score = max(0.0, 1.0 - penalty)
        return score
    
    def _score_vocabulary(self, text: str) -> float:
        """Kelime seçimi skoru (alakasız kelimeler var mı?)"""
        text_lower = text.lower()
        
        # Alakasız/garip kelime kombinasyonları (örneklerden)
        weird_phrases = [
            'karnivora dizi',
            'channel dairecisi',
            'ulaşım sen bana',
            'pis kokulu dedin',
        ]
        
        penalty = 0
        for phrase in weird_phrases:
            if phrase in text_lower:
                penalty += 0.3
        
        score = max(0.0, 1.0 - penalty)
        return score


# ========================================
# GLOBAL INSTANCE
# ========================================

_turkish_processor = TurkishLanguageProcessor()


def normalize_user_input(text: str) -> str:
    """Utility: Kullanıcı girdisini normalize et"""
    return _turkish_processor.normalize_user_input(text)


def enhance_model_output(text: str, aggressive: bool = False) -> str:
    """Utility: Model çıktısını iyileştir"""
    return _turkish_processor.enhance_model_output(text, aggressive)


def calculate_turkish_quality(text: str) -> TurkishQualityScore:
    """Utility: Türkçe kalite skoru"""
    return _turkish_processor.calculate_turkish_quality(text)