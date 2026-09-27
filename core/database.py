import sqlite3
from datetime import datetime
from config import ADAY_DB, CHAT_DB


def _conn(db_path):
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _kolon_ekle(conn, tablo, kolon, tip):
    mevcut = {
        r["name"]
        for r in conn.execute(f"PRAGMA table_info({tablo})").fetchall()
    }
    if kolon not in mevcut:
        conn.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tip}")
        return True
    return False


def init_all():
    # --------------------------------------------------------
    # Eski aday tablosu - mevcut Excel/AI sistemi korunuyor.
    # --------------------------------------------------------
    with _conn(ADAY_DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS adaylar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT,
            tarih TEXT,
            aciklama TEXT,
            davet INTEGER,
            randevu INTEGER,
            plan INTEGER,
            kayit INTEGER,
            takip INTEGER,
            hayir INTEGER,
            is_ariyor INTEGER,
            kaynak_hash TEXT UNIQUE
        )''')

        # ----------------------------------------------------
        # Yeni aday profili
        # ----------------------------------------------------
        c.execute('''
            CREATE TABLE IF NOT EXISTS aday_profil (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL,
                telefon TEXT DEFAULT '',
                email TEXT DEFAULT '',
                adres TEXT DEFAULT '',
                aktif INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # ----------------------------------------------------
        # Yeni aday olay/gecmis tablosu
        # ----------------------------------------------------
        c.execute('''
            CREATE TABLE IF NOT EXISTS aday_olaylari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aday_id INTEGER NOT NULL,
                tarih TEXT,
                olay_tipi TEXT,
                olay_metni TEXT,
                kaynak TEXT,
                kaynak_kayit_id INTEGER,
                davet INTEGER DEFAULT 0,
                randevu INTEGER DEFAULT 0,
                plan INTEGER DEFAULT 0,
                kayit INTEGER DEFAULT 0,
                takip INTEGER DEFAULT 0,
                hayir INTEGER DEFAULT 0,
                is_ariyor INTEGER DEFAULT 0,
                durum TEXT DEFAULT '',
                created_at TEXT
            )
        ''')

        # Önceden migration yapılmış sistemlerde durum kolonu yoksa ekle.
        _kolon_ekle(c, "aday_olaylari", "durum", "TEXT DEFAULT ''")

        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_aday_profil_isim
            ON aday_profil(isim)
        ''')

        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_aday_olaylari_aday
            ON aday_olaylari(aday_id)
        ''')

        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_aday_olaylari_tarih
            ON aday_olaylari(tarih)
        ''')

        # ----------------------------------------------------
        # Migration kontrolü:
        # Eski adaylar için profil + eski Excel geçmişi oluştur.
        # Daha önce yapılmış migration tekrar kayıt üretmez.
        # ----------------------------------------------------
        eski_adaylar = c.execute(
            "SELECT * FROM adaylar ORDER BY id ASC"
        ).fetchall()

        for eski in eski_adaylar:
            isim = (eski["isim"] or "").strip()
            if not isim:
                continue

            profil = c.execute(
                '''
                SELECT id
                FROM aday_profil
                WHERE lower(trim(isim)) = lower(trim(?))
                ORDER BY id ASC
                LIMIT 1
                ''',
                (isim,)
            ).fetchone()

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if profil is None:
                cur = c.execute(
                    '''
                    INSERT INTO aday_profil
                    (isim, telefon, email, adres, aktif, created_at, updated_at)
                    VALUES (?, '', '', '', 1, ?, ?)
                    ''',
                    (isim, now, now)
                )
                profil_id = cur.lastrowid
            else:
                profil_id = profil["id"]

            mevcut_olay = c.execute(
                '''
                SELECT id
                FROM aday_olaylari
                WHERE kaynak = 'excel_migrasyon'
                  AND kaynak_kayit_id = ?
                LIMIT 1
                ''',
                (eski["id"],)
            ).fetchone()

            if mevcut_olay is None:
                c.execute(
                    '''
                    INSERT INTO aday_olaylari
                    (
                        aday_id,
                        tarih,
                        olay_tipi,
                        olay_metni,
                        kaynak,
                        kaynak_kayit_id,
                        davet,
                        randevu,
                        plan,
                        kayit,
                        takip,
                        hayir,
                        is_ariyor,
                        durum,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        profil_id,
                        eski["tarih"] or "",
                        "Excel Geçmişi",
                        eski["aciklama"] or "",
                        "excel_migrasyon",
                        eski["id"],
                        int(eski["davet"] or 0),
                        int(eski["randevu"] or 0),
                        int(eski["plan"] or 0),
                        int(eski["kayit"] or 0),
                        int(eski["takip"] or 0),
                        int(eski["hayir"] or 0),
                        int(eski["is_ariyor"] or 0),
                        "",
                        now
                    )
                )

        c.commit()

    # --------------------------------------------------------
    # Chat geçmişi
    # --------------------------------------------------------
    with _conn(CHAT_DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS sohbet_loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT,
            icerik TEXT,
            zaman TEXT,
            model TEXT,
            fallback INTEGER DEFAULT 0
        )''')

        mevcut = {
            r["name"]
            for r in c.execute(
                "PRAGMA table_info(sohbet_loglari)"
            ).fetchall()
        }

        if "model" not in mevcut:
            c.execute(
                "ALTER TABLE sohbet_loglari ADD COLUMN model TEXT"
            )

        if "fallback" not in mevcut:
            c.execute(
                "ALTER TABLE sohbet_loglari ADD COLUMN fallback INTEGER DEFAULT 0"
            )

        c.commit()


# ============================================================
# Eski aday sistemi
# ============================================================

def adaylari_getir():
    with _conn(ADAY_DB) as c:
        rows = c.execute(
            "SELECT * FROM adaylar ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def aday_ekle(
    isim,
    tarih,
    aciklama,
    davet,
    randevu,
    plan,
    kayit,
    takip,
    hayir,
    is_ariyor,
    kaynak_hash=None
):
    try:
        with _conn(ADAY_DB) as c:
            c.execute(
                '''
                INSERT INTO adaylar
                (
                    isim,
                    tarih,
                    aciklama,
                    davet,
                    randevu,
                    plan,
                    kayit,
                    takip,
                    hayir,
                    is_ariyor,
                    kaynak_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    isim,
                    tarih,
                    aciklama,
                    int(davet),
                    int(randevu),
                    int(plan),
                    int(kayit),
                    int(takip),
                    int(hayir),
                    int(is_ariyor),
                    kaynak_hash
                )
            )

            eski_id = c.execute(
                "SELECT last_insert_rowid() AS id"
            ).fetchone()["id"]

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            profil = c.execute(
                '''
                SELECT id
                FROM aday_profil
                WHERE lower(trim(isim)) = lower(trim(?))
                ORDER BY id ASC
                LIMIT 1
                ''',
                (isim.strip(),)
            ).fetchone()

            if profil is None:
                cur = c.execute(
                    '''
                    INSERT INTO aday_profil
                    (isim, telefon, email, adres, aktif, created_at, updated_at)
                    VALUES (?, '', '', '', 1, ?, ?)
                    ''',
                    (isim.strip(), now, now)
                )
                profil_id = cur.lastrowid
            else:
                profil_id = profil["id"]

            c.execute(
                '''
                INSERT INTO aday_olaylari
                (
                    aday_id,
                    tarih,
                    olay_tipi,
                    olay_metni,
                    kaynak,
                    kaynak_kayit_id,
                    davet,
                    randevu,
                    plan,
                    kayit,
                    takip,
                    hayir,
                    is_ariyor,
                    durum,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    profil_id,
                    tarih or "",
                    "Aday Kaydı",
                    aciklama or "",
                    "uygulama",
                    eski_id,
                    int(davet),
                    int(randevu),
                    int(plan),
                    int(kayit),
                    int(takip),
                    int(hayir),
                    int(is_ariyor),
                    "",
                    now
                )
            )

            c.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    except Exception as e:
        print(f"Aday ekleme hatası: {e}")
        return False


def aday_sil(aday_id):
    # Eski davranış korunuyor.
    with _conn(ADAY_DB) as c:
        c.execute(
            "DELETE FROM adaylar WHERE id=?",
            (aday_id,)
        )
        c.commit()


def tum_adaylari_sil():
    with _conn(ADAY_DB) as c:
        c.execute("DELETE FROM adaylar")
        c.commit()


# ============================================================
# Yeni Aday Kartı / Geçmiş sistemi
# ============================================================

def _profil_id_eski_aday(aday_id):
    with _conn(ADAY_DB) as c:
        row = c.execute(
            '''
            SELECT aday_id
            FROM aday_olaylari
            WHERE kaynak_kayit_id = ?
            ORDER BY id ASC
            LIMIT 1
            ''',
            (aday_id,)
        ).fetchone()

        if row:
            return row["aday_id"]

        eski = c.execute(
            "SELECT isim FROM adaylar WHERE id=?",
            (aday_id,)
        ).fetchone()

        if not eski:
            return None

        profil = c.execute(
            '''
            SELECT id
            FROM aday_profil
            WHERE lower(trim(isim)) = lower(trim(?))
            ORDER BY id ASC
            LIMIT 1
            ''',
            (eski["isim"] or "",)
        ).fetchone()

        return profil["id"] if profil else None


def aday_karti_getir(eski_aday_id):
    with _conn(ADAY_DB) as c:
        eski = c.execute(
            "SELECT * FROM adaylar WHERE id=?",
            (eski_aday_id,)
        ).fetchone()

        if not eski:
            return None

        profil_id = _profil_id_eski_aday(eski_aday_id)

        if profil_id is None:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = c.execute(
                '''
                INSERT INTO aday_profil
                (isim, telefon, email, adres, aktif, created_at, updated_at)
                VALUES (?, '', '', '', 1, ?, ?)
                ''',
                (eski["isim"] or "", now, now)
            )
            profil_id = cur.lastrowid

            c.execute(
                '''
                INSERT INTO aday_olaylari
                (
                    aday_id,
                    tarih,
                    olay_tipi,
                    olay_metni,
                    kaynak,
                    kaynak_kayit_id,
                    davet,
                    randevu,
                    plan,
                    kayit,
                    takip,
                    hayir,
                    is_ariyor,
                    durum,
                    created_at
                )
                VALUES (?, ?, 'Excel Geçmişi', ?, 'eski_kayit', ?, ?, ?, ?, ?, ?, ?, ?, '', ?)
                ''',
                (
                    profil_id,
                    eski["tarih"] or "",
                    eski["aciklama"] or "",
                    eski["id"],
                    int(eski["davet"] or 0),
                    int(eski["randevu"] or 0),
                    int(eski["plan"] or 0),
                    int(eski["kayit"] or 0),
                    int(eski["takip"] or 0),
                    int(eski["hayir"] or 0),
                    int(eski["is_ariyor"] or 0),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            c.commit()

        profil = c.execute(
            '''
            SELECT *
            FROM aday_profil
            WHERE id=?
            ''',
            (profil_id,)
        ).fetchone()

        olaylar = c.execute(
            '''
            SELECT *
            FROM aday_olaylari
            WHERE aday_id=?
            ORDER BY
                CASE
                    WHEN tarih IS NULL OR trim(tarih) = '' THEN 1
                    ELSE 0
                END,
                id ASC
            ''',
            (profil_id,)
        ).fetchall()

        son_durum = c.execute(
            '''
            SELECT durum
            FROM aday_olaylari
            WHERE aday_id=?
              AND durum IS NOT NULL
              AND trim(durum) <> ''
            ORDER BY id DESC
            LIMIT 1
            ''',
            (profil_id,)
        ).fetchone()

        durum = (
            son_durum["durum"]
            if son_durum and son_durum["durum"]
            else "🟢 Aktif"
        )

        return {
            "aday_id": eski_aday_id,
            "profil_id": profil_id,
            "isim": profil["isim"] if profil else eski["isim"],
            "telefon": profil["telefon"] if profil else "",
            "email": profil["email"] if profil else "",
            "adres": profil["adres"] if profil else "",
            "aktif": bool(profil["aktif"]) if profil else True,
            "durum": durum,
            "gecmis": [dict(x) for x in olaylar]
        }


def aday_profil_guncelle(eski_aday_id, telefon, email, adres):
    with _conn(ADAY_DB) as c:
        profil_id = _profil_id_eski_aday(eski_aday_id)

        if profil_id is None:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            '''
            UPDATE aday_profil
            SET telefon=?,
                email=?,
                adres=?,
                updated_at=?
            WHERE id=?
            ''',
            (
                telefon or "",
                email or "",
                adres or "",
                now,
                profil_id
            )
        )
        c.commit()

    return True


def aday_gelisme_ekle(
    eski_aday_id,
    tarih,
    olay_tipi,
    olay_metni,
    durum=""
):
    with _conn(ADAY_DB) as c:
        profil_id = _profil_id_eski_aday(eski_aday_id)

        if profil_id is None:
            return False, "Aday bulunamadı."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            '''
            INSERT INTO aday_olaylari
            (
                aday_id,
                tarih,
                olay_tipi,
                olay_metni,
                kaynak,
                kaynak_kayit_id,
                davet,
                randevu,
                plan,
                kayit,
                takip,
                hayir,
                is_ariyor,
                durum,
                created_at
            )
            VALUES (?, ?, ?, ?, 'uygulama', ?, 0, 0, 0, 0, 0, 0, 0, ?, ?)
            ''',
            (
                profil_id,
                tarih or "",
                olay_tipi or "Not",
                olay_metni or "",
                eski_aday_id,
                durum or "",
                now
            )
        )

        c.commit()

    return True, "Gelişme kaydedildi."


# ============================================================
# Chat İşlemleri
# ============================================================

def chat_mesajlari_getir():
    with _conn(CHAT_DB) as c:
        rows = c.execute(
            '''
            SELECT rol, icerik, zaman, model, fallback
            FROM sohbet_loglari
            ORDER BY id ASC
            '''
        ).fetchall()

    return [
        {
            "role": r["rol"],
            "content": r["icerik"],
            "zaman": r["zaman"],
            "model": r["model"],
            "fallback": bool(r["fallback"])
        }
        for r in rows
    ]


def chat_mesaj_ekle(
    rol,
    icerik,
    model=None,
    fallback=False
):
    with _conn(CHAT_DB) as c:
        c.execute(
            '''
            INSERT INTO sohbet_loglari
            (rol, icerik, zaman, model, fallback)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                rol,
                icerik,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                model,
                int(bool(fallback))
            )
        )
        c.commit()


def chat_temizle():
    with _conn(CHAT_DB) as c:
        c.execute("DELETE FROM sohbet_loglari")
        c.commit()
