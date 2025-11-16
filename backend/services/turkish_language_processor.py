"""
services/turkish_language_processor.py
---------------------------------------
PROFESSIONAL VERSION - %100 Test Pass İçin
Yazım hatası düzeltme, normalizasyon ve kalite kontrolü
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


# ============================================
# YAZIM HATASI DÜZELTİCİ
# ============================================

TURKISH_CHAR_MAP = {
    # Türkçe → Türkçe (normalizasyon)
    'ı': 'ı', 'i': 'i', 'İ': 'İ', 'I': 'I',
    'ş': 'ş', 'Ş': 'Ş', 'ğ': 'ğ', 'Ğ': 'Ğ',
    'ü': 'ü', 'Ü': 'Ü', 'ö': 'ö', 'Ö': 'Ö',
    'ç': 'ç', 'Ç': 'Ç',
}

# Sık yapılan yazım hataları
COMMON_TYPOS = {
    # Türkçe karakter hataları
    'dongu': 'döngü',
    'donguler': 'döngüler',
    'degisken': 'değişken',
    'degiskenler': 'değişkenler',
    'fonksiyon': 'fonksiyon',  # Zaten doğru
    'sinif': 'sınıf',
    'siniflar': 'sınıflar',
    'ozellik': 'özellik',
    'ozellikler': 'özellikler',
    'kullanim': 'kullanım',
    'cozum': 'çözüm',
    'aciklama': 'açıklama',
    'ornek': 'örnek',
    'ornekler': 'örnekler',
    'ucretsiz': 'ücretsiz',
    'uyelik': 'üyelik',
    'gorsel': 'görsel',
    'gorunum': 'görünüm',
    'islem': 'işlem',
    'islemler': 'işlemler',
    'duzenleme': 'düzenleme',
    'guncelleme': 'güncelleme',
    'silme': 'silme',  # Zaten doğru
    'ekleme': 'ekleme',  # Zaten doğru
    
    # Kod terimleri
    'pythonda': 'python\'da',
    'pythonun': 'python\'un',
    'pythonla': 'python ile',
    'javascriptte': 'javascript\'te',
    'javascriptin': 'javascript\'in',
    
    # Sık hatalar
    'nasil': 'nasıl',
    'nedir': 'nedir',  # Zaten doğru
    'nedemek': 'ne demek',
    'neden': 'neden',  # Zaten doğru
    'nicin': 'niçin',
    'aciklarmisin': 'açıklar mısın',
    'anlat': 'anlat',  # Zaten doğru
    'yapilir': 'yapılır',
    'olusturulur': 'oluşturulur',
    'kullanilir': 'kullanılır',
    'yazilir': 'yazılır',
    'okunur': 'okunur',
    'silinir': 'silinir',
}

# Kelime düzeltmeleri (daha kapsamlı)
WORD_CORRECTIONS = {
    'bi': 'bir',
    'bişey': 'bir şey',
    'bisey': 'bir şey',
    'nolur': 'ne olur',
    'naber': 'ne haber',
    'napıyorsun': 'ne yapıyorsun',
    'napıyosun': 'ne yapıyorsun',
    'anlamadım': 'anlamadım',  # Zaten doğru
    'öğren': 'öğren',  # Zaten doğru
}


def normalize_user_input(text: str) -> str:
    """
    Kullanıcı girdisini normalleştir ve yazım hatalarını düzelt
    
    Args:
        text: Ham kullanıcı mesajı
        
    Returns:
        Düzeltilmiş ve normalleştirilmiş metin
    """
    if not text or len(text.strip()) == 0:
        return text
    
    original = text
    
    # 1. Baş/son boşlukları temizle
    text = text.strip()
    
    # 2. Çoklu boşlukları tek boşluğa indir
    text = re.sub(r'\s+', ' ', text)
    
    # 3. Sık yazım hatalarını düzelt (kelime bazında)
    words = text.split()
    corrected_words = []
    
    for word in words:
        # Küçük harfe çevir kontrol için
        word_lower = word.lower()
        
        # Noktalama işaretlerini ayır
        punctuation = ''
        if word_lower and word_lower[-1] in '.,!?;:':
            punctuation = word_lower[-1]
            word_lower = word_lower[:-1]
        
        # Sık hatalara bak
        if word_lower in COMMON_TYPOS:
            corrected = COMMON_TYPOS[word_lower]
            # Orijinal büyük harfse, düzeltmeyi de büyük yap
            if word[0].isupper() and len(corrected) > 0:
                corrected = corrected[0].upper() + corrected[1:]
            corrected_words.append(corrected + punctuation)
        elif word_lower in WORD_CORRECTIONS:
            corrected_words.append(WORD_CORRECTIONS[word_lower] + punctuation)
        else:
            corrected_words.append(word)
    
    text = ' '.join(corrected_words)
    
    # 4. Özel düzeltmeler (regex-based)
    # "pythonda" → "python'da"
    text = re.sub(r'\b(python|javascript|java)da\b', r"\1'da", text, flags=re.IGNORECASE)
    text = re.sub(r'\b(python|javascript|java)un\b', r"\1'un", text, flags=re.IGNORECASE)
    text = re.sub(r'\b(python|javascript|java)la\b', r"\1 ile", text, flags=re.IGNORECASE)
    
    # 5. Soru işareti yoksa ve soru kelimesi varsa ekle
    question_words = ['nasıl', 'nedir', 'ne', 'neden', 'niçin', 'kim', 'ne zaman', 'nerede']
    has_question_word = any(word in text.lower() for word in question_words)
    if has_question_word and not text.endswith('?'):
        text += '?'
    
    # Log düzeltmeler
    if original != text:
        logger.info(f"Text normalized: '{original[:50]}...' → '{text[:50]}...'")
    
    return text


def enhance_model_output(text: str, aggressive: bool = False) -> str:
    """
    Model çıktısını iyileştir
    
    Args:
        text: Model'den gelen ham cevap
        aggressive: Agresif temizlik (fazla değişiklik)
        
    Returns:
        İyileştirilmiş cevap
    """
    if not text:
        return text
    
    original = text
    
    # 1. Başındaki/sonundaki gereksiz boşlukları temizle
    text = text.strip()
    
    # 2. AI klişelerini temizle
    ai_phrases = [
        r'^Tabii ki!?\s*',
        r'^Elbette!?\s*',
        r'^Memnuniyetle!?\s*',
        r'^İşte cevabınız:?\s*',
        r'^Size yardımcı olabilirim\.?\s*',
        r'^Ben bir yapay zeka.*?\.\s*',
        r'^AI asistanı olarak.*?\.\s*',
    ]
    
    for pattern in ai_phrases:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # 3. Meta tagları temizle
    text = re.sub(r'\[USER\]|\[ASSISTANT\]|\[INST\]|\[/INST\]|<think>|</think>', '', text)
    
    # 4. Çoklu satır sonlarını normalize et
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 5. Başındaki gereksiz kelimeler
    if aggressive:
        # "İşte açıklamam:", "Şöyle:" gibi gereksiz başlangıçlar
        text = re.sub(r'^(İşte|Şöyle|Peki|Tamam|Öncelikle)[:\s]*', '', text, flags=re.IGNORECASE)
    
    # 6. Final cleanup
    text = text.strip()
    
    # Log
    if original != text:
        logger.debug(f"Output enhanced: {len(original)} → {len(text)} chars")
    
    return text


# ============================================
# KALİTE SKORU
# ============================================

class QualityScore:
    """Türkçe kalite skoru"""
    def __init__(self, overall: float, issues: list):
        self.overall = overall
        self.issues = issues


def calculate_turkish_quality(text: str) -> QualityScore:
    """
    Türkçe kalite skorunu hesapla
    
    Returns:
        QualityScore (0.0-1.0)
    """
    if not text or len(text.strip()) < 10:
        return QualityScore(0.0, ["Çok kısa cevap"])
    
    score = 1.0
    issues = []
    
    # 1. Türkçe karakter kontrolü
    has_turkish = any(char in text for char in ['ı', 'İ', 'ş', 'Ş', 'ğ', 'Ğ', 'ü', 'Ü', 'ö', 'Ö', 'ç', 'Ç'])
    
    # 2. AI klişeleri
    ai_cliches = [
        'ben bir yapay zeka',
        'ai asistanı olarak',
        'dil modeli olarak',
        'size nasıl yardımcı olabilirim',
        'benim için mümkün değil',
        'üzgünüm ama ben',
    ]
    
    for cliche in ai_cliches:
        if cliche in text.lower():
            score -= 0.3
            issues.append(f"AI klişesi: '{cliche}'")
            break
    
    # 3. Meta tag kontrolü
    if any(tag in text for tag in ['[USER]', '[ASSISTANT]', '[INST]', '<think>']):
        score -= 0.4
        issues.append("Meta tag bulundu")
    
    # 4. Uzunluk kontrolü
    if len(text) < 20:
        score -= 0.2
        issues.append("Çok kısa")
    
    # 5. Doğallık kontrolü (çok tekrarlı kelimeler)
    words = text.lower().split()
    if len(words) > 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            score -= 0.15
            issues.append("Çok tekrarlı")
    
    # Final score
    score = max(0.0, min(1.0, score))
    
    return QualityScore(score, issues)


# ============================================
# HELPER FUNCTIONS
# ============================================

def is_turkish_text(text: str) -> bool:
    """Metin Türkçe mi kontrol et"""
    if not text:
        return False
    
    turkish_chars = ['ı', 'İ', 'ş', 'Ş', 'ğ', 'Ğ', 'ü', 'Ü', 'ö', 'Ö', 'ç', 'Ç']
    return any(char in text for char in turkish_chars)


def clean_code_blocks(text: str) -> str:
    """Kod bloklarını temizle ve düzelt"""
    # Kod bloklarını bul ve düzelt
    # ```python yerine ``` python varsa düzelt
    text = re.sub(r'```\s+python', '```python', text)
    text = re.sub(r'```\s+javascript', '```javascript', text)
    
    return text


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    # Test 1: Yazım hatası düzeltme
    test1 = "Pythonda dongu nasil yazilir"
    result1 = normalize_user_input(test1)
    print(f"Test 1: '{test1}' → '{result1}'")
    
    # Test 2: Model output temizleme
    test2 = "Tabii ki! İşte cevabınız: Python bir programlama dilidir."
    result2 = enhance_model_output(test2, aggressive=True)
    print(f"Test 2: '{test2}' → '{result2}'")
    
    # Test 3: Kalite skoru
    test3 = "Python, yüksek seviyeli bir programlama dilidir."
    quality = calculate_turkish_quality(test3)
    print(f"Test 3: Quality={quality.overall}, Issues={quality.issues}")