"""
test_quick.py
=============
5 DAKİKADA SONUÇ VEREN HIZLI TEST
"""

import asyncio
import time
from services.ultimate_chat_engine import UltimateChatEngine, ChatMode

# ============================================
# TEST SORULARI
# ============================================

TEST_CASES = [
    {
        "message": "Merhaba, nasılsın?",
        "mode": ChatMode.FRIEND,
        "expected_intent": "greeting",
        "max_time": 5.0,
        "min_quality": 0.7
    },
    {
        "message": "Python'da liste nasıl oluşturulur?",
        "mode": ChatMode.CODE,
        "expected_intent": "code",
        "max_time": 6.0,
        "min_quality": 0.7
    },
    {
        "message": "Machine learning nedir? Açıklar mısın?",
        "mode": ChatMode.NORMAL,
        "expected_intent": "explain",
        "max_time": 7.0,
        "min_quality": 0.7
    },
    {
        "message": "Python ile JavaScript arasındaki fark nedir?",
        "mode": ChatMode.NORMAL,
        "expected_intent": "compare",
        "max_time": 7.0,
        "min_quality": 0.7
    },
    {
        "message": "Bana bir hikaye anlat",
        "mode": ChatMode.CREATIVE,
        "expected_intent": "question",
        "max_time": 8.0,
        "min_quality": 0.6
    }
]

# ============================================
# TEST RUNNER
# ============================================

async def run_tests():
    """Tüm testleri çalıştır"""
    
    print("=" * 70)
    print("🧪 HIZLI TEST BAŞLIYOR")
    print("=" * 70)
    
    engine = UltimateChatEngine()
    
    results = {
        "passed": 0,
        "failed": 0,
        "total_time": 0.0
    }
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(TEST_CASES)}: {test['message'][:50]}...")
        print(f"{'='*70}")
        
        try:
            # Test çalıştır
            response = await engine.chat(
                message=test["message"],
                user_id="test_user",
                session_id="test_session",
                mode=test["mode"]
            )
            
            # Sonuçları göster
            print(f"✅ Model: {response.model}")
            print(f"✅ Süre: {response.time:.2f}s")
            print(f"✅ Kalite: {response.quality_score:.2f}")
            print(f"✅ Intent: {response.intent}")
            
            # Validasyon
            checks = {
                "time": response.time <= test["max_time"],
                "quality": response.quality_score >= test["min_quality"],
                "intent": response.intent == test["expected_intent"],
                "turkish": any(c in response.content for c in "çğıöşüÇĞİÖŞÜ"),
                "no_ai_cliche": "size nasıl yardımcı" not in response.content.lower(),
                "no_meta_tags": "[USER]" not in response.content and "[ASSISTANT]" not in response.content
            }
            
            # Başarı kontrolü
            passed = sum(checks.values())
            total_checks = len(checks)
            
            print(f"\n📊 CHECKS ({passed}/{total_checks}):")
            for check, status in checks.items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {check}")
            
            print(f"\n💬 CEVAP (ilk 200 karakter):")
            print(f"  {response.content[:200]}...")
            
            # Sonuç
            if passed >= total_checks - 1:  # 1 hata tolere et
                print(f"\n✅ TEST BAŞARILI")
                results["passed"] += 1
            else:
                print(f"\n❌ TEST BAŞARISIZ")
                results["failed"] += 1
            
            results["total_time"] += response.time
        
        except Exception as e:
            print(f"\n❌ TEST HATASI: {str(e)}")
            results["failed"] += 1
        
        # Kısa ara (Ollama'ya nefes aldır)
        await asyncio.sleep(1)
    
    # FINAL RAPOR
    print("\n" + "=" * 70)
    print("📊 FINAL RAPOR")
    print("=" * 70)
    print(f"✅ Başarılı: {results['passed']}/{len(TEST_CASES)}")
    print(f"❌ Başarısız: {results['failed']}/{len(TEST_CASES)}")
    print(f"⏱️  Toplam Süre: {results['total_time']:.2f}s")
    print(f"⏱️  Ortalama Süre: {results['total_time']/len(TEST_CASES):.2f}s")
    
    success_rate = (results['passed'] / len(TEST_CASES)) * 100
    print(f"\n🎯 BAŞARI ORANI: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 MÜKEMMEL! SİSTEM HAZIR!")
    elif success_rate >= 60:
        print("\n👍 İYİ! Küçük iyileştirmeler yapılabilir.")
    else:
        print("\n⚠️  DİKKAT! Ciddi sorunlar var.")
    
    await engine.close()

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("\n🚀 Test başlatılıyor...")
    print("⚠️  Ollama'nın çalıştığından emin olun!")
    print()
    
    asyncio.run(run_tests())