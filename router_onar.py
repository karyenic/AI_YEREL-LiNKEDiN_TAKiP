import os
import traceback

dizin = r"C:\AI_YEREL\LiNKEDiN_TAKiP"

def hata_duzelt():
    chat_yolu = os.path.join(dizin, "routes", "chat.py")
    if not os.path.exists(chat_yolu):
        chat_yolu = os.path.join(dizin, "chat.py")

    if not os.path.exists(chat_yolu):
        print("❌ HATA: chat.py bulunamadı.")
        return

    with open(chat_yolu, "r", encoding="utf-8") as f:
        icerik = f.read()

    # Hatalı bloğu doğru girintili (indentation) haliyle değiştiriyoruz
    hatali_blok = """            # Hibrit Model Router Desteği: 'otomatik' seçildiyse akıllı router devreye girer
    if model == "otomatik" or not model:
        model_secili = _model_sec(kullanici_mesaji)
    else:
        model_secili = model"""

    dogru_blok = """            # Hibrit Model Router Desteği: 'otomatik' seçildiyse akıllı router devreye girer
            if model == "otomatik" or not model:
                model_secili = _model_sec(kullanici_mesaji)
            else:
                model_secili = model"""

    if hatali_blok in icerik:
        yeni_icerik = icerik.replace(hatali_blok, dogru_blok)
    else:
        # Eğer tam eşleşmezse eski satırı bulup doğrudan düzeltelim
        eski_aranan = "model_secili = model if model else DEFAULT_MODEL"
        dogru_degisim = """# Hibrit Model Router Desteği: 'otomatik' seçildiyse akıllı router devreye girer
            if model == "otomatik" or not model:
                model_secili = _model_sec(kullanici_mesaji)
            else:
                model_secili = model"""
        yeni_icerik = icerik.replace(eski_aranan, dogru_degisim)

    with open(chat_yolu, "w", encoding="utf-8") as f:
        f.write(yeni_icerik)
    
    print("✅ BAŞARILI: chat.py dosyasındaki girinti hatası düzeltildi!")

if __name__ == "__main__":
    try:
        print("Onarım başlatılıyor...\n")
        hata_duzelt()
    except Exception as e:
        print("\n❌ HATA OLUŞTU:")
        print(traceback.format_exc())
    finally:
        input("\nÇıkmak için ENTER'a basın...")