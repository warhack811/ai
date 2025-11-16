"""
backend/services/personality_engine.py
=======================================
KİŞİLİK MOTORU - Model Bağımsız Kişilik Yönetimi

Görev:
- Asistanın kişiliğini tanımla
- Her modele aynı kişiliği ver
- Tutarlı ton ve üslup sağla

Özellikler:
✅ Dinamik kişilik profili
✅ Mode'a göre adaptasyon
✅ Emotion'a göre ton ayarlama
✅ Sansür seviyesi kontrolü
"""

from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass

from schemas.common import ChatMode, EmotionLabel, SentimentLabel


class ToneType(str, Enum):
    """Konuşma tonu"""
    PROFESSIONAL = "professional"  # Resmi, profesyonel
    FRIENDLY = "friendly"  # Samimi, arkadaşça
    CASUAL = "casual"  # Günlük, rahat
    EMPATHETIC = "empathetic"  # Empatik, destekleyici
    DIRECT = "direct"  # Direkt, net
    PLAYFUL = "playful"  # Eğlenceli, şakacı


@dataclass
class PersonalityProfile:
    """Kişilik profili"""
    tone: ToneType
    formality: float  # 0.0=çok rahat, 1.0=çok resmi
    verbosity: float  # 0.0=çok kısa, 1.0=çok detaylı
    creativity: float  # 0.0=sade, 1.0=yaratıcı
    directness: float  # 0.0=dolaylı, 1.0=direkt
    empathy: float  # 0.0=tarafsız, 1.0=çok empatik
    humor: float  # 0.0=ciddi, 1.0=eğlenceli


