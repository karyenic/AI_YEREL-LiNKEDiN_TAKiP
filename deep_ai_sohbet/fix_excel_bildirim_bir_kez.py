# -*- coding: utf-8 -*-
"""
fix_excel_bildirim_bir_kez.py — v11
excelBildirimGoster() DOMContentLoaded'da her sayfa yuklemesinde calisiyordu.
sessionStorage ile "sekme basina 1 kez" mantigina cevirir.

Sayfa degistir  -> bildirim YOK
Yenile         -> bildirim YOK
Sekme kapat-ac -> 1 kez gosterir
Yeni sekme     -> 1 kez gosterir
"""
import sys, shutil
from pathlib import Path
from datetime import datetime

PROJE = Path(__file__).resolve().parent.parent
APP_JS = PROJE / "static" / "app.js"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

ESKI = """    excelBildirimGoster();
    linkedinUrlIzle();"""

YENI = """    // v11: Excel bildirimi sadece tarayici acilisinda 1 kez.
    // Sayfa degisince veya yenilendiginde tekrar gosterilmez.
    if (!sessionStorage.getItem("excel_bildirim_gosterildi")) {
      excelBildirimGoster();
      sessionStorage.setItem("excel_bildirim_gosterildi", "1");
    }
    linkedinUrlIzle();"""


def yedek_al(dosya):
    y = dosya.with_suffix(dosya.suffix + f".bak_excelbirkez_{TS}")
    shutil.copy2(dosya, y)
    return y


def geri_yukle(dosya, yedek):
    shutil.copy2(yedek, dosya)
    print(f"  [XX] Geri yuklendi: {dosya.name}")


def main():
    print("=" * 62)
    print(f"  fix_excel_bildirim_bir_kez.py — {TS}")
    print("=" * 62)

    if not APP_JS.exists():
        print(f"[XX] Bulunamadi: {APP_JS}")
        sys.exit(1)

    icerik = APP_JS.read_text(encoding="utf-8")

    # Idempotent kontrol
    if "excel_bildirim_gosterildi" in icerik:
        print("\n[OK] Zaten uygulanmis, atlaniyor.")
        sys.exit(0)

    adet = icerik.count(ESKI)
    if adet == 0:
        print("\n[XX] Hedef blok bulunamadi.")
        print("     Beklenen:")
        print(repr(ESKI))
        sys.exit(1)
    if adet > 1:
        print(f"\n[XX] Hedef blok {adet} kez gecmis - DUR.")
        sys.exit(1)

    yedek = yedek_al(APP_JS)
    print(f"\n[OK] Yedek: {yedek.name}")

    yeni = icerik.replace(ESKI, YENI, 1)
    APP_JS.write_text(yeni, encoding="utf-8")
    print("[OK] excelBildirimGoster() sessionStorage kontrolune alindi")

    # Dogrulama
    kontrol = APP_JS.read_text(encoding="utf-8")
    if "excel_bildirim_gosterildi" in kontrol and YENI in kontrol:
        print("[OK] Dogrulama gecti")
    else:
        print("[XX] Dogrulama basarisiz, geri yukleniyor")
        geri_yukle(APP_JS, yedek)
        sys.exit(1)

    print()
    print("=" * 62)
    print("  [OK] TAMAM")
    print("=" * 62)
    print(f"  Yedek: {yedek.name}")
    print()
    print("  SONRAKI ADIM:")
    print("  1. Baslat.bat -> Flask restart")
    print("  2. Tarayici   -> Ctrl+Shift+R")
    print("  3. TEST:")
    print("     a) Sayfa yenile  -> bildirim CIKMAMALI")
    print("     b) /metrics git  -> bildirim CIKMAMALI")
    print("     c) Sekmeyi kapatip yeniden ac -> 1 kez CIKMALI")
    print()


if __name__ == "__main__":
    main()