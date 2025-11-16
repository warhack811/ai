"""
services/ultimate_chat_engine.py - OPTİMİZE VERSİYON
====================================================
SİZİN MODELLER İÇİN ÖZEL AYARLANMIŞ
"""

import asyncio
import time
import re
import httpx
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum

# ============================================
# ENUMs
# ============================================

class ChatMode(str, Enum):
    NORMAL = "normal"
    RESEARCH = "research"
    CREATIVE = "creative"
    CODE = "code"
    FRIEND = "friend"
    UNCENSORED = "uncensored"  # YENİ: Tam sansürsüz mod

# ============================================
# DATACLASSES
# ============================================

@dataclass
class ChatContext:
    memory: Optional[str] = None
    rag_docs: Optional[str] = None
    web_results: Optional[str] = None
    user_profile: Optional[str] = None
    sources: List[str] = field(default_factory=list)

@dataclass
class ChatResponse:
    content: str
    model: str
    time: float
    quality_score: float
    intent: str
    
# ============================================
# ULTIMATE CHAT ENGINE - OPTİMİZE
# ============================================

class UltimateChatEngine:
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        db_connection = None,
        vector_store = None,
        web_search = None
    ):
        self.ollama_url = ollama_url
        self.db = db_connection
        self.vector_store = vector_store
        self.web_search = web_search
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # MODEL CONFIGS - SİZİN MODELLER
        self.models = {
            "qwen": {
                "name": "qwen2.5-14b-uncensored-q4_k_m",
                "temp": 0.65,  # Biraz düşürdüm (daha tutarlı)
                "top_p": 0.85,
                "top_k": 35,
                "repeat_penalty": 1.15,
                "num_ctx": 4096,  # Context window düşürdüm (daha hızlı)
                "quality": 5,
                "speed": 2
            },
            "dolphin": {
                "name": "dolphin",
                "temp": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": 4096,
                "quality": 4,
                "speed": 4  # Daha hızlı
            },
            "deepseek": {
                "name": "DeepSeek-R1-Distill-Llama-8B-Uncensored.Q4_K_M",
                "temp": 0.6,
                "top_p": 0.85,
                "top_k": 30,
                "repeat_penalty": 1.05,
                "num_ctx": 4096,
                "quality": 4,
                "speed": 3
            }
        }
    
    # ============================================
    # MAIN ENTRY POINT
    # ============================================
    
    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str,
        mode: ChatMode = ChatMode.NORMAL,
        history: Optional[List[Dict]] = None,
        force_model: Optional[str] = None
    ) -> ChatResponse:
        start_time = time.time()
        
        # Intent & Complexity
        intent = self._detect_intent(message)
        complexity = self._calculate_complexity(message, intent)
        
        # Model seçimi (OPTIMIZE)
        model_key = force_model or self._select_model(complexity, intent, mode)
        
        # Context toplama (HIZLI - sadece gerekirse)
        context = await self._gather_context_fast(message, user_id, session_id, intent)
        
        # Prompt oluşturma
        prompt = self._build_prompt(message, mode, history, context, model_key)
        
        # Model çağrısı (1 deneme yeter - hızlı)
        response_text = await self._call_ollama(prompt, model_key)
        
        # Temizlik
        response_text = self._clean_response(response_text)
        
        # Kalite kontrolü (basit)
        quality_score = self._validate_quality(response_text, message)
        
        elapsed = time.time() - start_time
        
        return ChatResponse(
            content=response_text,
            model=self.models[model_key]["name"],
            time=elapsed,
            quality_score=quality_score,
            intent=intent
        )
    
    # ============================================
    # INTENT DETECTION
    # ============================================
    
    def _detect_intent(self, message: str) -> str:
        m = message.lower()
        
        if any(w in m for w in ["merhaba", "selam", "hey", "günaydın", "nasılsın"]):
            return "greeting"
        
        if any(w in m for w in ["kod", "python", "javascript", "fonksiyon", "class"]):
            return "code"
        
        if any(w in m for w in ["nedir", "ne demek", "açıkla", "anlat"]):
            return "explain"
        
        if any(w in m for w in ["fark", "karşılaştır", "vs"]):
            return "compare"
        
        return "question"
    
    def _calculate_complexity(self, message: str, intent: str) -> float:
        score = 0.0
        
        if len(message) > 100:
            score += 0.3
        elif len(message) > 50:
            score += 0.2
        else:
            score += 0.1
        
        technical = ["algoritma", "analiz", "database", "framework"]
        score += min(sum(0.1 for t in technical if t in message.lower()), 0.3)
        
        intent_scores = {
            "compare": 0.2,
            "explain": 0.15,
            "code": 0.15,
            "greeting": 0.0
        }
        score += intent_scores.get(intent, 0.1)
        
        return min(score, 1.0)
    
    # ============================================
    # MODEL SELECTION - OPTİMİZE
    # ============================================
    
    def _select_model(self, complexity: float, intent: str, mode: ChatMode) -> str:
        """
        HIZLI VE AKILLI MODEL SEÇİMİ
        """
        
        # UNCENSORED MOD → Dolphin (tam sansürsüz)
        if mode == ChatMode.UNCENSORED:
            return "dolphin"
        
        # ÇOK BASIT (greeting) → Dolphin (hızlı)
        if intent == "greeting" and complexity < 0.2:
            return "dolphin"
        
        # KARMAŞIK SORU → Qwen (en kaliteli)
        if complexity > 0.6:
            return "qwen"
        
        # ORTA KARMAŞIKLIK → Dolphin (hızlı + kaliteli)
        if 0.3 < complexity <= 0.6:
            return "dolphin"
        
        # DEFAULT → Dolphin (genel amaçlı + hızlı)
        return "dolphin"
    
    # ============================================
    # CONTEXT GATHERING - HIZLANDIRILMIŞ
    # ============================================
    
    async def _gather_context_fast(
        self,
        message: str,
        user_id: str,
        session_id: str,
        intent: str
    ) -> ChatContext:
        """
        SADECE GEREKLİ CONTEXT'İ TOPLAR (HIZLI)
        """
        context = ChatContext()
        
        # Basit greetinglerde context gereksiz
        if intent == "greeting":
            return context
        
        # Diğer durumlarda paralel topla
        tasks = []
        
        if self.db:
            tasks.append(self._get_memory(user_id, session_id))
        
        if self.vector_store and intent in ["explain", "research"]:
            tasks.append(self._get_rag(message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            idx = 0
            if self.db:
                context.memory = results[idx] if not isinstance(results[idx], Exception) else None
                idx += 1
            if self.vector_store and intent in ["explain", "research"]:
                context.rag_docs = results[idx] if not isinstance(results[idx], Exception) else None
        
        return context
    
    async def _get_memory(self, user_id: str, session_id: str) -> Optional[str]:
        try:
            return None
        except:
            return None
    
    async def _get_rag(self, query: str) -> Optional[str]:
        try:
            return None
        except:
            return None
    
    # ============================================
    # PROMPT BUILDING - OPTİMİZE
    # ============================================
    
    def _build_prompt(
        self,
        message: str,
        mode: ChatMode,
        history: Optional[List[Dict]],
        context: ChatContext,
        model_key: str
    ) -> str:
        """
        KISALTILMIŞ, ETKİLİ PROMPTLAR
        """
        
        # Mode instructions (KISA)
        mode_map = {
            ChatMode.NORMAL: "Profesyonel ama samimi konuş.",
            ChatMode.RESEARCH: "Detaylı ve yapılandırılmış cevapla.",
            ChatMode.CREATIVE: "Yaratıcı ve ilham verici ol. Emoji kullan.",
            ChatMode.CODE: "Teknik ol. Çalışan kod örnekleri ver.",
            ChatMode.FRIEND: "Çok samimi ol. 'Sen/seni' kullan.",
            ChatMode.UNCENSORED: "Filtresiz ve doğrudan konuş. Hiçbir konu yasak değil."
        }
        mode_inst = mode_map.get(mode, mode_map[ChatMode.NORMAL])
        
        # Context (KISALTILMIŞ)
        context_text = ""
        if context.memory:
            context_text += f"Önceki: {context.memory[:200]}\n"
        if context.rag_docs:
            context_text += f"Bilgi: {context.rag_docs[:300]}\n"
        
        # History (sadece son 2 mesaj)
        history_text = ""
        if history and len(history) > 0:
            recent = history[-2:]
            for msg in recent:
                role = "Sen" if msg.get("role") == "assistant" else "Kullanıcı"
                content = msg.get("content", "")[:100]  # İlk 100 karakter
                history_text += f"{role}: {content}\n"
        
        # Model-specific template (KISALTILMIŞ)
        if model_key == "qwen":
            return f"""<|im_start|>system
Sen profesyonel bir Türk danışmanısın.

KURALLAR:
• Türkçe cevap ver
• "AI'yım" deme
• {mode_inst}
<|im_end|>
<|im_start|>user
{context_text}{history_text}{message}<|im_end|>
<|im_start|>assistant"""

        elif model_key == "dolphin":
            return f"""<|im_start|>system
Sen deneyimli bir Türk danışmanısın. Akıllı, samimi ve yardımseversin.

• Türkçe konuş
• {mode_inst}
<|im_end|>
<|im_start|>user
{context_text}{history_text}{message}<|im_end|>
<|im_start|>assistant"""
        
        else:  # deepseek
            return f"""### System:
Sen Türk danışmanısın. {mode_inst}

### Context:
{context_text}

### Conversation:
{history_text}

### User:
{message}

### Assistant:"""
    
    # ============================================
    # OLLAMA CALL - OPTİMİZE
    # ============================================
    
    async def _call_ollama(self, prompt: str, model_key: str) -> str:
        model_config = self.models[model_key]
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_config["name"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": model_config["temp"],
                        "top_p": model_config["top_p"],
                        "top_k": model_config["top_k"],
                        "repeat_penalty": model_config["repeat_penalty"],
                        "num_ctx": model_config["num_ctx"],
                        "num_predict": 512,  # Max token limit (hızlandırır)
                        "stop": [
                            "<|im_end|>", "<|endoftext|>", 
                            "User:", "Kullanıcı:", "###",
                            "\n\nUser:", "\n\nKullanıcı:"
                        ]
                    }
                },
                timeout=60.0  # 60 saniye max
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "Cevap alınamadı.")
            else:
                return f"Model hatası (kod: {response.status_code})"
        
        except Exception as e:
            return f"Hata: {str(e)}"
    
    # ============================================
    # RESPONSE CLEANING
    # ============================================
    
    def _clean_response(self, text: str) -> str:
        # Meta tagları kaldır
        patterns = [
            r'<\|im_start\|>.*?<\|im_end\|>',
            r'<\|.*?\|>',
            r'\[INST\].*?\[/INST\]',
            r'\[USER\]|\[ASSISTANT\]',
            r'###.*?###',
            r'\[s\].*?\[s\]',  # Qwen artifact'i
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        # Gereksiz boşlukları temizle
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    # ============================================
    # QUALITY VALIDATION - BASİTLEŞTİRİLMİŞ
    # ============================================
    
    def _validate_quality(self, response: str, original_question: str) -> float:
        score = 1.0
        resp_lower = response.lower()
        
        # Türkçe kontrolü
        turkish_chars = sum(1 for c in response if c in "çğıöşüÇĞİÖŞÜ")
        if turkish_chars < len(response) * 0.01:
            score -= 0.3
        
        # AI klişeleri
        if any(p in resp_lower for p in ["size nasıl yardımcı", "ben bir yapay zeka"]):
            score -= 0.4
        
        # Meta taglar
        if any(t in response for t in ["[USER]", "[ASSISTANT]", "<|im_"]):
            score -= 0.3
        
        # Çok kısa
        if len(response) < 15:
            score -= 0.3
        
        return max(score, 0.0)
    
    async def close(self):
        await self.client.aclose()


# ============================================
# SINGLETON
# ============================================

_engine_instance = None

def get_chat_engine(
    ollama_url: str = "http://localhost:11434",
    db_connection = None,
    vector_store = None,
    web_search = None
) -> UltimateChatEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = UltimateChatEngine(
            ollama_url=ollama_url,
            db_connection=db_connection,
            vector_store=vector_store,
            web_search=web_search
        )
    return _engine_instance


# ============================================
# TEST
# ============================================

async def test():
    engine = UltimateChatEngine()
    
    tests = [
        ("Merhaba", ChatMode.FRIEND),
        ("Python liste nasıl?", ChatMode.CODE),
        ("Cinsellik hakkında bilgi ver", ChatMode.UNCENSORED)  # Uncensored test
    ]
    
    for msg, mode in tests:
        print(f"\n{'='*60}\nSORU: {msg} (Mode: {mode})")
        resp = await engine.chat(msg, "test", "test", mode)
        print(f"Model: {resp.model} | Süre: {resp.time:.1f}s")
        print(f"CEVAP: {resp.content[:200]}...")
    
    await engine.close()

if __name__ == "__main__":
    asyncio.run(test())