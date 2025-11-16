"""
backend/services/adaptive_learning_system.py
============================================
ADAPTIVE LEARNING - Kullanıcı Feedback'i ile Öğrenme

Görev:
- Kullanıcı feedback'lerini topla
- Model performansını izle
- Hangi stratejiler işe yarıyor öğren
- Zamanla iyileş

Özellikler:
✅ Explicit feedback (kullanıcı beğendi/beğenmedi)
✅ Implicit feedback (tekrar sordu mu? düzeltti mi?)
✅ Strategy optimization
✅ A/B testing
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from config import get_settings

settings = get_settings()


@dataclass
class FeedbackEvent:
    """Feedback olayı"""
    user_id: str
    session_id: str
    message_id: Optional[int]
    query: str
    response: str
    model_used: str
    
    # Feedback tipleri
    explicit_rating: Optional[int]  # 1-5 arası (varsa)
    implicit_signal: str  # "retry", "clarification", "accepted", "ignored"
    
    # Metadata
    intent: str
    mode: str
    complexity: int
    response_time_ms: float
    
    timestamp: datetime


@dataclass
class LearningInsight:
    """Öğrenilen bilgi"""
    category: str  # "model_performance", "strategy", "user_preference"
    key: str
    value: float
    confidence: float
    sample_size: int


class AdaptiveLearningSystem:
    """
    Adaptive learning sistemi
    """
    
    def __init__(self):
        self.db_path = Path("data/adaptive_learning.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
class AdaptiveLearningSystem:
    """
    Adaptive learning sistemi
    """
    
    def __init__(self):
        self.db_path = Path("data/adaptive_learning.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):  # ← Bu satır class içinde, __init__'den sonra
        """Database tabloları oluştur"""
        conn = sqlite3.connect(str(self.db_path))
        
        # Feedback olayları tablosu
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                message_id INTEGER,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                model_used TEXT NOT NULL,
                
                explicit_rating INTEGER,
                implicit_signal TEXT NOT NULL,
                
                intent TEXT,
                mode TEXT,
                complexity INTEGER,
                response_time_ms REAL,
                
                timestamp TEXT NOT NULL
            )
        """)
        
        # Index'leri AYRI komutlarla oluştur
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_user 
            ON feedback_events(user_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_model 
            ON feedback_events(model_used)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_signal 
            ON feedback_events(implicit_signal)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
            ON feedback_events(timestamp)
        """)
        
        # Öğrenilen insights tablosu
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value REAL NOT NULL,
                confidence REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                last_updated TEXT NOT NULL,
                
                UNIQUE(category, key)
            )
        """)
        
        # Insights için index
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_insights_category 
            ON learning_insights(category)
        """)
        
        conn.commit()
        conn.close()
    
    def record_feedback(self, event: FeedbackEvent):  # ← Sonraki metodlar buradan devam
        """
        Feedback kaydı
        """
        # ... geri kalan kodlar
    
    def record_feedback(self, event: FeedbackEvent):
        """
        Feedback kaydı
        
        Her cevaptan sonra çağrılır (implicit signal ile)
        """
        conn = sqlite3.connect(str(self.db_path))
        
        conn.execute("""
            INSERT INTO feedback_events (
                user_id, session_id, message_id, query, response, model_used,
                explicit_rating, implicit_signal,
                intent, mode, complexity, response_time_ms,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.user_id,
            event.session_id,
            event.message_id,
            event.query,
            event.response,
            event.model_used,
            event.explicit_rating,
            event.implicit_signal,
            event.intent,
            event.mode,
            event.complexity,
            event.response_time_ms,
            event.timestamp.isoformat(),
        ))
        
        conn.commit()
        conn.close()
    
    def record_explicit_feedback(
        self,
        user_id: str,
        message_id: int,
        rating: int  # 1-5 arası
    ):
        """
        Kullanıcı direkt feedback verdi (👍/👎 butonu)
        """
        # Event'i güncelle
        conn = sqlite3.connect(str(self.db_path))
        
        conn.execute("""
            UPDATE feedback_events
            SET explicit_rating = ?
            WHERE user_id = ? AND message_id = ?
        """, (rating, user_id, message_id))
        
        conn.commit()
        conn.close()
        
        # Hemen öğren
        self._update_insights()
    
    def detect_implicit_signal(
        self,
        current_query: str,
        previous_query: Optional[str],
        previous_response: Optional[str],
        user_id: str
    ) -> str:
        """
        Implicit feedback tespit et
        
        Kullanıcı davranışından anlam çıkar:
        - Aynı soruyu tekrar sordu → "retry" (cevap kötüydü)
        - "Anlamadım" dedi → "clarification" (yeterince açık değildi)
        - Yeni konuya geçti → "accepted" (cevap iyiydi)
        - Hiç cevap vermedi → "ignored" (ilgisiz buldu)
        """
        if not previous_query or not previous_response:
            return "new_conversation"
        
        current_lower = current_query.lower()
        prev_lower = previous_query.lower()
        
        # 1. Aynı soruyu tekrar soruyor mu?
        similarity = self._text_similarity(current_lower, prev_lower)
        if similarity > 0.7:
            return "retry"  # Cevap yetersizdi
        
        # 2. Açıklama istiyor mu?
        clarification_keywords = [
            'anlamadım', 'ne demek', 'açıklar mısın',
            'daha basit', 'tekrar anlatır mısın'
        ]
        if any(kw in current_lower for kw in clarification_keywords):
            return "clarification"  # Yeterince açık değildi
        
        # 3. Devam ediyor mu? (aynı topic)
        continuation_keywords = ['peki', 'ee', 'o zaman', 'ayrıca']
        if any(kw in current_lower for kw in continuation_keywords):
            return "continuation"  # İyi gidiyor, devam ediyor
        
        # 4. Yeni konu (cevap kabul edildi)
        return "accepted"
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        İki text'in benzerliği (basit)
        
        Gerçek sistem: Embedding similarity kullanır
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _update_insights(self):
        """
        Feedback'lerden insight'lar çıkar
        
        Periyodik olarak çağrılır (her 10 feedback'te bir)
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # 1. Model performansı
        self._learn_model_performance(conn)
        
        # 2. Intent-Model matching
        self._learn_intent_model_matching(conn)
        
        # 3. Complexity-Model matching
        self._learn_complexity_model_matching(conn)
        
        # 4. User preferences
        self._learn_user_preferences(conn)
        
        conn.close()
    
    def _learn_model_performance(self, conn):
        """Model performans skorları"""
        # Her model için ortalama skor hesapla
        cursor = conn.execute("""
            SELECT 
                model_used,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN explicit_rating IS NOT NULL THEN explicit_rating
                    WHEN implicit_signal = 'accepted' THEN 5
                    WHEN implicit_signal = 'continuation' THEN 4
                    WHEN implicit_signal = 'clarification' THEN 2
                    WHEN implicit_signal = 'retry' THEN 1
                    ELSE 3
                END) as avg_score
            FROM feedback_events
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY model_used
            HAVING total >= 10
        """)
        
        for row in cursor.fetchall():
            self._save_insight(
                category="model_performance",
                key=row['model_used'],
                value=row['avg_score'] / 5.0,  # Normalize to 0-1
                sample_size=row['total']
            )
    
    def _learn_intent_model_matching(self, conn):
        """Hangi intent için hangi model daha iyi?"""
        cursor = conn.execute("""
            SELECT 
                intent,
                model_used,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN explicit_rating IS NOT NULL THEN explicit_rating
                    WHEN implicit_signal = 'accepted' THEN 5
                    WHEN implicit_signal = 'continuation' THEN 4
                    ELSE 3
                END) as avg_score
            FROM feedback_events
            WHERE timestamp > datetime('now', '-30 days')
            AND intent IS NOT NULL
            GROUP BY intent, model_used
            HAVING total >= 5
        """)
        
        for row in cursor.fetchall():
            key = f"{row['intent']}:{row['model_used']}"
            self._save_insight(
                category="intent_model_match",
                key=key,
                value=row['avg_score'] / 5.0,
                sample_size=row['total']
            )
    
    def _learn_complexity_model_matching(self, conn):
        """Hangi complexity için hangi model?"""
        cursor = conn.execute("""
            SELECT 
                CASE
                    WHEN complexity <= 3 THEN 'low'
                    WHEN complexity <= 6 THEN 'medium'
                    ELSE 'high'
                END as complexity_bucket,
                model_used,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN implicit_signal = 'accepted' THEN 5
                    WHEN implicit_signal = 'retry' THEN 1
                    ELSE 3
                END) as avg_score
            FROM feedback_events
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY complexity_bucket, model_used
            HAVING total >= 5
        """)
        
        for row in cursor.fetchall():
            key = f"{row['complexity_bucket']}:{row['model_used']}"
            self._save_insight(
                category="complexity_model_match",
                key=key,
                value=row['avg_score'] / 5.0,
                sample_size=row['total']
            )
    
    def _learn_user_preferences(self, conn):
        """Kullanıcı tercihleri (kişiye özel)"""
        # Örnek: response_time'a tolerans
        cursor = conn.execute("""
            SELECT 
                CASE
                    WHEN response_time_ms < 2000 THEN 'fast'
                    WHEN response_time_ms < 5000 THEN 'medium'
                    ELSE 'slow'
                END as speed_bucket,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN implicit_signal = 'accepted' THEN 1
                    ELSE 0
                END) as acceptance_rate
            FROM feedback_events
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY speed_bucket
        """)
        
        for row in cursor.fetchall():
            self._save_insight(
                category="speed_preference",
                key=row['speed_bucket'],
                value=row['acceptance_rate'],
                sample_size=row['total']
            )
    
    def _save_insight(
        self,
        category: str,
        key: str,
        value: float,
        sample_size: int
    ):
        """Insight kaydet/güncelle"""
        # Confidence: Sample size'a göre
        confidence = min(1.0, sample_size / 100.0)
        
        conn = sqlite3.connect(str(self.db_path))
        
        conn.execute("""
            INSERT INTO learning_insights (
                category, key, value, confidence, sample_size, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(category, key) DO UPDATE SET
                value = excluded.value,
                confidence = excluded.confidence,
                sample_size = excluded.sample_size,
                last_updated = excluded.last_updated
        """, (
            category,
            key,
            value,
            confidence,
            sample_size,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_model_recommendation(
        self,
        intent: str,
        complexity: int,
        available_models: List[str]
    ) -> Tuple[str, float]:
        """
        Öğrenilen bilgilerden en iyi modeli öner
        
        Returns:
            (model_name, confidence)
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        scores = {}
        
        # 1. Intent match skorları
        cursor = conn.execute("""
            SELECT key, value, confidence
            FROM learning_insights
            WHERE category = 'intent_model_match'
            AND key LIKE ?
        """, (f"{intent}:%",))
        
        for row in cursor.fetchall():
            model = row['key'].split(':')[1]
            if model in available_models:
                scores[model] = scores.get(model, 0) + row['value'] * row['confidence']
        
        # 2. Complexity match skorları
        complexity_bucket = 'low' if complexity <= 3 else ('medium' if complexity <= 6 else 'high')
        
        cursor = conn.execute("""
            SELECT key, value, confidence
            FROM learning_insights
            WHERE category = 'complexity_model_match'
            AND key LIKE ?
        """, (f"{complexity_bucket}:%",))
        
        for row in cursor.fetchall():
            model = row['key'].split(':')[1]
            if model in available_models:
                scores[model] = scores.get(model, 0) + row['value'] * row['confidence']
        
        # 3. Genel model performansı
        cursor = conn.execute("""
            SELECT key, value, confidence
            FROM learning_insights
            WHERE category = 'model_performance'
        """)
        
        for row in cursor.fetchall():
            model = row['key']
            if model in available_models:
                scores[model] = scores.get(model, 0) + row['value'] * row['confidence'] * 0.5
        
        conn.close()
        
        if not scores:
            # Öğrenilmiş bir şey yok, None dön
            return None, 0.0
        
        # En yüksek skorlu model
        best_model = max(scores, key=scores.get)
        best_score = scores[best_model]
        
        # Normalize confidence
        max_possible = 3.0  # 3 kategori
        confidence = min(1.0, best_score / max_possible)
        
        return best_model, confidence
    
    def get_statistics(self) -> Dict:
        """İstatistikler (dashboard için)"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        stats = {}
        
        # Total feedback count
        cursor = conn.execute("SELECT COUNT(*) as total FROM feedback_events")
        stats['total_feedback'] = cursor.fetchone()['total']
        
        # Explicit ratings
        cursor = conn.execute("""
            SELECT AVG(explicit_rating) as avg_rating
            FROM feedback_events
            WHERE explicit_rating IS NOT NULL
        """)
        row = cursor.fetchone()
        stats['avg_explicit_rating'] = row['avg_rating'] if row['avg_rating'] else 0
        
        # Implicit signals distribution
        cursor = conn.execute("""
            SELECT implicit_signal, COUNT(*) as count
            FROM feedback_events
            GROUP BY implicit_signal
        """)
        stats['implicit_signals'] = {row['implicit_signal']: row['count'] for row in cursor.fetchall()}
        
        # Learned insights count
        cursor = conn.execute("SELECT COUNT(*) as total FROM learning_insights")
        stats['total_insights'] = cursor.fetchone()['total']
        
        conn.close()
        
        return stats


# ========================================
# GLOBAL INSTANCE
# ========================================

_adaptive_learning = AdaptiveLearningSystem()


def record_feedback(event: FeedbackEvent):
    """Utility: Feedback kaydet"""
    _adaptive_learning.record_feedback(event)


def record_explicit_feedback(user_id: str, message_id: int, rating: int):
    """Utility: Explicit feedback"""
    _adaptive_learning.record_explicit_feedback(user_id, message_id, rating)


def detect_implicit_signal(
    current_query: str,
    previous_query: Optional[str],
    previous_response: Optional[str],
    user_id: str
) -> str:
    """Utility: Implicit signal tespit et"""
    return _adaptive_learning.detect_implicit_signal(
        current_query, previous_query, previous_response, user_id
    )


def get_model_recommendation(
    intent: str,
    complexity: int,
    available_models: List[str]
) -> Tuple[str, float]:
    """Utility: Öğrenilmiş bilgilerden model öner"""
    return _adaptive_learning.get_model_recommendation(intent, complexity, available_models)


def get_learning_statistics() -> Dict:
    """Utility: İstatistikler"""
    return _adaptive_learning.get_statistics()

def get_learning_stats() -> dict:
    """
    Learning system istatistiklerini döndür
    
    Returns:
        dict: İstatistikler
    """
    global _feedback_events
    
    if not _feedback_events:
        return {
            "total_events": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "by_model": {},
            "by_intent": {},
            "avg_response_time_ms": 0
        }
    
    # İstatistikleri hesapla
    total = len(_feedback_events)
    positive = sum(1 for e in _feedback_events if e.implicit_signal == "positive")
    negative = sum(1 for e in _feedback_events if e.implicit_signal == "negative")
    neutral = sum(1 for e in _feedback_events if e.implicit_signal == "neutral")
    
    # Model bazında
    by_model = {}
    for event in _feedback_events:
        model = event.model_used or "unknown"
        if model not in by_model:
            by_model[model] = {"count": 0, "positive": 0, "negative": 0}
        by_model[model]["count"] += 1
        if event.implicit_signal == "positive":
            by_model[model]["positive"] += 1
        elif event.implicit_signal == "negative":
            by_model[model]["negative"] += 1
    
    # Intent bazında
    by_intent = {}
    for event in _feedback_events:
        intent = event.intent or "unknown"
        if intent not in by_intent:
            by_intent[intent] = {"count": 0, "positive": 0}
        by_intent[intent]["count"] += 1
        if event.implicit_signal == "positive":
            by_intent[intent]["positive"] += 1
    
    # Ortalama response time
    avg_time = sum(e.response_time_ms for e in _feedback_events if e.response_time_ms) / total if total > 0 else 0
    
    return {
        "total_events": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "by_model": by_model,
        "by_intent": by_intent,
        "avg_response_time_ms": avg_time
    }