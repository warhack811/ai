"""
services/output_cleaner.py
--------------------------
Model output'unu temizler ve düzeltir
"""

import re
from typing import Optional

class OutputCleaner:
    """
    Multi-stage output cleaning pipeline
    """
    
    def clean(self, raw_output: str, model_key: str) -> str:
        """
        Ana cleaning fonksiyonu
        """
        if not raw_output:
            return ""
        
        text = raw_output
        
        # Stage 1: Meta tag'leri kaldır
        text = self._remove_meta_tags(text)
        
        # Stage 2: Tekrarlanan cümleleri kaldır
        text = self._fix_repetition(text)
        
        # Stage 3: Yarım cümleleri düzelt
        text = self._trim_incomplete(text)
        
        # Stage 4: Fazla boşlukları temizle
        text = self._clean_whitespace(text)
        
        # Stage 5: Code block formatting (varsa)
        text = self._fix_code_blocks(text)
        
        return text.strip()
    
    def _remove_meta_tags(self, text: str) -> str:
        """
        Model'in eklediği meta tag'leri kaldır
        """
        patterns = [
            r'\[/?(?:USER|ASSISTANT|INST|SYSTEM|user|assistant)\]',
            r'<\|im_start\|>.*?<\|im_end\|>',
            r'<\|(?:system|user|assistant|end)\|>',
            r'###\s*(?:User|Assistant|System):?\s*',
            r'\[INST\]|\[/INST\]',
            r'<s>|</s>',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_repetition(self, text: str) -> str:
        """
        Tekrarlanan cümleleri kaldır
        """
        # Basit cümle tokenization (Türkçe için)
        sentences = re.split(r'[.!?]\s+', text)
        
        unique_sentences = []
        seen = set()
        
        for sent in sentences:
            sent_clean = sent.strip().lower()
            
            # Aynı cümle 2+ kez geçiyorsa sadece 1 kez ekle
            if sent_clean and sent_clean not in seen:
                unique_sentences.append(sent.strip())
                seen.add(sent_clean)
        
        return '. '.join(unique_sentences) + ('.' if unique_sentences else '')
    
    def _trim_incomplete(self, text: str) -> str:
        """
        Yarım kalmış son cümleyi kaldır
        """
        # Son cümle noktalama ile bitmiyor mu kontrol et
        if not text:
            return text
        
        last_char = text[-1]
        
        # Noktalama ile bitiyorsa sorun yok
        if last_char in '.!?':
            return text
        
        # Son noktalamaya kadar kes
        last_punctuation_pos = max(
            text.rfind('.'),
            text.rfind('!'),
            text.rfind('?')
        )
        
        if last_punctuation_pos > len(text) * 0.5:  # En az %50'si kalsın
            return text[:last_punctuation_pos + 1]
        
        # Çok kısa kalmışsa olduğu gibi dön
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """
        Fazla boşlukları temizle
        """
        # Çoklu satır sonlarını düzelt
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Çoklu boşlukları düzelt
        text = re.sub(r' {2,}', ' ', text)
        
        # Satır başı/sonu boşluklarını temizle
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def _fix_code_blocks(self, text: str) -> str:
        """
        Code block'ları düzelt
        """
        # Eğer ``` varsa ama kapatılmamışsa kapat
        code_block_count = text.count('```')
        
        if code_block_count % 2 != 0:
            # Tek sayıda ``` var, son satıra ``` ekle
            text = text + '\n```'
        
        return text


# Global instance
_output_cleaner = OutputCleaner()

def clean_output(raw_output: str, model_key: str) -> str:
    """Utility function"""
    return _output_cleaner.clean(raw_output, model_key)