import sqlite3
from datetime import datetime
from config import ADAY_DB, CHAT_DB


def _conn(db_path):
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_all():
    # Adaylar tablosu
    with _conn(ADAY_DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS adaylar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT, tarih TEXT, aciklama TEXT,
            davet INTEGER, randevu INTEGER, plan INTEGER,
            kayit INTEGER, takip INTEGER, hayir INTEGER,
            is_ariyor INTEGER,
            kaynak_hash TEXT UNIQUE
        )''')
        c.commit()
    # Chat geçmişi
    with _conn(CHAT_DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS sohbet_loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT, icerik TEXT, zaman TEXT,
            model TEXT, fallback INTEGER DEFAULT 0
        )''')
        # Eski veritabanlarında bu kolonlar yoksa ekle (migration)
        mevcut = {r["name"] for r in c.execute("PRAGMA table_info(sohbet_loglari)").fetchall()}
        if "model" not in mevcut:
            c.execute("ALTER TABLE sohbet_loglari ADD COLUMN model TEXT")
        if "fallback" not in mevcut:
            c.execute("ALTER TABLE sohbet_loglari ADD COLUMN fallback INTEGER DEFAULT 0")
        c.commit()


# ─── Aday İşlemleri ────────────────────────────────────
def adaylari_getir():
    with _conn(ADAY_DB) as c:
        rows = c.execute("SELECT * FROM adaylar ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def aday_ekle(isim, tarih, aciklama, davet, randevu, plan, kayit, takip, hayir, is_ariyor, kaynak_hash=None):
    try:
        with _conn(ADAY_DB) as c:
            c.execute('''INSERT INTO adaylar
                (isim, tarih, aciklama, davet, randevu, plan, kayit, takip, hayir, is_ariyor, kaynak_hash)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (isim, tarih, aciklama, int(davet), int(randevu), int(plan),
                 int(kayit), int(takip), int(hayir), int(is_ariyor), kaynak_hash))
            c.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # duplicate (aynı hash)
    except Exception as e:
        print(f"Aday ekleme hatası: {e}")
        return False


def aday_sil(aday_id):
    with _conn(ADAY_DB) as c:
        c.execute("DELETE FROM adaylar WHERE id=?", (aday_id,))
        c.commit()


def tum_adaylari_sil():
    with _conn(ADAY_DB) as c:
        c.execute("DELETE FROM adaylar")
        c.commit()


# ─── Chat İşlemleri ────────────────────────────────────
def chat_mesajlari_getir():
    with _conn(CHAT_DB) as c:
        rows = c.execute(
            "SELECT rol, icerik, zaman, model, fallback FROM sohbet_loglari ORDER BY id ASC"
        ).fetchall()
    return [{"role": r["rol"], "content": r["icerik"], "zaman": r["zaman"],
             "model": r["model"], "fallback": bool(r["fallback"])} for r in rows]


def chat_mesaj_ekle(rol, icerik, model=None, fallback=False):
    with _conn(CHAT_DB) as c:
        c.execute(
            "INSERT INTO sohbet_loglari (rol, icerik, zaman, model, fallback) VALUES (?,?,?,?,?)",
            (rol, icerik, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), model, int(bool(fallback)))
        )
        c.commit()


def chat_temizle():
    with _conn(CHAT_DB) as c:
        c.execute("DELETE FROM sohbet_loglari")
        c.commit()