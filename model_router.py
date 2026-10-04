import os
import shutil
import re
import traceback

dizin = r"C:\AI_YEREL\LiNKEDiN_TAKiP"
rapor = ["\n" + "="*50, "📋 MODEL ROUTER SİSTEMİ GÜVENLİ ENTEGRASYONU", "="*50]

def yedekle_ve_oku(dosya_yolu, ek_ad):
    yedek_yolu = dosya_yolu.replace(".", f"_backup_{ek_ad}.")
    if not os.path.exists(yedek_yolu):
        shutil.copy2(dosya_yolu, yedek_yolu)
        rapor.append(f"📦 Emniyet yedeği alındı: {os.path.basename(yedek_yolu)}")
    else:
        rapor.append(f"ℹ️ Yedek zaten mevcut: {os.path.basename(yedek_yolu)}")
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return f.read()

# ==========================================
# 1. OLLAMA_CLIENT.PY GÜNCELLEMESİ
# ==========================================
def router_guncelle():
    py_yolu = os.path.join(dizin, "core", "ollama_client.py")
    if not os.path.exists(py_yolu):
        py_yolu = os.path.join(dizin, "ollama_client.py")

    if not os.path.exists(py_yolu):
        rapor.append("❌ HATA: ollama_client.py bulunamadı.")
        return False

    icerik = yedekle_ve_oku(py_yolu, "router_sys")

    eski_router = r"def _model_sec\(soru\):\s*\"\"\"Router: Soru tipine gore model secer\.\"\"\"[\s\S]*?return MODEL_ROUTER\[\"normal\"\]"
    
    yeni_router = """def _model_sec(soru):
    \"\"\"Router: Soru tipine gore en uygun yerel modeli secer.\"\"\"
    if not soru:
        return DEFAULT_MODEL
    
    soru_lower = soru.lower()
    
    # Kodlama ve yazılım geliştirme soruları için Coder modeli
    if any(k in soru_lower for k in ["kod", "python", "flask", "js", "sql", "fonksiyon", "hata", "script", "bug", "kodla"]):
        return "qwen2.5-coder:14b"
        
    # Haftalık plan, derin analiz ve stratejik raporlar için 64k DeepSeek modeli
    if any(k in soru_lower for k in ["haftalık", "plan", "analiz", "rapor", "program", "detaylı", "strateji"]):
        return "deepseek-r1-64k"
        
    return DEFAULT_MODEL"""

    yeni_icerik = re.sub(eski_router, yeni_router, icerik)

    if yeni_icerik != icerik:
        with open(py_yolu, "w", encoding="utf-8") as f:
            f.write(yeni_icerik)
        rapor.append("✅ BAŞARILI: ollama_client.py Akıllı Router güncellendi.")
        return True
    else:
        rapor.append("⚠️ UYARI: ollama_client.py içinde _model_sec bulunamadı (zaten güncel olabilir).")
        return False

# ==========================================
# 2. CHAT.PY GÜNCELLEMESİ (Otomatik/Manuel Ayrımı)
# ==========================================
def chat_router_guncelle():
    chat_yolu = os.path.join(dizin, "routes", "chat.py")
    if not os.path.exists(chat_yolu):
        chat_yolu = os.path.join(dizin, "chat.py")

    if not os.path.exists(chat_yolu):
        rapor.append("❌ HATA: chat.py bulunamadı.")
        return False

    icerik = yedekle_ve_oku(chat_yolu, "router_chat")

    eski_secim = r"model_secili = model if model else DEFAULT_MODEL"
    yeni_secim = """# Hibrit Model Router Desteği: 'otomatik' seçildiyse akıllı router devreye girer
    if model == "otomatik" or not model:
        model_secili = _model_sec(kullanici_mesaji)
    else:
        model_secili = model"""

    yeni_icerik = icerik.replace(eski_secim, yeni_secim)

    if yeni_icerik != icerik:
        with open(chat_yolu, "w", encoding="utf-8") as f:
            f.write(yeni_icerik)
        rapor.append("✅ BAŞARILI: chat.py dosyasına Otomatik Router mantığı eklendi.")
        return True
    else:
        rapor.append("⚠️ UYARI: chat.py içinde model seçim satırı eşleşmedi.")
        return False

if __name__ == "__main__":
    try:
        print("Güvenli Model Router entegrasyonu başlatılıyor...\n")
        r1 = router_guncelle()
        r2 = chat_router_guncelle()
        
        rapor.append("="*50)
        if r1 or r2:
            rapor.append("📌 SONUÇ: Router başarıyla kuruldu ve yedekler alındı!")
            rapor.append("📌 Tarayıcınızda CTRL+F5 yapmayı unutmayın.")
        else:
            rapor.append("📌 SONUÇ: Hiçbir dosya değiştirilemedi.")
            
        for satir in rapor:
            print(satir)
            
    except Exception as e:
        print("\n❌ BEKLENMEYEN BİR HATA OLUŞTU:")
        print(traceback.format_exc())
    finally:
        input("\nÇıkmak için ENTER'a basın...")