"""1) Yeni hash fonksiyonuyla hash'leri günceller
   2) Aynı hash'ten birden fazla varsa, en eskisini tutar, diğerlerini siler
   3) UNIQUE index'i yeniden kurar"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.excel_io import _satir_hash

DB = "data/linkedin_takip.db"
c = sqlite3.connect(DB)

# 1. UNIQUE index varsa kaldır (güncelleme sırasında çakışma olmasın)
c.execute("DROP INDEX IF EXISTS idx_kaynak_hash")
c.commit()

# 2. Tüm kayıtların hash'ini yeniden hesapla
rows = c.execute("SELECT id, isim, tarih, aciklama FROM adaylar").fetchall()
print(f"Toplam kayıt: {len(rows)}")

for r in rows:
    yeni_hash = _satir_hash(r[1], r[2], r[3])
    c.execute("UPDATE adaylar SET kaynak_hash = ? WHERE id = ?", (yeni_hash, r[0]))

c.commit()
print(f"Hash'ler güncellendi: {len(rows)}")

# 3. Duplicate'leri sil (aynı hash'ten en eski ID'yi tut)
before = c.execute("SELECT COUNT(*) FROM adaylar").fetchone()[0]
c.execute("""
    DELETE FROM adaylar
    WHERE id NOT IN (
        SELECT MIN(id) FROM adaylar GROUP BY kaynak_hash
    )
""")
c.commit()
after = c.execute("SELECT COUNT(*) FROM adaylar").fetchone()[0]
print(f"Silinen: {before - after}")
print(f"Kalan:   {after}")

# 4. UNIQUE index'i yeniden kur
c.execute("CREATE UNIQUE INDEX idx_kaynak_hash ON adaylar(kaynak_hash)")
c.commit()
print("UNIQUE index yeniden kuruldu ✅")

# 5. Kontrol
tekil = c.execute("SELECT COUNT(DISTINCT kaynak_hash) FROM adaylar").fetchone()[0]
print()
print("═" * 50)
print(f"Toplam:      {after}")
print(f"Tekil hash:  {tekil}")
print(f"Duplicate:   {after - tekil}")
print("═" * 50)

# 6. Nesli Diril kontrolü
print()
print("Nesli Diril:")
rows = c.execute("SELECT id, isim, kaynak_hash FROM adaylar WHERE isim LIKE '%Nesli%'").fetchall()
for r in rows:
    print(f"  ID={r[0]}  hash={r[2]}")

c.close()