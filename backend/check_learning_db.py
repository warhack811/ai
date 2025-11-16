#!/usr/bin/env python3
"""
check_learning_db.py
===================
Adaptive Learning veritabanını kontrol et

Kullanım:
    python check_learning_db.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

DB_PATH = Path("backend/data/adaptive_learning.db")


def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")


def check_database():
    """Veritabanı kontrolü"""
    
    if not DB_PATH.exists():
        print(f"{Fore.RED}❌ Veritabanı bulunamadı: {DB_PATH}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Sistem henüz hiç soru almamış olabilir.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}✅ Veritabanı bulundu: {DB_PATH}{Style.RESET_ALL}")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ============================================
    # 1. FEEDBACK EVENTS
    # ============================================
    print_header("1. FEEDBACK EVENTS")
    
    cursor.execute("SELECT COUNT(*) as total FROM feedback_events")
    total = cursor.fetchone()['total']
    print(f"Toplam feedback kayıtları: {Fore.GREEN}{total}{Style.RESET_ALL}")
    
    if total == 0:
        print(f"{Fore.YELLOW}⚠️ Henüz hiç feedback kaydı yok{Style.RESET_ALL}")
    else:
        # Implicit signals dağılımı
        print(f"\n{Fore.YELLOW}Implicit Signals:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT implicit_signal, COUNT(*) as count
            FROM feedback_events
            GROUP BY implicit_signal
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            signal = row['implicit_signal']
            count = row['count']
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {signal:20s}: {count:3d} ({percentage:5.1f}%)")
        
        # Model kullanımı
        print(f"\n{Fore.YELLOW}Model Kullanımı:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT model_used, COUNT(*) as count
            FROM feedback_events
            GROUP BY model_used
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            model = row['model_used']
            count = row['count']
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {model:20s}: {count:3d} ({percentage:5.1f}%)")
        
        # Intent dağılımı
        print(f"\n{Fore.YELLOW}Intent Dağılımı:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT intent, COUNT(*) as count
            FROM feedback_events
            WHERE intent IS NOT NULL
            GROUP BY intent
            ORDER BY count DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            intent = row['intent']
            count = row['count']
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {intent:20s}: {count:3d} ({percentage:5.1f}%)")
        
        # Explicit ratings (varsa)
        cursor.execute("""
            SELECT COUNT(*) as total, AVG(explicit_rating) as avg_rating
            FROM feedback_events
            WHERE explicit_rating IS NOT NULL
        """)
        rating_row = cursor.fetchone()
        explicit_count = rating_row['total']
        avg_rating = rating_row['avg_rating']
        
        print(f"\n{Fore.YELLOW}Explicit Ratings:{Style.RESET_ALL}")
        if explicit_count > 0:
            print(f"  Toplam: {explicit_count}")
            print(f"  Ortalama: {avg_rating:.2f} / 5.0")
        else:
            print(f"  {Fore.YELLOW}Henüz explicit rating yok (👍/👎 butonları kullanılmamış){Style.RESET_ALL}")
        
        # Son 5 feedback
        print(f"\n{Fore.YELLOW}Son 5 Feedback:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT 
                query, 
                model_used, 
                implicit_signal, 
                complexity,
                timestamp
            FROM feedback_events
            ORDER BY id DESC
            LIMIT 5
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            query = row['query'][:50] + "..." if len(row['query']) > 50 else row['query']
            print(f"\n  {i}. {Fore.CYAN}{query}{Style.RESET_ALL}")
            print(f"     Model: {row['model_used']} | Signal: {row['implicit_signal']} | Complexity: {row['complexity']}")
            print(f"     Time: {row['timestamp']}")
    
    # ============================================
    # 2. LEARNING INSIGHTS
    # ============================================
    print_header("2. LEARNING INSIGHTS (Öğrenilen Bilgiler)")
    
    cursor.execute("SELECT COUNT(*) as total FROM learning_insights")
    insights_total = cursor.fetchone()['total']
    print(f"Toplam insights: {Fore.GREEN}{insights_total}{Style.RESET_ALL}")
    
    if insights_total == 0:
        print(f"{Fore.YELLOW}⚠️ Henüz hiç insight öğrenilmemiş{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 10+ feedback sonra sistem otomatik öğrenmeye başlayacak{Style.RESET_ALL}")
    else:
        # Kategorilere göre
        print(f"\n{Fore.YELLOW}Kategori Dağılımı:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM learning_insights
            GROUP BY category
        """)
        
        for row in cursor.fetchall():
            print(f"  {row['category']:30s}: {row['count']} insight")
        
        # En iyi model performansları
        print(f"\n{Fore.YELLOW}Model Performansları:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT key, value, confidence, sample_size
            FROM learning_insights
            WHERE category = 'model_performance'
            ORDER BY value DESC
        """)
        
        for row in cursor.fetchall():
            model = row['key']
            score = row['value']
            confidence = row['confidence']
            sample_size = row['sample_size']
            
            # Score'u yıldıza çevir
            stars = '⭐' * int(score * 5)
            
            print(f"  {model:20s}: {stars} ({score:.2f}) [confidence: {confidence:.2f}, n={sample_size}]")
        
        # Intent-Model eşleşmeleri (top 5)
        print(f"\n{Fore.YELLOW}En İyi Intent-Model Eşleşmeleri:{Style.RESET_ALL}")
        cursor.execute("""
            SELECT key, value, confidence, sample_size
            FROM learning_insights
            WHERE category = 'intent_model_match'
            ORDER BY value DESC
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            key_parts = row['key'].split(':')
            if len(key_parts) == 2:
                intent, model = key_parts
                score = row['value']
                confidence = row['confidence']
                sample_size = row['sample_size']
                
                print(f"  {intent:20s} + {model:15s} = {score:.2f} [n={sample_size}]")
    
    # ============================================
    # 3. İSTATİSTİKLER
    # ============================================
    print_header("3. GENEL İSTATİSTİKLER")
    
    # Toplam kullanıcı sayısı
    cursor.execute("SELECT COUNT(DISTINCT user_id) as users FROM feedback_events")
    users = cursor.fetchone()['users']
    print(f"Toplam kullanıcı: {users}")
    
    # Toplam session sayısı
    cursor.execute("SELECT COUNT(DISTINCT session_id) as sessions FROM feedback_events")
    sessions = cursor.fetchone()['sessions']
    print(f"Toplam session: {sessions}")
    
    # Ortalama response time
    cursor.execute("SELECT AVG(response_time_ms) as avg_time FROM feedback_events WHERE response_time_ms IS NOT NULL")
    avg_time = cursor.fetchone()['avg_time']
    if avg_time:
        print(f"Ortalama response time: {avg_time:.0f}ms ({avg_time/1000:.2f}s)")
    
    # Bugünkü aktivite
    cursor.execute("""
        SELECT COUNT(*) as today_count
        FROM feedback_events
        WHERE DATE(timestamp) = DATE('now')
    """)
    today = cursor.fetchone()['today_count']
    print(f"Bugünkü feedback: {today}")
    
    conn.close()
    
    # ============================================
    # 4. ÖNERİLER
    # ============================================
    print_header("4. ÖNERİLER")
    
    if total < 10:
        print(f"{Fore.YELLOW}📌 En az 10 feedback toplamak için daha fazla soru sorun{Style.RESET_ALL}")
    
    if explicit_count == 0:
        print(f"{Fore.YELLOW}📌 Frontend'e 👍/👎 butonları ekleyin (explicit feedback için){Style.RESET_ALL}")
    
    if insights_total == 0 and total >= 10:
        print(f"{Fore.YELLOW}📌 Manuel olarak insight update çalıştırın{Style.RESET_ALL}")
        print(f"   Python shell'de:")
        print(f"   >>> from services.adaptive_learning_system import _adaptive_learning")
        print(f"   >>> _adaptive_learning._update_insights()")
    
    if insights_total > 0:
        print(f"{Fore.GREEN}✅ Sistem öğreniyor! Model önerileri optimize ediliyor{Style.RESET_ALL}")


def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("=" * 60)
    print("  🔍 ADAPTIVE LEARNING - VERİTABANI KONTROLÜ")
    print("=" * 60)
    print(f"{Style.RESET_ALL}")
    
    check_database()
    
    print(f"\n{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Kontrol tamamlandı!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()