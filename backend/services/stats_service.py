"""
services/stats_service.py
-------------------------
Sistem istatistiklerini toplar ve /api/stats endpoint'i için
StatsSummary / StatsResponse üretir.

Kaynaklar:
- chat_history.db  -> toplam soru, toplam mesaj
- knowledge.db     -> doküman sayısı, chunk sayısı
- (ileride) web scraping istatistikleri, model kullanım istatistikleri
"""

from __future__ import annotations

from typing import Dict

from schemas.common import StatsSummary
from services import chat_db
from services.db import fetch_val


# ---------------------------------------------------------------------------
# Knowledge DB İstatistikleri
# ---------------------------------------------------------------------------

def get_total_documents() -> int:
    """
    knowledge.db içindeki doküman sayısını döner.
    """
    sql = "SELECT COUNT(*) AS cnt FROM documents;"
    value = fetch_val(sql, db="knowledge")
    return int(value or 0)


def get_total_chunks() -> int:
    """
    knowledge.db içindeki chunk sayısını döner.
    İstersen ileride daha detaylı kullanabiliriz.
    """
    sql = "SELECT COUNT(*) AS cnt FROM chunks;"
    value = fetch_val(sql, db="knowledge")
    return int(value or 0)


def get_total_scraped_sites() -> int:
    """
    Web scraping istatistiği:
    Şimdilik knowledge_stats tablosunda 'scraped_sites' key'i varsa onu kullanır,
    yoksa 0 döner.

    Not: Web scraping tarafını implemente ettiğimizde bu değeri artıracağız.
    """
    sql = "SELECT value FROM knowledge_stats WHERE key = 'scraped_sites';"
    value = fetch_val(sql, db="knowledge")
    return int(value or 0)


# ---------------------------------------------------------------------------
# Model Kullanım İstatistikleri (şimdilik basit stub)
# ---------------------------------------------------------------------------

def get_model_usage_stats() -> Dict[str, int]:
    """
    Hangi modelin kaç kez kullanıldığını dönen sözlük.

    Şimdilik DB'de ayrı bir tablo tutmuyoruz; ileride:
      - model_usage (model_name TEXT PRIMARY KEY, count INTEGER)
    gibi bir tablo ekleyip bunu gerçek veriye bağlayabiliriz.

    Şimdilik boş dict döndürmek sorun yaratmaz.
    """
    # Örnek taslak (ileride kullanmak için):
    # return {
    #   "qwen2.5-14b-instruct": 120,
    #   "deepseek-r1:8b": 40,
    #   "mistral-7b-instruct": 30,
    #   "phi3.5-mini-instruct": 25,
    # }
    return {}


# ---------------------------------------------------------------------------
# Toplu StatsSummary Üretimi
# ---------------------------------------------------------------------------

def get_stats_summary() -> StatsSummary:
    """
    /api/stats endpoint'i için StatsSummary modelini oluşturur.
    """
    total_queries = chat_db.get_total_queries()
    db_chat_rows = chat_db.get_db_chat_size_rows()
    total_docs = get_total_documents()
    total_chunks = get_total_chunks()
    total_scraped_sites = get_total_scraped_sites()

    # db_size alanını şimdilik:
    #   chat_messages satır sayısı + doküman + chunk sayısı toplamı gibi basit bir metrik yapıyoruz.
    db_size = db_chat_rows + total_docs + total_chunks

    model_usage = get_model_usage_stats()

    stats = StatsSummary(
    total_queries=total_queries,
    total_documents=total_docs,
    db_size=db_size,
    total_scraped_sites=total_scraped_sites,
    llm_usage=model_usage or None,  # ✅ llm_usage olarak değişti
    avg_response_time_ms=None,
)
    return stats
