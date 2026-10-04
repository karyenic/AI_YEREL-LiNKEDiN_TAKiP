import os
import shutil
import re
import traceback

dizin = r"C:\AI_YEREL\LiNKEDiN_TAKiP"
rapor = ["\n" + "="*50, "📋 HİBRİT MODEL VE AKILLI ROUTER GÜNCELLEMESİ", "="*50]

def yedekle_ve_oku(dosya_yolu, ek_ad):
    yedek_yolu = dosya_yolu.replace(".", f"_backup_{ek_ad}.")
    if not os.path.exists(yedek_yolu):
        shutil.copy2(dosya_yolu, yedek_yolu)
        rapor.append(f"📦 Yedek alındı: {os.path.basename(yedek_yolu)}")
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return f.read()

# ==========================================
# 1. APP.JS GÜNCELLEMESİ (Arayüz Model Listesi)
# ==========================================
def js_guncelle():
    js_yolu = os.path.join(dizin, "static", "app.js")
    if not os.path.exists(js_yolu):
        js_yolu = os.path.join(dizin, "app.js")

    if not os.path.exists(js_yolu):
        rapor.append("❌ HATA: app.js bulunamadı.")
        return False

    icerik = yedekle_ve_oku(js_yolu, "model")

    # modelleriYukle fonksiyonunu güncelliyoruz
    eski_fonk = r"async function modelleriYukle\(\)\s*\{[\s\S]*?}"
    
    yeni_fonk = """async function modelleriYukle() {
  const sel = document.getElementById("model-select");
  if (!sel) return;

  sel.innerHTML = "";

  // Otomatik Akıllı Seçim en üstte yer alır
  const otomatikOpt = document.createElement("option");
  otomatikOpt.value = "otomatik";
  otomatikOpt.textContent = "🤖 Otomatik (Akıllı Seçim)";
  sel.appendChild(otomatikOpt);

  const modeller = [
    "deepseek-r1-64k",
    "qwen2.5-coder:14b",
    "deepseek-r1:7b",
    "qwen2.5:7b",
    "llama3.1:latest",
    "ministral-3:14b"
  ];

  for (const m of modeller) {
    const o = document.createElement("option");
    o.value = m;
    o.textContent = m;
    sel.appendChild(o);
  }
}"""

    yeni_icerik = re.sub(eski_fonk, yeni_fonk, icerik)

    if yeni_icerik != icerik:
        with open(js_yolu, "w", encoding="utf-8") as f:
            f.write(yeni_icerik)
        rapor.append("✅ BAŞARILI: app.js model listesi akıllı seçim ve yeni modellerle güncellendi.")
        return True
    else:
        rapor.append("⚠️ UYARI: app.js içinde modelleriYukle fonksiyonu bulunamadı.")
        return False

# ==========================================
# 2. OLLAMA_CLIENT.PY GÜNCELLEMESİ (Akıllı Router)
# ==========================================
def python_router_guncelle():
    py_yolu = os.path.join(dizin, "core", "ollama_client.py")
    if not os.path.exists(py_yolu):
        py_yolu = os.path.join(dizin, "ollama_client.py")

    if not os.path.exists(py_yolu):
        rapor.append("❌ HATA: ollama_client.py bulunamadı.")
        return False

    icerik = yedekle_ve_oku(py_yolu, "router")

    # _model_sec fonksiyonunu güncelliyoruz
    eski_router = r"def _model_sec\(soru\):\s*\"\"\"Router: Soru tipine gore model secer\.\"\"\"[\s\S]*?return MODEL_ROUTER\[\"normal\"\]"
    
    yeni_router = """def _model_sec(soru):
    \"\"\"Router: Soru tipine gore en uygun yerel modeli secer.\"\"\"
    if not soru:
        return "qwen2.5:7b"
    
    soru_lower = soru.lower()
    
    # Kodlama, Python, Flask, JS, SQL gibi teknik sorularda Coder modeli devreye girer
    if any(k in soru_lower for k in ["kod", "python", "flask", "js", "sql", "fonksiyon", "hata", "script", "bug"]):
        return "qwen2.5-coder:14b"
        
    # Haftalık plan, derin analiz, rapor veya uzun bağlam gerektiren durumlarda 64k DeepSeek devreye girer
    if any(k in soru_lower for k in ["haftalık", "plan", "analiz", "rapor", "program", "detaylı"]):
        return "deepseek-r1-64k"
        
    return "qwen2.5:7b" """

    yeni_icerik = re.sub(eski_router, yeni_router, icerik)

    if yeni_icerik != icerik:
        with open(py_yolu, "w", encoding="utf-8") as f:
            f.write(yeni_icerik)
        rapor.append("✅ BAŞARILI: ollama_client.py Akıllı Router mekanizması güncellendi.")
        return True
    else:
        rapor.append("⚠️ UYARI: ollama_client.py içinde _model_sec fonksiyonu bulunamadı.")
        return False

if __name__ == "__main__":
    try:
        print("Hibrit model entegrasyonu başlatılıyor...\n")
        js_ok = js_guncelle()
        py_ok = python_router_guncelle()
        
        rapor.append("="*50)
        if js_ok or py_ok:
            rapor.append("📌 SONUÇ: Entegrasyon tamamlandı! Tarayıcınızda CTRL+F5 yapmayı unutmayın.")
        else:
            rapor.append("📌 SONUÇ: Hiçbir dosya güncellenemedi, yolları kontrol edin.")
            
        for satir in rapor:
            print(satir)
            
    except Exception as e:
        print("\n❌ BEKLENMEYEN BİR HATA OLUŞTU:")
        print(traceback.format_exc())
    finally:
        input("\nÇıkmak için ENTER'a basın...")