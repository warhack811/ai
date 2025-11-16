"""
services/personality_enforcer.py
---------------------------------
PERSONALITY ENFORCER - Model çıktısına personality zorla uygula
Friend mode → emoji ekle, samimi dil
Creative mode → emoji ve yaratıcılık ekle
"""

import re
import random
import logging
from typing import Tuple

from schemas.common import ChatMode, EmotionLabel

logger = logging.getLogger(__name__)


# ============================================
# EMOJİ KÜTÜPHANESİ
# ============================================

EMOJIS = {
    'friendly': ['😊', '👍', '💫', '✨', '🙂', '😄'],
    'creative': ['🎨', '✨', '💡', '🎭', '🌟', '🎉', '💫', '🚀'],
    'supportive': ['💪', '👏', '🤝', '❤️', '🌟'],
    'excited': ['🎉', '🚀', '⭐', '💥', '🔥'],
    'thinking': ['🤔', '💭', '🧠', '📚'],
    'code': ['💻', '⚙️', '🔧', '📝'],
}


def add_emojis_to_text(text: str, mode: ChatMode, count: int = 2) -> str:
    """
    Metne emoji ekle
    
    Args:
        text: Orijinal metin
        mode: Chat modu
        count: Eklenecek emoji sayısı
        
    Returns:
        Emoji eklenmiş metin
    """
    
    if not text or len(text.strip()) == 0:
        return text
    
    # Zaten emoji varsa ekleme
    if any(emoji in text for emoji_list in EMOJIS.values() for emoji in emoji_list):
        return text
    
    # Mode'a göre emoji seç
    if mode == ChatMode.FRIEND:
        emoji_pool = EMOJIS['friendly']
    elif mode == ChatMode.CREATIVE:
        emoji_pool = EMOJIS['creative']
    else:
        return text  # Başka modlarda emoji ekleme
    
    # Random emoji seç
    selected_emojis = random.sample(emoji_pool, min(count, len(emoji_pool)))
    
    # Metni cümlelere ayır
    sentences = re.split(r'([.!?]+)', text)
    
    if len(sentences) < 2:
        # Tek cümle - sonuna ekle
        return f"{text} {selected_emojis[0]}"
    
    # İlk cümlenin sonuna bir emoji
    result = sentences[0] + (sentences[1] if len(sentences) > 1 else '')
    result += f" {selected_emojis[0]}"
    
    # Geri kalanı ekle
    for i in range(2, len(sentences)):
        result += sentences[i]
    
    # Son cümleye de emoji (eğer yeterince uzunsa)
    if len(sentences) > 4 and len(selected_emojis) > 1:
        result += f" {selected_emojis[1]}"
    
    return result


# ============================================
# DİL ÜSLÜBÜNü DEĞİŞTİR
# ============================================

