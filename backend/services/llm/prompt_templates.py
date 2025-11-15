"""
services/llm/prompt_templates.py
--------------------------------
Her model için native prompt templates
"""

from typing import Dict, List
from schemas.common import ChatMode

# ============================================
# QWEN 2.5 TEMPLATE (ChatML Format)
# ============================================

QWEN_SYSTEM_TEMPLATE = """<|im_start|>system
Sen Türkçe konuşan, akıllı ve yardımsever bir AI asistansın.

ÖNEMLİ KURALLAR:
- Kullanıcı Türkçe yazıyorsa MUTLAKA Türkçe cevap ver
- Doğal, akıcı ve samimi bir dille konuş
- Emin olmadığın konularda "Tam emin değilim" de, asla uydurma
- Kod sorularında önce kısa açıklama yap, sonra ```kod``` bloğu ile örnek ver
- Cevabına asla [USER], [ASSISTANT], [INST] gibi meta tag ekleme

{mode_instruction}
<|im_end|>"""

QWEN_USER_TEMPLATE = """<|im_start|>user
{context}

{user_message}<|im_end|>
<|im_start|>assistant"""


# ============================================
# DEEPSEEK R1 TEMPLATE (Reasoning Format)
# ============================================

DEEPSEEK_SYSTEM_TEMPLATE = """### System Instruction:
You are a reasoning AI assistant that thinks step-by-step in Turkish.

IMPORTANT RULES:
- Respond in Turkish if the user writes in Turkish
- Use chain-of-thought reasoning for complex questions
- Be precise and logical
- Never add meta tags like [USER], [ASSISTANT] in your response

{mode_instruction}"""

DEEPSEEK_USER_TEMPLATE = """### Context:
{context}

### User Query:
{user_message}

### Reasoning Process:
Let me think through this step by step in Turkish...

### Response:"""


# ============================================
# MISTRAL TEMPLATE (Instruct Format)
# ============================================

MISTRAL_SYSTEM_TEMPLATE = """Sen hızlı ve etkili bir Türkçe AI asistansın.

KURALLAR:
- Kısa ve öz cevaplar ver
- Türkçe yanıtla
- Meta tag kullanma ([USER], [ASSISTANT] gibi)

{mode_instruction}"""

MISTRAL_USER_TEMPLATE = """<s>[INST] {system_prompt}

{context}

{user_message} [/INST]"""


# ============================================
# PHI 3.5 TEMPLATE (Phi Format)
# ============================================

PHI_SYSTEM_TEMPLATE = """<|system|>
Sen küçük ama yetenekli bir Türkçe AI asistansın. Hızlı ve doğru cevaplar verirsin.

{mode_instruction}<|end|>"""

PHI_USER_TEMPLATE = """<|user|>
{context}

{user_message}<|end|>
<|assistant|>"""


# ============================================
# MODE-SPECIFIC INSTRUCTIONS
# ============================================

MODE_INSTRUCTIONS = {
    ChatMode.NORMAL: "Mod: Normal - Genel konularda yardımcı ol.",
    ChatMode.RESEARCH: "Mod: Araştırma - Detaylı, yapılandırılmış ve kaynak göstererek cevapla.",
    ChatMode.CREATIVE: "Mod: Yaratıcı - Daha imgesel, ilham verici ve yaratıcı ol.",
    ChatMode.CODE: "Mod: Kod - Teknik ve kesin ol. Çalışan kod örnekleri göster.",
    ChatMode.FRIEND: "Mod: Arkadaş - Samimi, destekleyici ve sıcak konuş.",
    ChatMode.TURKISH_TEACHER: "Mod: Türkçe Öğretmen - Dilbilgisi hatalarını nazikçe düzelt ve açıkla.",
}


# ============================================
# TEMPLATE BUILDER
# ============================================

class PromptTemplateBuilder:
    """
    Model ve mode'a göre optimize prompt üretir
    """
    
    def __init__(self, model_key: str, mode: ChatMode):
        self.model_key = model_key
        self.mode = mode
        self.mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS[ChatMode.NORMAL])
    
    def build_system_prompt(self) -> str:
        """Model için system prompt üret"""
        
        if self.model_key == "qwen":
            return QWEN_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif self.model_key == "deepseek":
            return DEEPSEEK_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif self.model_key == "mistral":
            return MISTRAL_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        elif self.model_key == "phi":
            return PHI_SYSTEM_TEMPLATE.format(
                mode_instruction=self.mode_instruction
            )
        
        else:
            # Fallback generic template
            return f"Sen bir AI asistansın. {self.mode_instruction}"
    
    def build_user_prompt(
        self,
        user_message: str,
        context: str = "",
    ) -> str:
        """Model için user prompt üret"""
        
        # Context formatting
        formatted_context = self._format_context(context) if context else ""
        
        if self.model_key == "qwen":
            system = self.build_system_prompt()
            user_part = QWEN_USER_TEMPLATE.format(
                context=formatted_context,
                user_message=user_message
            )
            return system + "\n" + user_part
        
        elif self.model_key == "deepseek":
            return DEEPSEEK_USER_TEMPLATE.format(
                context=formatted_context,
                user_message=user_message
            )
        
        elif self.model_key == "mistral":
            return MISTRAL_USER_TEMPLATE.format(
                system_prompt=self.build_system_prompt(),
                context=formatted_context,
                user_message=user_message
            )
        
        elif self.model_key == "phi":
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
        
        # Uzunsa kırp
        max_context_chars = 2000
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "..."
        
        return context


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_prompt_builder(model_key: str, mode: ChatMode) -> PromptTemplateBuilder:
    """Factory function"""
    return PromptTemplateBuilder(model_key, mode)