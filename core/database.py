import sqlite3
from datetime import datetime
from config import ADAY_DB, CHAT_DB



def _profil_id_eski_aday(aday_id):
    """Eski aday ID'sinden profil ID'sini bulur."""
    with _conn(ADAY_DB) as c:
        # 1. aday_olaylari tablosunda ara
        row = c.execute(
            """
            SELECT aday_id
            FROM aday_olaylari
            WHERE kaynak_kayit_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (aday_id,)
        ).fetchone()

        if row:
            return row["aday_id"]

        # 2. isim ile aday_profil'da ara
        eski = c.execute(
            "SELECT isim FROM adaylar WHERE id=?",
            (aday_id,)
        ).fetchone()

        if not eski:
            return None

        isim = eski["isim"] or ""

        # 3. Ayni isimdeki profil kaydini bul
        profil = c.execute(
            "SELECT id FROM aday_profil WHERE isim=? LIMIT 1",
            (isim,)
        ).fetchone()

        if profil:
            return profil["id"]

        return None

def _conn(db_path):
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        timeout=10
    )
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass
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
                    (isim, telefon, email, adres, durum, aktif, created_at, updated_at)
                    VALUES (?, '', '', '', ?, 1, ?, ?)
                    ''',
                    (isim.strip(), durum or "🆕 Yeni", now, now)
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

        if "kategori" not in mevcut:
            c.execute(
                "ALTER TABLE sohbet_loglari ADD COLUMN kategori TEXT DEFAULT 'sohbet'"
            )
            # Mevcut mesajlari geriye donuk kategorize et
            print("Mevcut mesajlar kategorize ediliyor...")
            tum_mesajlar = c.execute(
                "SELECT id, rol, icerik FROM sohbet_loglari"
            ).fetchall()
            for m in tum_mesajlar:
                k = _kategori_bul(m["icerik"], m["rol"])
                c.execute(
                    "UPDATE sohbet_loglari SET kategori=? WHERE id=?",
                    (k, m["id"])
                )
            print(f"{len(tum_mesajlar)} mesaj kategorize edildi")

        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_sohbet_kategori ON sohbet_loglari(kategori)"
        )

        c.commit()


# ============================================================
# Eski aday sistemi
# ============================================================

def adaylari_getir():
    """Tum adaylari son durumlariyla birlikte dondurur.
    Durum, aday_profil tablosundan okunur (kart ile ayni kaynak)."""
    with _conn(ADAY_DB) as c:
        rows = c.execute("SELECT * FROM adaylar ORDER BY id DESC").fetchall()

        sonuc = []
        for r in rows:
            d = dict(r)
            isim = (d.get("isim") or "").strip()

            # Durum: aday_profil'DAN (kart ile ayni kaynak)
            durum = "Yeni"
            try:
                if isim:
                    profil = c.execute(
                        "SELECT durum FROM aday_profil WHERE LOWER(TRIM(isim))=LOWER(TRIM(?)) LIMIT 1",
                        (isim,)
                    ).fetchone()
                    
                    if profil and profil["durum"]:
                        durum = profil["durum"]
                    else:
                        durum = "Yeni"
            except Exception:
                durum = "Yeni"
            d["durum"] = durum
            sonuc.append(d)

    return sonuc

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
    kaynak_hash=None,
    linkedin_url=None,
    durum=""
):
    try:
        with _conn(ADAY_DB) as c:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                    kaynak_hash,
                    linkedin_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    kaynak_hash,
                    linkedin_url
                )
            )

            eski_id = c.execute(
                "SELECT last_insert_rowid() AS id"
            ).fetchone()["id"]

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
                    (isim, telefon, email, adres, durum, aktif, created_at, updated_at)
                    VALUES (?, '', '', '', ?, 1, ?, ?)
                    ''',
                    (isim.strip(), durum or "🆕 Yeni", now, now)
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
                    durum or "",
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

def aday_karti_getir(eski_aday_id):
    """Eski aday ID'sinden kart bilgilerini getirir."""
    with _conn(ADAY_DB) as c:
        # 1. adaylar tablosundan ana kaydi al
        eski = c.execute(
            "SELECT * FROM adaylar WHERE id=?",
            (eski_aday_id,)
        ).fetchone()

        if not eski:
            return None

        isim = eski["isim"] or ""

        # 2. Son durum: aday_olaylari'ndan
        durum_row = c.execute("""
            SELECT durum FROM aday_olaylari
            WHERE kaynak_kayit_id = ?
              AND durum IS NOT NULL
              AND durum != ''
            ORDER BY id DESC LIMIT 1
        """, (eski_aday_id,)).fetchone()

        durum = durum_row["durum"] if durum_row else "\U0001F195 Yeni"

        # 3. Profil bilgileri (varsa)
        profil = c.execute(
            "SELECT * FROM aday_profil WHERE isim=? LIMIT 1",
            (isim,)
        ).fetchone()

        # 4. Gecmis olaylar
        gecmis = []
        try:
            gecmis_rows = c.execute("""
                SELECT tarih, olay_tipi, olay_metni, durum
                FROM aday_olaylari
                WHERE kaynak_kayit_id = ?
                ORDER BY tarih DESC, id DESC
                LIMIT 50
            """, (eski_aday_id,)).fetchall()
            gecmis = [dict(r) for r in gecmis_rows]
        except Exception:
            gecmis = []

        def _get(row, key, default=None):
            try:
                return row[key] if row and key in row.keys() else default
            except Exception:
                return default

        return {
            "id": eski["id"],
            "isim": isim,
            "tarih": _get(eski, "tarih", ""),
            "aciklama": _get(eski, "aciklama", ""),
            "davet": _get(eski, "davet", 0),
            "randevu": _get(eski, "randevu", 0),
            "plan": _get(eski, "plan", 0),
            "kayit": _get(eski, "kayit", 0),
            "takip": _get(eski, "takip", 0),
            "hayir": _get(eski, "hayir", 0),
            "is_ariyor": _get(eski, "is_ariyor", 0),
            "linkedin_url": _get(eski, "linkedin_url", None),
            "telefon": _get(profil, "telefon", ""),
            "email": _get(profil, "email", ""),
            "adres": _get(profil, "adres", ""),
            "durum": durum,
            "gecmis": gecmis
        }

def aday_profil_guncelle(aday_id, telefon, email, adres):
    """Aday profil bilgilerini gunceller (telefon, email, adres)."""
    with _conn(ADAY_DB) as c:
        # 1. Adayin ismini al
        eski = c.execute(
            "SELECT isim FROM adaylar WHERE id=?",
            (aday_id,)
        ).fetchone()

        if not eski:
            return False

        isim = eski["isim"] or ""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. Bu isimde profil var mi?
        profil = c.execute(
            "SELECT id FROM aday_profil WHERE isim=? LIMIT 1",
            (isim,)
        ).fetchone()

        if profil:
            # 3a. Varsa guncelle
            c.execute(
                """
                UPDATE aday_profil
                SET telefon=?, email=?, adres=?, updated_at=?
                WHERE id=?
                """,
                (telefon, email, adres, now, profil["id"])
            )
        else:
            # 3b. Yoksa yeni olustur
            c.execute(
                """
                INSERT INTO aday_profil
                (isim, telefon, email, adres, aktif, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (isim, telefon, email, adres, now, now)
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

        # Durum verildiyse aday_profil.durum'u da guncelle
        if durum and str(durum).strip():
            try:
                isim_row = c.execute(
                    "SELECT isim FROM adaylar WHERE id=?",
                    (eski_aday_id,)
                ).fetchone()

                if isim_row:
                    try:
                        isim = isim_row["isim"] if hasattr(isim_row, "keys") else isim_row[0]
                    except Exception:
                        isim = str(isim_row)
                    isim = (isim or "").strip()

                    if isim:
                        profil = c.execute(
                            "SELECT id FROM aday_profil WHERE isim=? LIMIT 1",
                            (isim,)
                        ).fetchone()

                        if profil:
                            try:
                                pid = profil["id"] if hasattr(profil, "keys") else profil[0]
                            except Exception:
                                pid = profil
                            c.execute(
                                "UPDATE aday_profil SET durum=?, updated_at=? WHERE id=?",
                                (durum, now, pid)
                            )
                        else:
                            c.execute(
                                "INSERT INTO aday_profil (isim, telefon, email, adres, durum, aktif, created_at, updated_at) VALUES (?, '', '', '', ?, 1, ?, ?)",
                                (isim, durum, now, now)
                            )
            except Exception as e:
                print(f"Durum guncelleme hatasi: {e}")


        c.commit()

    return True, "Gelişme kaydedildi."


# ============================================================
# Chat İşlemleri
# ============================================================

def _kategori_bul(mesaj, rol):
    """Mesaji keyword bazli kategorize eder.
    Kategoriler: sohbet, istatistik, sorgu, oneri, analiz
    Oncelik sirasi: oneri > analiz > istatistik > sorgu > sohbet
    """
    if not mesaj:
        return "sohbet"

    m = mesaj.lower()
    # Turkce karakter normalizasyonu
    tr_map = str.maketrans("İIıçşğüöÇŞĞÜÖ", "iiicsguoCSGUO")
    m = mesaj.translate(tr_map).lower()
    if rol == "assistant":
        # Cevap icerigi bazli
        if "oneri:" in m or "aksiyon:" in m:
            return "oneri"
        if any(k in m for k in ["funnel", "analiz", "trend", "oran", "donusum"]):
            return "analiz"
        return "sohbet"

    # Kullanici mesaji - ONERI once (daha guclu sinyal)
    if any(k in m for k in ["degerlendir", "oner", "odaklan", "oncelik",
                            "strateji", "planla", "yapalim", "yapmali",
                            "ne yap", "nasil ilerle", "kimlere odak"]):
        return "oneri"
    # ANALIZ
    if any(k in m for k in ["analiz", "funnel", "trend", "karsilastir", "rapor"]):
        return "analiz"
    # ISTATISTIK
    if any(k in m for k in ["kac", "toplam", "sayi", "adet", "liste", "kactane"]):
        return "istatistik"
    # SORGU
    if any(k in m for k in ["kim", "nerede", "hangi", "ne zaman", "baska", "neler"]):
        return "sorgu"
    return "sohbet"


def chat_mesajlari_getir():
    with _conn(CHAT_DB) as c:
        rows = c.execute(
            '''
            SELECT rol, icerik, zaman, model, fallback, kategori
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
            "fallback": bool(r["fallback"]),
            "kategori": r["kategori"] or "sohbet"
        }
        for r in rows
    ]


def chat_mesaj_ekle(
    rol,
    icerik,
    model=None,
    fallback=False,
    kategori=None
):
    # Kategori verilmediyse otomatik bul
    if kategori is None:
        kategori = _kategori_bul(icerik, rol)

    with _conn(CHAT_DB) as c:
        c.execute(
            '''
            INSERT INTO sohbet_loglari
            (rol, icerik, zaman, model, fallback, kategori)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                rol,
                icerik,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                model,
                int(bool(fallback)),
                kategori
            )
        )
        c.commit()


def chat_temizle():
    with _conn(CHAT_DB) as c:
        c.execute("DELETE FROM sohbet_loglari")
        c.commit()



def aday_linkedin_guncelle(aday_id, linkedin_url):
    """Adayin LinkedIn URL'sini gunceller."""
    with _conn(ADAY_DB) as c:
        c.execute(
            "UPDATE adaylar SET linkedin_url=? WHERE id=?",
            (linkedin_url, aday_id)
        )
        c.commit()
        return c.total_changes > 0



def aday_durum_otomatik_guncelle(aday_id, davet=0, plan=0, kayit=0, hayir=0):
    """Checkbox'lara gore statuyu otomatik gunceller.
    
    Kurallar:
    - Hayir ✓ -> 🔴 Olumsuz
    - Plan ✓ + Kayit ✓ -> 🎓 SG
    - Plan ✓ + Kayit ✗ -> 🔔 Takip
    - Plan ✗ (ve davet yok) -> ❄️ DeepFreeze
    """
    yeni_durum = None
    
    if hayir == 1:
        yeni_durum = "🔴 Olumsuz"
    elif plan == 1 and kayit == 1:
        yeni_durum = "🎓 SG"
    elif plan == 1 and kayit == 0:
        yeni_durum = "🔔 Takip"
    elif plan == 0 and davet == 1:
        yeni_durum = "🟢 Aktif"  # Davet var ama plan yok
    else:
        return False  # Statu degismedi
    
    # Statu guncelle
    with _conn(ADAY_DB) as c:
        eski = c.execute(
            "SELECT isim FROM adaylar WHERE id=?",
            (aday_id,)
        ).fetchone()
        
        if not eski:
            return False
        
        isim = eski["isim"] or ""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        profil = c.execute(
            "SELECT id FROM aday_profil WHERE isim=? LIMIT 1",
            (isim,)
        ).fetchone()
        
        if profil:
            c.execute(
                "UPDATE aday_profil SET durum=?, updated_at=? WHERE id=?",
                (yeni_durum, now, profil["id"])
            )
        else:
            c.execute(
                """
                INSERT INTO aday_profil
                (isim, telefon, email, adres, durum, aktif, created_at, updated_at)
                VALUES (?, '', '', '', ?, 1, ?, ?)
                """,
                (isim, yeni_durum, now, now)
            )
        c.commit()
        print(f"Otomatik statu: {isim} -> {yeni_durum}")
        return True