def make_friendly(text: str) -> str:
    """
    Metni samimi hale getir (size → sana)
    """
    
    if not text:
        return text
    
    # "Size" → "Sana" dönüşümleri
    replacements = [
        (r'\bsize\b', 'sana'),
        (r'\bSize\b', 'Sana'),
        (r'\bSİZE\b', 'SANA'),
        (r'\bsizin\b', 'senin'),
        (r'\bSizin\b', 'Senin'),
        (r'\bsizi\b', 'seni'),
        (r'\bSizi\b', 'Seni'),
        (r'\bsizden\b', 'senden'),
        (r'\bSizden\b', 'Senden'),
        (r'\bsizinle\b', 'seninle'),
        (r'\bSizinle\b', 'Seninle'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text


def make_casual(text: str) -> str:
    """
    Metni daha rahat/günlük hale getir
    """
    
    if not text:
        return text
    
    # Resmi → Günlük dönüşümler
    replacements = [
        ('memnuniyetle', 'memnuniyetle'),  # Değişmesin
        ('elbette', 'tabii'),
        ('kesinlikle', 'kesinlikle'),  # Değişmesin
        ('yardımcı olabilirim', 'yardım edebilirim'),
        ('size yardımcı olmak', 'sana yardım etmek'),
    ]
    
    for old, new in replacements:
        text = text.replace(old, new)
    
    return text


# ============================================
# ANA ENFORCER FONKSİYONU
# ============================================

def enforce_personality(
    text: str,
    mode: ChatMode,
    emotion: EmotionLabel = None
) -> Tuple[str, bool]:
    """
    Model çıktısına personality zorla uygula
    
    Args:
        text: Model'den gelen orijinal cevap
        mode: Chat modu
        emotion: Kullanıcı duygusu (opsiyonel)
        
    Returns:
        (modified_text, was_modified)
    """
    
    if not text or len(text.strip()) < 5:
        return text, False
    
    original = text
    modified = False
    
    # 1. FRIEND MODE
    if mode == ChatMode.FRIEND:
        # Samimi dil yap
        new_text = make_friendly(text)
        if new_text != text:
            text = new_text
            modified = True
            logger.info("Applied friendly language (size→sana)")
        
        # Emoji ekle
        new_text = add_emojis_to_text(text, mode, count=2)
        if new_text != text:
            text = new_text
            modified = True
            logger.info("Added friendly emojis")
        
        # Rahat dil
        new_text = make_casual(text)
        if new_text != text:
            text = new_text
            modified = True
    
    # 2. CREATIVE MODE
    elif mode == ChatMode.CREATIVE:
        # Emoji ekle (daha fazla)
        new_text = add_emojis_to_text(text, mode, count=3)
        if new_text != text:
            text = new_text
            modified = True
            logger.info("Added creative emojis")
    
    # 3. CODE MODE
    elif mode == ChatMode.CODE:
        # Kod bloklarını kontrol et
        if '```' not in text and any(word in text.lower() for word in ['fonksiyon', 'kod', 'örnek']):
            # Kod bloğu yoksa uyar
            logger.warning("Code mode but no code block found")
    
    return text, modified


# ============================================
# POST-PROCESSING
# ============================================

def validate_personality_compliance(
    text: str,
    mode: ChatMode
) -> Tuple[bool, str]:
    """
    Cevabın personality kurallarına uygun olup olmadığını kontrol et
    
    Returns:
        (is_compliant, issue_description)
    """
    
    issues = []
    
    # Friend mode kontrolü
    if mode == ChatMode.FRIEND:
        # "Size" varsa hata
        if re.search(r'\bsize\b|\bsizin\b|\bsizi\b', text, re.IGNORECASE):
            issues.append("Friend mode'da 'size/sizin' kullanılmamalı (sana/senin olmalı)")
        
        # Emoji var mı?
        has_emoji = any(char in text for emoji_list in EMOJIS.values() for char in emoji_list)
        if not has_emoji:
            issues.append("Friend mode'da emoji olmalı")
    
    # Creative mode kontrolü
    elif mode == ChatMode.CREATIVE:
        # Emoji var mı?
        has_emoji = any(char in text for char in EMOJIS['creative'])
        if not has_emoji:
            issues.append("Creative mode'da yaratıcı emoji olmalı")
    
    # Sorunlar varsa
    if issues:
        return False, '; '.join(issues)
    
    return True, "OK"


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    # Test 1: Friend mode
    text1 = "Size Python öğrenmek için bazı kaynaklar önerebilirim."
    result1, modified1 = enforce_personality(text1, ChatMode.FRIEND)
    print(f"Test 1 (Friend):")
    print(f"  Before: {text1}")
    print(f"  After:  {result1}")
    print(f"  Modified: {modified1}")
    print()
    
    # Test 2: Creative mode
    text2 = "Python harika bir programlama dilidir."
    result2, modified2 = enforce_personality(text2, ChatMode.CREATIVE)
    print(f"Test 2 (Creative):")
    print(f"  Before: {text2}")
    print(f"  After:  {result2}")
    print(f"  Modified: {modified2}")
    print()
    
    # Test 3: Validation
    compliant, issue = validate_personality_compliance(result1, ChatMode.FRIEND)
    print(f"Test 3 (Validation):")
    print(f"  Compliant: {compliant}")
    print(f"  Issue: {issue}")