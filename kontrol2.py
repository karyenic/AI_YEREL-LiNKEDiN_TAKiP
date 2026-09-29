import core.excel_io as e

# Modüldeki tüm fonksiyonları listele
fonksiyonlar = [name for name in dir(e) if callable(getattr(e, name)) and not name.startswith("_")]
print("Mevcut fonksiyonlar:")
for f in fonksiyonlar:
    print(f"  - {f}")