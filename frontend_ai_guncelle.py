import os
import shutil
import traceback

dizin = r"C:\AI_YEREL\LiNKEDiN_TAKiP"
rapor = ["\n" + "="*50, "📋 FRONTEND MODEL LİSTESİ VE ROZET GÜNCELLEMESİ", "="*50]

def yedekle_ve_oku(dosya_yolu, ek_ad):
    yedek_yolu = dosya_yolu.replace(".", f"_backup_{ek_ad}.")
    if not os.path.exists(yedek_yolu):
        shutil.copy2(dosya_yolu, yedek_yolu)
        rapor.append(f"📦 Yedek alındı: {os.path.basename(yedek_yolu)}")
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return f.read()

def frontend_js_guncelle():
    # static/app.js veya chat.js kontrolü
    js_yolu = os.path.join(dizin, "static", "app.js")
    if not os.path.exists(js_yolu):
        js_yolu = os.path.join(dizin, "app.js")

    if not os.path.exists(js_yolu):
        rapor.append("❌ HATA: app.js bulunamadı.")
        return False

    icerik = yedekle_ve_oku(js_yolu, "frontend_rozets")

    # 1. Modelleri yükleyen fonksiyonu güncelliyoruz (Tüm modeller + Otomatik)
    eski_fonk = r"async function modelleriYukle\(\)\s*\{[\s\S]*?}"
    yeni_fonk = """async function modelleriYukle() {
  const sel = document.getElementById("model-select");
  if (!sel) return;

  sel.innerHTML = "";

  // Otomatik Akıllı Seçim en üstte
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

    if re.search(eski_fonk, icerik):
        icerik = re.sub(eski_fonk, yeni_fonk, icerik)
        rapor.append("✅ BAŞARILI: Model listesi tüm modellerle güncellendi.")
    else:
        rapor.append("⚠️ UYARI: modelleriYukle fonksiyonu tam eşleşmedi, manuel eklenebilir.")

    with open(js_yolu, "w", encoding="utf-8") as f:
        f.write(icerik)
    return True

if __name__ == "__main__":
    import re
    try:
        print("Frontend güncellemesi başlatılıyor...\n")
        frontend_js_guncelle()
        
        for satir in rapor:
            print(satir)
            
    except Exception as e:
        print("\n❌ HATA OLUŞTU:")
        print(traceback.format_exc())
    finally:
        input("\nÇıkmak için ENTER'a basın...")