"""
backend/services/response_planner.py
====================================
CEVAP PLANLAYICI - Claude Tarzı Response Planning

Görev:
- Karmaşık soruları parçala
- Cevap yapısını planla
- Model'e talimat ver

Claude'un yaptığının basit versiyonu
"""

from typing import List, Optional
from dataclasses import dataclass
from schemas.common import IntentLabel, ChatMode


@dataclass
class ResponsePlan:
    """Cevap planı"""
    structure: List[str]  # Cevabın yapısı (adımlar)
    tone: str  # Kullanılacak ton
    approach: str  # Yaklaşım (direct, step-by-step, example-based)
    special_instructions: List[str]  # Özel talimatlar


class ResponsePlanner:
    """
    Cevap planlayıcı sistem
    """
    
    def plan_response(
        self,
        query: str,
        intent: IntentLabel,
        mode: ChatMode,
        complexity: int
    ) -> ResponsePlan:
        """
        Soruya göre cevap planı oluştur
        
        Args:
            query: Kullanıcı sorusu
            intent: Intent
            mode: Chat mode
            complexity: Soru karmaşıklığı (1-10)
            
        Returns:
            ResponsePlan
        """
        # Intent'e göre strateji seç
        if intent == IntentLabel.CODE_HELP:
            return self._plan_code_response(query, complexity)
        
        elif intent == IntentLabel.EXPLAIN:
            return self._plan_explanation_response(query, complexity)
        
        elif intent == IntentLabel.COMPARE:
            return self._plan_comparison_response(query)
        
        elif intent == IntentLabel.RECOMMENDATION:
            return self._plan_recommendation_response(query)
        
        elif intent == IntentLabel.QUESTION:
            if complexity > 7:
                return self._plan_complex_question_response(query)
            else:
                return self._plan_simple_question_response(query)
        
        else:
            # Default plan
            return self._plan_default_response(query, intent)
    
    def _plan_code_response(self, query: str, complexity: int) -> ResponsePlan:
        """Kod sorusu için plan"""
        structure = [
            "Kısa açıklama (1-2 cümle)",
            "Kod örneği (çalışır kod)",
            "Kod açıklaması (satır satır)",
        ]
        
        if complexity > 6:
            structure.append("Alternatif yaklaşımlar")
            structure.append("Best practices")
        
        return ResponsePlan(
            structure=structure,
            tone="teknik ama anlaşılır",
            approach="example-based",
            special_instructions=[
                "Kod bloğu kullan (```python```)",
                "Çalışır kod ver, placeholder değil",
                "Yorumlar ekle",
            ]
        )
    
    def _plan_explanation_response(self, query: str, complexity: int) -> ResponsePlan:
        """Açıklama sorusu için plan"""
        structure = [
            "Tanım (ne olduğu)",
            "Neden önemli/nasıl çalışır",
        ]
        
        if complexity > 5:
            structure.append("Detaylı açıklama")
            structure.append("Örnekler")
        
        if 'basit' in query.lower() or 'anlaşılır' in query.lower():
            structure.insert(0, "Basit terimlerle özet")
            approach = "eli5"  # Explain Like I'm 5
        else:
            approach = "step-by-step"
        
        return ResponsePlan(
            structure=structure,
            tone="eğitici ve net",
            approach=approach,
            special_instructions=[
                "Jargon varsa açıkla",
                "Günlük örnekler ver",
            ]
        )
    
    def _plan_comparison_response(self, query: str) -> ResponsePlan:
        """Karşılaştırma sorusu için plan"""
        # "Python mu JavaScript mi?" gibi soruları parse et
        items_to_compare = self._extract_comparison_items(query)
        
        structure = [
            "Kısa özet (hangisi hangi durumda)",
        ]
        
        if len(items_to_compare) == 2:
            structure.append(f"Birinci seçenek: {items_to_compare[0]}")
            structure.append(f"İkinci seçenek: {items_to_compare[1]}")
            structure.append("Karşılaştırma tablosu (artı/eksi)")
            structure.append("Sonuç ve öneri")
        else:
            structure.append("Seçenekleri açıkla")
            structure.append("Farklarını listele")
        
        return ResponsePlan(
            structure=structure,
            tone="tarafsız ve objektif",
            approach="comparative",
            special_instructions=[
                "Her seçeneği dengeli anlat",
                "Kullanım senaryolarını ver",
                "Net sonuç/öneri ver",
            ]
        )
    
    def _plan_recommendation_response(self, query: str) -> ResponsePlan:
        """Öneri sorusu için plan"""
        structure = [
            "Durumu anla (kullanıcı ne istiyor)",
            "Öneri 1 (en iyi seçenek)",
            "Öneri 2 (alternatif)",
            "Neden bu önerileri verdin",
        ]
        
        return ResponsePlan(
            structure=structure,
            tone="yardımcı ve destekleyici",
            approach="recommendation",
            special_instructions=[
                "Kullanıcı bağlamını dikkate al",
                "Pratik öneriler ver",
                "İlk adımı söyle",
            ]
        )
    
    def _plan_complex_question_response(self, query: str) -> ResponsePlan:
        """Karmaşık soru için plan"""
        structure = [
            "Soruyu parçala (alt sorular)",
            "Her parçayı sırayla cevapla",
            "Genel sonuç/özet",
        ]
        
        return ResponsePlan(
            structure=structure,
            tone="düşünceli ve sistematik",
            approach="step-by-step",
            special_instructions=[
                "Mantıklı sırayla ilerle",
                "Bağlantıları açıkla",
                "Sonuçta özet ver",
            ]
        )
    
    def _plan_simple_question_response(self, query: str) -> ResponsePlan:
        """Basit soru için plan"""
        structure = [
            "Direkt cevap (1-2 cümle)",
        ]
        
        if '?' in query:
            structure.append("Kısa detay (gerekirse)")
        
        return ResponsePlan(
            structure=structure,
            tone="net ve kısa",
            approach="direct",
            special_instructions=[
                "Fazla detaya girme",
                "Dolambaç yapma",
            ]
        )
    
    def _plan_default_response(self, query: str, intent: IntentLabel) -> ResponsePlan:
        """Varsayılan plan"""
        return ResponsePlan(
            structure=["Cevap ver"],
            tone="doğal",
            approach="conversational",
            special_instructions=[]
        )
    
    def _extract_comparison_items(self, query: str) -> List[str]:
        """
        Karşılaştırma sorularından öğeleri çıkar
        
        Örnek: "Python mu JavaScript mi?" → ["Python", "JavaScript"]
        """
        import re
        
        # "X mi yoksa Y mi?" pattern
        match = re.search(r'(\w+)\s+m[iuıü]\s+yoksa\s+(\w+)', query, re.IGNORECASE)
        if match:
            return [match.group(1), match.group(2)]
        
        # "X vs Y" pattern
        match = re.search(r'(\w+)\s+vs\s+(\w+)', query, re.IGNORECASE)
        if match:
            return [match.group(1), match.group(2)]
        
        return []
    
    def build_planning_instructions(self, plan: ResponsePlan) -> str:
        """
        Plan'dan model için talimat oluştur
        
        Bu model'e gönderilecek
        """
        instructions = []
        
        # Yaklaşım
        approach_texts = {
            "direct": "Direkt ve kısa cevap ver.",
            "step-by-step": "Adım adım açıkla.",
            "example-based": "Örneklerle göster.",
            "comparative": "Objektif karşılaştır.",
            "recommendation": "Pratik öneriler sun.",
            "eli5": "Çok basit terimlerle açıkla (5 yaşında birine anlatır gibi).",
        }
        instructions.append(approach_texts.get(plan.approach, ""))
        
        # Yapı
        if plan.structure:
            instructions.append("\nCevap yapısı:")
            for i, step in enumerate(plan.structure, 1):
                instructions.append(f"{i}. {step}")
        
        # Özel talimatlar
        if plan.special_instructions:
            instructions.append("\nÖnemli:")
            for inst in plan.special_instructions:
                instructions.append(f"• {inst}")
        
        return "\n".join(instructions)


# ========================================
# GLOBAL INSTANCE
# ========================================

_response_planner = ResponsePlanner()


def plan_response(
    query: str,
    intent: IntentLabel,
    mode: ChatMode,
    complexity: int
) -> ResponsePlan:
    """Utility: Response planning"""
    return _response_planner.plan_response(query, intent, mode, complexity)


def build_planning_instructions(plan: ResponsePlan) -> str:
    """Utility: Build instructions from plan"""
    return _response_planner.build_planning_instructions(plan)