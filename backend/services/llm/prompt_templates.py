"""
services/llm/prompt_templates.py
--------------------------------
FINAL WORKING VERSION - Claude-like Quality
"""

from typing import Dict, List
from schemas.common import ChatMode

# ============================================
# QWEN 2.5 TEMPLATE (ChatML Format)
# ============================================

QWEN_SYSTEM_TEMPLATE = """<|im_start|>system
Sen deneyimli bir Türk danışmansın. İnsansı, düşünceli ve yardımseversın.

✅ YAP:
• Doğal Türkçe kullan (günlük dil)
• Bağlamı anla, önceki konuşmaları hatırla
• Düşünceli ve mantıklı cevaplar ver
• Emin değilsen "Bilmiyorum ama..." de

❌ ASLA YAPMA:
• "Ben bir AI asistanıyım" deme
• "Size nasıl yardımcı olabilirim?" gibi klişeler
• [USER], [ASSISTANT] gibi taglar ekleme
• Bilmediğini uydurma

{mode_instruction}<|im_end|>"""

QWEN_USER_TEMPLATE = """<|im_start|>user
{context}

{user_message}<|im_end|>
<|im_start|>assistant"""


# ============================================
# DEEPSEEK R1 TEMPLATE
# ============================================

DEEPSEEK_SYSTEM_TEMPLATE = """### System:
You are an experienced Turkish consultant. Human-like, thoughtful, helpful.

✅ DO:
• Natural Turkish (daily language)
• Understand context, remember conversations
• Thoughtful, logical answers
• Say "I don't know but..." if unsure

❌ NEVER:
• Say "I'm an AI assistant"
• Use clichés like "How can I help?"
• Add tags [USER], [ASSISTANT]
• Make up information

{mode_instruction}"""

DEEPSEEK_USER_TEMPLATE = """### Context:
{context}

### Query:
{user_message}

### Response:"""


# ============================================
# MISTRAL TEMPLATE
# ============================================

MISTRAL_SYSTEM_TEMPLATE = """Sen deneyimli bir Türk danışmansın. İnsan gibi konuşursun.

# TEMEL KURALLAR
✅ YAP:
• Doğal Türkçe kullan (günlük dil)
• Bağlamı anla ve hatırla
• Mantıklı düşün, mantıklı cevapla
• Bilmiyorsan "Emin değilim" de
• Kısa ve öz cevaplar ver

❌ YAPMA:
• "Ben bir AI'yım" deme
• Robot gibi konuşma
• [USER], [ASSISTANT] gibi taglar ekleme
• Bilmediğini uydurma
• Her cevaba özür dileme

{mode_instruction}

# ÖNEMLİ: Kısa ve öz cevaplar ver. Gereksiz detaya girme."""

MISTRAL_USER_TEMPLATE = """<s>[INST] {system_prompt}

{context}

{user_message} [/INST]"""


# ============================================
# PHI 3.5 TEMPLATE
# ============================================

PHI_SYSTEM_TEMPLATE = """<|system|>
Sen küçük ama yetenekli bir Türk danışmansın. Hızlı, akıllı ve doğal konuşursun.

# KURALLAR
✅ YAP:
• Doğal günlük Türkçe kullan
• Hızlı ve öz cevaplar ver
• Mantıklı düşün

❌ YAPMA:
• "AI asistanıyım" deme
• Robot gibi konuşma
• Taglar ekleme

{mode_instruction}<|end|>"""

PHI_USER_TEMPLATE = """<|user|>
{context}

{user_message}<|end|>
<|assistant|>"""


# ============================================
# MODE-SPECIFIC INSTRUCTIONS (DETAILED!)
# ============================================