class PersonalityEngine:
    """
    Kişilik yönetim motoru
    """
    
    def __init__(self):
        # Varsayılan kişilik (iş adamı için optimize)
        self.base_profile = PersonalityProfile(
            tone=ToneType.FRIENDLY,
            formality=0.6,  # Profesyonel ama samimi
            verbosity=0.5,  # Dengeli
            creativity=0.7,  # Oldukça yaratıcı
            directness=0.8,  # Direkt ve net
            empathy=0.7,  # Empatik
            humor=0.6,  # Hafif eğlenceli
        )
        
        # Sansür seviyelerine göre ayarlar
        self.censorship_adjustments = {
            0: {"directness": 1.0, "formality": 0.3},  # Tamamen sansürsüz
            1: {"directness": 0.8, "formality": 0.5},  # Dengeli
            2: {"directness": 0.6, "formality": 0.7},  # Güvenli
        }
    
    def get_personality_for_context(
        self,
        mode: ChatMode,
        emotion: Optional[EmotionLabel] = None,
        sentiment: Optional[SentimentLabel] = None,
        safety_level: int = 0,
    ) -> PersonalityProfile:
        """
        Bağlama göre kişilik profili üret
        
        Args:
            mode: Chat modu
            emotion: Kullanıcının duygu durumu
            sentiment: Kullanıcının genel duygusu
            safety_level: Sansür seviyesi (0=yok, 1=orta, 2=yüksek)
            
        Returns:
            Optimize edilmiş PersonalityProfile
        """
        # Base'den başla
        profile = PersonalityProfile(**vars(self.base_profile))
        
        # Mode'a göre ayarla
        profile = self._adjust_for_mode(profile, mode)
        
        # Emotion'a göre ayarla
        if emotion:
            profile = self._adjust_for_emotion(profile, emotion, sentiment)
        
        # Sansür seviyesine göre ayarla
        if safety_level in self.censorship_adjustments:
            adj = self.censorship_adjustments[safety_level]
            for key, value in adj.items():
                setattr(profile, key, value)
        
        return profile
    
    def build_personality_instructions(
        self,
        profile: PersonalityProfile
    ) -> str:
        """
        Kişilik profilinden prompt talimatları üret
        
        Returns:
            Model için kişilik talimatları (string)
        """
        instructions = []
        
        # Temel kimlik
        instructions.append(
            "Sen deneyimli bir Türk danışman ve düşünürsün. "
            "İnsan gibi düşünür ve konuşursun."
        )
        
        # Tone
        tone_descriptions = {
            ToneType.PROFESSIONAL: "Profesyonel ve güvenilir bir üslup kullan.",
            ToneType.FRIENDLY: "Samimi ve arkadaşça konuş, ama profesyonelliğini koru.",
            ToneType.CASUAL: "Rahat ve günlük dil kullan.",
            ToneType.EMPATHETIC: "Empatik ve destekleyici ol.",
            ToneType.DIRECT: "Direkt ve net konuş, dolambacı yapma.",
            ToneType.PLAYFUL: "Eğlenceli ve şakacı bir ton kullan.",
        }
        instructions.append(tone_descriptions.get(profile.tone, ""))
        
        # Formality
        if profile.formality < 0.4:
            instructions.append("Rahat ve günlük Türkçe kullan, fazla resmi olma.")
        elif profile.formality > 0.7:
            instructions.append("Kibar ve resmi bir dil kullan.")
        else:
            instructions.append("Profesyonel ama samimi bir dil kullan.")
        
        # Verbosity (detay seviyesi)
        if profile.verbosity < 0.4:
            instructions.append(
                "Kısa ve öz cevaplar ver. Gereksiz detaya girme. "
                "Her cümle değerli olmalı."
            )
        elif profile.verbosity > 0.7:
            instructions.append(
                "Detaylı ve kapsamlı açıklamalar yap. "
                "Örnekler ver, derinlemesine ele al."
            )
        else:
            instructions.append(
                "Dengeli cevaplar ver. Ne çok kısa ne çok uzun. "
                "Yeterince detay ver ama sıkma."
            )
        
        # Creativity
        if profile.creativity > 0.6:
            instructions.append(
                "Yaratıcı ve ilginç örnekler kullan. "
                "Sıradan olmaktan kaçın, özelleştir."
            )
        
        # Directness
        if profile.directness > 0.7:
            instructions.append(
                "Dolambaçlı konuşma. Direkt cevap ver. "
                "Gereksiz giriş yapma, hemen konuya gir."
            )
        
        # Empathy
        if profile.empathy > 0.6:
            instructions.append(
                "Kullanıcının duygularını anla ve dikkate al. "
                "Destekleyici ve anlayışlı ol."
            )
        
        # Humor
        if profile.humor > 0.6:
            instructions.append(
                "Uygun yerlerde hafif espri yapabilirsin. "
                "Ama çok ileri gitme, profesyonelliğini koru."
            )
        
        # Yasaklar (HER ZAMAN)
        instructions.append(
            "\n❌ ASLA YAPMA:\n"
            "• 'Ben bir yapay zeka olarak...' deme\n"
            "• 'Size nasıl yardımcı olabilirim?' gibi klişeler\n"
            "• Robot gibi soğuk cümleler kurma\n"
            "• Bilmediğin şeyi uydurmaya çalışma\n"
            "• Gereksiz özür dileme ('Üzgünüm ama...')"
        )
        
        # Davranışlar (HER ZAMAN)
        instructions.append(
            "\n✅ MUTLAKA YAP:\n"
            "• İnsan gibi düşün ve akıl yürüt\n"
            "• Bağlamı anla, önceki konuşmaları hatırla\n"
            "• Emin olmadığın konularda 'Bilmiyorum' de\n"
            "• Doğal Türkçe kullan (günlük dil)\n"
            "• Düşünceli ve mantıklı cevaplar ver"
        )
        
        return "\n".join(instructions)
    
    def _adjust_for_mode(
        self,
        profile: PersonalityProfile,
        mode: ChatMode
    ) -> PersonalityProfile:
        """Mode'a göre kişiliği ayarla"""
        
        if mode == ChatMode.CODE:
            # Kod modu: Daha teknik ve direkt
            profile.formality = 0.7
            profile.verbosity = 0.6  # Detaylı açıklama
            profile.directness = 0.9
            profile.creativity = 0.4  # Daha az yaratıcı, daha teknik
        
        elif mode == ChatMode.CREATIVE:
            # Yaratıcı mod: Daha özgür ve eğlenceli
            profile.creativity = 0.9
            profile.humor = 0.8
            profile.formality = 0.3
            profile.verbosity = 0.7
        
        elif mode == ChatMode.FRIEND:
            # Arkadaş modu: Çok samimi
            profile.tone = ToneType.FRIENDLY
            profile.formality = 0.3
            profile.empathy = 0.9
            profile.humor = 0.7
        
        elif mode == ChatMode.RESEARCH:
            # Araştırma modu: Detaylı ve profesyonel
            profile.formality = 0.7
            profile.verbosity = 0.8
            profile.directness = 0.7
        
        elif mode == ChatMode.TURKISH_TEACHER:
            # Türkçe öğretmen: Eğitici ve nazik
            profile.formality = 0.6
            profile.verbosity = 0.7
            profile.empathy = 0.8
            profile.directness = 0.6
        
        return profile
    
    def _adjust_for_emotion(
        self,
        profile: PersonalityProfile,
        emotion: EmotionLabel,
        sentiment: Optional[SentimentLabel]
    ) -> PersonalityProfile:
        """Kullanıcının duygusuna göre ayarla"""
        
        if emotion == EmotionLabel.SAD:
            # Üzgün kullanıcı: Empatik ve destekleyici
            profile.tone = ToneType.EMPATHETIC
            profile.empathy = 0.9
            profile.humor = 0.2  # Şaka yapma
            profile.verbosity = 0.6
        
        elif emotion == EmotionLabel.ANGRY:
            # Sinirli kullanıcı: Sakin ve profesyonel
            profile.tone = ToneType.PROFESSIONAL
            profile.directness = 0.7
            profile.empathy = 0.7
            profile.humor = 0.1  # Hiç şaka yapma
        
        elif emotion == EmotionLabel.ANXIOUS:
            # Kaygılı kullanıcı: Sakinleştirici
            profile.tone = ToneType.EMPATHETIC
            profile.empathy = 0.9
            profile.directness = 0.6
            profile.verbosity = 0.5  # Fazla uzun yazma, kısa ve net
        
        elif emotion == EmotionLabel.HAPPY or emotion == EmotionLabel.EXCITED:
            # Mutlu kullanıcı: Eğlenceli ve enerjik
            profile.tone = ToneType.PLAYFUL
            profile.humor = 0.8
            profile.creativity = 0.8
        
        elif emotion == EmotionLabel.TIRED:
            # Yorgun kullanıcı: Kısa ve öz
            profile.verbosity = 0.3
            profile.directness = 0.8
        
        return profile


# ========================================
# GLOBAL INSTANCE
# ========================================

_personality_engine = PersonalityEngine()


def get_personality(
    mode: ChatMode,
    emotion: Optional[EmotionLabel] = None,
    sentiment: Optional[SentimentLabel] = None,
    safety_level: int = 0,
) -> PersonalityProfile:
    """Utility: Kişilik profili al"""
    return _personality_engine.get_personality_for_context(
        mode, emotion, sentiment, safety_level
    )


def build_personality_prompt(profile: PersonalityProfile) -> str:
    """Utility: Kişilik talimatları üret"""
    return _personality_engine.build_personality_instructions(profile)