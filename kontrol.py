import sqlite3

c = sqlite3.connect("data/linkedin_takip.db")

rows = c.execute("SELECT id, isim, aciklama, kaynak_hash FROM adaylar WHERE isim LIKE '%Nesli%'").fetchall()

for r in rows:
    print(f"ID={r[0]}")
    print(f"  isim     = {r[1]!r}  →  unicode: {[hex(ord(ch)) for ch in r[1]]}")
    print(f"  aciklama = {r[2]!r}")
    print(f"  hash     = {r[3]}")
    print()

c.close()