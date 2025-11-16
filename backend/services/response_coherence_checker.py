"""
backend/services/response_coherence_checker.py
==============================================
CEVAP TUTARLILIĞI KONTROLÜ

Görev:
- Cevap soruyla alakalı mı?
- Mantıklı mı?
- Hallüsinasyon var mı?
- Tutarlı mı?

Claude'un yaptığının basitleştirilmiş versiyonu
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import re


@dataclass
class CoherenceScore:
    """Tutarlılık skoru"""
    overall: float  # 0-1 genel skor
    relevance: float  # Soruyla alakalı mı?
    consistency: float  # Tutarlı mı?
    factuality: float  # Gerçekçi mi?
    completeness: float  # Eksiksiz mi?
    issues: List[str]  # Tespit edilen sorunlar


class ResponseCoherenceChecker:
    """
    Cevap tutarlılığı kontrol eden sistem
    """
    
    def __init__(self):
        # Hallüsinasyon işaretleri
        self.hallucination_indicators = [
            r'20(1[5-9]|2[0-9]|3[0-9]) yılında',  # Gelecek tarihler
            r'yakın zamanda yapılan araştırma',
            r'bilimsel olarak kanıtlanmıştır',
            r'uzmanlar söylüyor',
            r'son araştırmalar gösteriyor',
            # Kaynak olmadan iddia
        ]
        
        # Tutarsızlık işaretleri
        self.inconsistency_patterns = [
            r'(evet|hayır).*\b(ama|ancak|fakat)\b.*(hayır|evet)',
            # "Evet ama hayır" gibi çelişkiler
        ]
        
        # Alakasız ifadeler
        self.irrelevant_indicators = [
            'karnivora', 'domuz kaz', 'channel dairecisi',
            # Örneklerden öğrendiklerimiz
        ]
    
    def check_coherence(
        self,
        response: str,
        original_query: str,
        rag_sources: Optional[List[str]] = None
    ) -> CoherenceScore:
        """
        Cevabın tutarlılığını kontrol et
        
        Args:
            response: Model'in cevabı
            original_query: Kullanıcının sorusu
            rag_sources: RAG'den gelen kaynaklar (varsa)
            
        Returns:
            CoherenceScore
        """
        issues = []
        
        # 1. Relevance (Alakalılık)
        relevance = self._check_relevance(response, original_query)
        if relevance < 0.5:
            issues.append("Cevap soruyla alakasız görünüyor")
        
        # 2. Consistency (Tutarlılık)
        consistency = self._check_consistency(response)
        if consistency < 0.6:
            issues.append("Cevap içinde çelişkiler var")
        
        # 3. Factuality (Gerçekçilik)
        factuality = self._check_factuality(response, rag_sources)
        if factuality < 0.6:
            issues.append("Hallüsinasyon olabilir")
        
        # 4. Completeness (Eksiksizlik)
        completeness = self._check_completeness(response, original_query)
        if completeness < 0.5:
            issues.append("Cevap eksik/yarım")
        
        # Genel skor (ağırlıklı)
        overall = (
            relevance * 0.35 +
            consistency * 0.25 +
            factuality * 0.25 +
            completeness * 0.15
        )
        
        return CoherenceScore(
            overall=overall,
            relevance=relevance,
            consistency=consistency,
            factuality=factuality,
            completeness=completeness,
            issues=issues
        )
    
    def _check_relevance(self, response: str, query: str) -> float:
        """
        Cevap soruyla alakalı mı?
        
        Basit yöntem: Ortak kelime sayısı
        (Gerçek sistem: Semantic similarity)
        """
        # Query'den önemli kelimeleri çıkar
        query_words = set(self._extract_keywords(query.lower()))
        response_words = set(self._extract_keywords(response.lower()))
        
        if not query_words:
            return 0.5
        
        # Ortak kelime oranı
        common = query_words & response_words
        overlap_ratio = len(common) / len(query_words)
        
        # Soru türüne göre ayarla
        if '?' in query:
            # Soru ise, cevap içermeli
            if any(word in response.lower() for word in ['evet', 'hayır', 'şöyle', 'şu şekilde']):
                overlap_ratio += 0.2
        
        # Alakasız ifadeler var mı?
        for irrelevant in self.irrelevant_indicators:
            if irrelevant in response.lower():
                overlap_ratio -= 0.3  # Büyük ceza
        
        return min(1.0, max(0.0, overlap_ratio))
    
    def _check_consistency(self, response: str) -> float:
        """
        Cevap kendi içinde tutarlı mı?
        """
        score = 1.0
        
        # 1. Çelişki kontrolü
        for pattern in self.inconsistency_patterns:
            if re.search(pattern, response.lower()):
                score -= 0.3
        
        # 2. Tekrarlanan kelime grupları (copy-paste hatası)
        sentences = response.split('.')
        seen_sentences = set()
        for sent in sentences:
            sent_clean = sent.strip().lower()
            if sent_clean and sent_clean in seen_sentences:
                score -= 0.2  # Tekrar var
            seen_sentences.add(sent_clean)
        
        # 3. Yarım cümle var mı?
        if response and response[-1] not in '.!?':
            score -= 0.1
        
        return max(0.0, score)
    
    def _check_factuality(
        self,
        response: str,
        rag_sources: Optional[List[str]]
    ) -> float:
        """
        Gerçekçilik kontrolü (hallüsinasyon tespiti)
        """
        score = 1.0
        
        # 1. Hallüsinasyon işaretleri
        for indicator in self.hallucination_indicators:
            if re.search(indicator, response, re.IGNORECASE):
                # Eğer RAG'de kaynak varsa sorun yok
                if rag_sources:
                    # Kaynakta geçiyor mu kontrol et (basit)
                    found_in_source = False
                    for source in rag_sources:
                        if indicator[:20] in source:
                            found_in_source = True
                            break
                    if not found_in_source:
                        score -= 0.3
                else:
                    score -= 0.4  # Kaynak yok, hallüsinasyon!
        
        # 2. Sayısal iddialar (kaynak olmadan)
        number_claims = re.findall(r'\b\d+%\b|\b\d+\s*(milyon|milyar|bin)\b', response)
        if number_claims and not rag_sources:
            score -= 0.2  # Sayı veriyor ama kaynak yok
        
        return max(0.0, score)
    
    def _check_completeness(self, response: str, query: str) -> float:
        """
        Cevap eksiksiz mi?
        """
        score = 0.5  # Base
        
        # 1. Uzunluk kontrolü
        word_count = len(response.split())
        
        # Soru karmaşıklığına göre beklenen uzunluk
        query_words = len(query.split())
        
        if query_words < 10:
            # Basit soru, kısa cevap yeter
            expected_min = 20
            expected_max = 150
        else:
            # Karmaşık soru, detaylı cevap
            expected_min = 50
            expected_max = 300
        
        if expected_min <= word_count <= expected_max:
            score += 0.3
        elif word_count < expected_min:
            score -= 0.2  # Çok kısa
        elif word_count > expected_max * 2:
            score -= 0.1  # Çok uzun
        
        # 2. Cümle yapısı var mı?
        if '.' in response or '!' in response or '?' in response:
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Metinden önemli kelimeleri çıkar
        (Stop words çıkarılıyor)
        """
        # Türkçe stop words (basit liste)
        stop_words = {
            've', 'veya', 'ama', 'fakat', 'çünkü', 'için',
            'bir', 'bu', 'şu', 'o', 'de', 'da', 'mi', 'mı',
            'ile', 'gibi', 'kadar', 'daha', 'en', 'çok',
        }
        
        # Kelimeleri ayır
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Stop words'leri filtrele
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords


# ========================================
# GLOBAL INSTANCE
# ========================================

_coherence_checker = ResponseCoherenceChecker()


def check_response_coherence(
    response: str,
    original_query: str,
    rag_sources: Optional[List[str]] = None
) -> CoherenceScore:
    """Utility: Response coherence check"""
    return _coherence_checker.check_coherence(response, original_query, rag_sources)