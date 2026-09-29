"""UNIQUE constraint'i kaldirmak icin tabloyu yeniden olusturur."""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.excel_io import _satir_hash

DB = "data/linkedin_takip.db"
c = sqlite3.connect(DB)

# 1. Mevcut tablonun şemasını gör
print("Eski şema:")
print(c.execute("SELECT sql FROM sqlite_master WHERE name='adaylar'").fetchone()[0])
print()

# 2. Yeni tablo oluştur (kaynak_hash UNIQUE OLMADAN)
c.executescript("""
    BEGIN TRANSACTION;

    CREATE TABLE adaylar_yeni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isim TEXT, tarih TEXT, aciklama TEXT,
        davet INTEGER, randevu INTEGER, plan INTEGER,
        kayit INTEGER, takip INTEGER, hayir INTEGER,
        is_ariyor INTEGER,
        kaynak_hash TEXT
    );

    INSERT INTO adaylar_yeni (id, isim, tarih, aciklama,
                              davet, randevu, plan, kayit, takip, hayir,
                              is_ariyor, kaynak_hash)
    SELECT id, isim, tarih, aciklama,
           davet, randevu, plan, kayit, takip, hayir,
           is_ariyor, kaynak_hash
    FROM adaylar;

    DROP TABLE adaylar;
    ALTER TABLE adaylar_yeni RENAME TO adaylar;

    COMMIT;
""")

print("Yeni tablo olusturuldu (UNIQUE constraint YOK).")
print()

# 3. Şimdi hash'leri yeniden hesapla
rows = c.execute("SELECT id, isim, tarih, aciklama FROM adaylar").fetchall()
print(f"Toplam: {len(rows)}")
for r in rows:
    yeni = _satir_hash(r[1], r[2], r[3])
    c.execute("UPDATE adaylar SET kaynak_hash = ? WHERE id = ?", (yeni, r[0]))
c.commit()
print("Hash'ler guncellendi.")

# 4. Duplicate'leri sil
before = c.execute("SELECT COUNT(*) FROM adaylar").fetchone()[0]
c.execute("""
    DELETE FROM adaylar
    WHERE id NOT IN (SELECT MIN(id) FROM adaylar GROUP BY kaynak_hash)
""")
c.commit()
after = c.execute("SELECT COUNT(*) FROM adaylar").fetchone()[0]
print(f"Silinen: {before - after}, Kalan: {after}")

# 5. UNIQUE INDEX kur (artik sütunda değil, index olarak)
c.execute("CREATE UNIQUE INDEX idx_kaynak_hash ON adaylar(kaynak_hash)")
c.commit()
print("UNIQUE INDEX kuruldu (sütunda değil, index olarak).")

# 6. Kontrol
toplam = c.execute("SELECT COUNT(*) FROM adaylar").fetchone()[0]
tekil = c.execute("SELECT COUNT(DISTINCT kaynak_hash) FROM adaylar").fetchone()[0]
print()
print("═" * 50)
print(f"Toplam:     {toplam}")
print(f"Tekil hash: {tekil}")
print(f"Duplicate:  {toplam - tekil}")
print("═" * 50)

# 7. Nesli Diril
print()
print("Nesli Diril:")
for r in c.execute("SELECT id, isim, kaynak_hash FROM adaylar WHERE isim LIKE '%Nesli%'"):
    print(f"  ID={r[0]} hash={r[2]}")

c.close()