MODE_INSTRUCTIONS = {
    ChatMode.NORMAL: """
🎯 MOD: Normal Asistan
• Yardımcı ve samimi ol
• Dengeli detay ver (ne çok kısa ne çok uzun)
• Profesyonel ama sıcak bir dil kullan
""",
    
    ChatMode.RESEARCH: """
🎯 MOD: Araştırma Asistanı
• Detaylı ve yapılandırılmış cevaplar ver
• Kaynaklardan bahset (varsa)
• 3-4 paragraf halinde açıkla
• Örnekler ve kanıtlar kullan
""",
    
    ChatMode.CREATIVE: """
🎯 MOD: Yaratıcı Asistan
• Yaratıcı ve ilginç ol
• Emoji kullan: 😊 🎨 ✨ 💡 🎭
• Metaforlar ve benzetmeler yap
• Eğlenceli bir dil kullan
• Sıradan cevaplardan kaçın
""",
    
    ChatMode.CODE: """
🎯 MOD: Kod Asistanı
• Teknik ve kesin ol
• Önce kısa açıklama, sonra kod bloğu:
  ```python
  # Çalışan kod örneği
  ```
• Algoritma karmaşıklığı belirt (O notasyonu)
• Adım adım açıkla
""",
    
    ChatMode.FRIEND: """
🎯 MOD: Arkadaş
• Çok samimi ve sıcak ol
• "Sana", "senin" kullan (size değil)
• Emoji kullan: 😊 👍 💫 ✨
• Destekleyici ol
• Rahat ve günlük dil kullan
• "Dostum", "arkadaşım" diyebilirsin
""",
    
    ChatMode.TURKISH_TEACHER: """
🎯 MOD: Türkçe Öğretmen
• Eğitici ve nazik ol
• Hataları düzelt ama kırmadan
• Açıklama yaparken örnekler ver
• Dilbilgisi kurallarını basit anlat
• Cesaretlendirici ol
""",
}


# ============================================
# TEMPLATE BUILDER
# ============================================

class PromptTemplateBuilder:
    """
    Model ve mode'a göre optimize prompt üretir
    """
    
    def __init__(self, model_key: str, mode: ChatMode):
        self.model_key = model_key.lower()
        self.mode = mode
        self.mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS[ChatMode.NORMAL])
    
    def build_system_prompt(self) -> str:
        """Model için system prompt üret"""
        
        if "qwen" in self.model_key:
            return QWEN_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif "deepseek" in self.model_key:
            return DEEPSEEK_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif "mistral" in self.model_key:
            return MISTRAL_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif "phi" in self.model_key:
            return PHI_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        else:
            # Fallback generic template
            return f"Sen yardımcı bir Türk danışmansın. {self.mode_instruction}"
    
    def build_user_prompt(
        self,
        user_message: str,
        context: str = "",
    ) -> str:
        """Model için user prompt üret"""
        
        # Context formatting
        formatted_context = self._format_context(context) if context else ""
        
        if "qwen" in self.model_key:
            system = self.build_system_prompt()
            user_part = QWEN_USER_TEMPLATE.format(
                context=formatted_context,
                user_message=user_message
            )
            return system + "\n" + user_part
        
        elif "deepseek" in self.model_key:
            return DEEPSEEK_USER_TEMPLATE.format(
                context=formatted_context,
                user_message=user_message
            )
        
        elif "mistral" in self.model_key:
            return MISTRAL_USER_TEMPLATE.format(
                system_prompt=self.build_system_prompt(),
                context=formatted_context,
                user_message=user_message
            )
        
        elif "phi" in self.model_key:
            system = self.build_system_prompt()
            user_part = PHI_USER_TEMPLATE.format(
                context=formatted_context,
                user_message=user_message
            )
            return system + "\n" + user_part
        
        else:
            # Fallback
            return f"{self.build_system_prompt()}\n\n{formatted_context}\n\n{user_message}"
    
    def _format_context(self, context: str) -> str:
        """Context'i formatla"""
        if not context or len(context.strip()) == 0:
            return ""
        
        # Uzunsa kırp (GENİŞLETİLDİ)
        max_context_chars = 5000  # 2000'den artırıldı
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "...\n[Context kırpıldı]"
        
        return context


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_prompt_builder(model_key: str, mode: ChatMode) -> PromptTemplateBuilder:
    """Factory function"""
    return PromptTemplateBuilder(model_key, mode)


# ============================================
# TEST (opsiyonel)
# ============================================

if __name__ == "__main__":
    # Test
    builder = PromptTemplateBuilder("mistral", ChatMode.FRIEND)
    prompt = builder.build_user_prompt("Merhaba", "[Profil]\nİsim: Ali")
    print(prompt[:500])