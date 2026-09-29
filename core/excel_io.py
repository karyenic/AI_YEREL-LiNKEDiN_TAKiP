"""Excel içe/dışa aktarma modülü."""
import io
import hashlib
import unicodedata
from datetime import datetime
from pathlib import Path
import openpyxl
import pandas as pd
from core.database import aday_ekle, adaylari_getir


# ═══════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════
def _satir_hash(isim, tarih, aciklama):
    """Mükerrer kontrolü için hash. Tarih DAHİL EDİLMEZ."""
    def normalize(s):
        if not s:
            return ""
        s = str(s)
        s = unicodedata.normalize("NFKD", s)
        # Görünmez karakterleri temizle
        for ch in ["\u00a0", "\u200b", "\u200c", "\u200d", "\ufeff", "\u2028", "\u2029"]:
            s = s.replace(ch, " ")
        # Tüm whitespace'i tek boşluğa indir + baş/son temizle
        s = " ".join(s.split())
        return s.lower()

    isim_norm = normalize(isim)
    aciklama_norm = normalize(aciklama)
    raw = f"{isim_norm}|{aciklama_norm}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _kolon_bul(headers, *names):
    """Sütun başlığı arar. Tam eşleşme, sonra kısmi eşleşme."""
    for n in names:
        n = n.lower().strip()
        # 1. Tam eşleşme
        if n in headers:
            return headers.index(n)
        # 2. Kısmi eşleşme (başlık, aranan kelimeyi içeriyor mu?)
        for i, h in enumerate(headers):
            if n in h:
                return i
    return None


def _evet_mi(val):
    """Excel hücresini 0/1'e çevirir."""
    if val is None:
        return 0
    s = str(val).strip().lower()
    return 1 if s in ["evet", "yes", "true", "1", "var", "x", "✓", "doğru", "e"] else 0


# ═══════════════════════════════════════════════════════════
# EXCEL İÇE AKTARMA
# ═══════════════════════════════════════════════════════════
def excel_ice_aktar(excel_yolu):
    """Excel dosyasını okur ve yeni adayları DB'ye ekler."""
    yol = Path(excel_yolu)
    if not yol.exists():
        return False, f"Excel dosyası bulunamadı: {yol}"

    try:
        wb = openpyxl.load_workbook(yol, data_only=True)
        ws = wb.active

        # 1. Başlıkları oku (1. satır)
        headers = []
        for c in ws[1]:
            if c.value is None:
                headers.append("")
            else:
                headers.append(str(c.value).strip().lower())

        # 2. Sütun indekslerini bul
        isim_i = _kolon_bul(headers, "isim", "ad", "adi", "adi soyadi", "name", "aday", "aday ismi")
        tarih_i = _kolon_bul(headers, "tarih", "date", "gun", "baglanti tarihi", "baglanti")
        aciklama_i = _kolon_bul(headers, "aciklama", "dusunceler", "not", "notes", "thoughts", "detay")
        davet_i = _kolon_bul(headers, "davet")
        randevu_i = _kolon_bul(headers, "randevu")
        plan_i = _kolon_bul(headers, "plan")
        kayit_i = _kolon_bul(headers, "kayit")
        takip_i = _kolon_bul(headers, "takip")
        hayir_i = _kolon_bul(headers, "hayir", "yanit")
        is_ariyor_i = _kolon_bul(headers, "is_ariyor", "is ariyor", "isariyor")

        if isim_i is None:
            return False, f"Excel'de 'İsim' sütunu bulunamadı. Başlık satırı: {headers}"

        # 3. Satırları işle
        eklenen = 0
        atlanan = 0
        bugun = datetime.now().strftime("%d %m %y")

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue

            isim = str(row[isim_i]).strip() if isim_i < len(row) and row[isim_i] else ""
            if not isim or isim.isdigit():
                continue

            # Tarih
            tarih = ""
            if tarih_i is not None and tarih_i < len(row) and row[tarih_i]:
                v = row[tarih_i]
                try:
                    tarih = pd.to_datetime(v).strftime("%d %m %y")
                except Exception:
                    tarih = str(v).strip()
            if not tarih:
                tarih = bugun

            # Açıklama
            aciklama = ""
            if aciklama_i is not None and aciklama_i < len(row) and row[aciklama_i]:
                aciklama = str(row[aciklama_i]).strip()

            # Booleanlar
            davet = _evet_mi(row[davet_i]) if davet_i is not None and davet_i < len(row) else 0
            randevu = _evet_mi(row[randevu_i]) if randevu_i is not None and randevu_i < len(row) else 0
            plan = _evet_mi(row[plan_i]) if plan_i is not None and plan_i < len(row) else 0
            kayit = _evet_mi(row[kayit_i]) if kayit_i is not None and kayit_i < len(row) else 0
            takip = _evet_mi(row[takip_i]) if takip_i is not None and takip_i < len(row) else 0
            hayir = _evet_mi(row[hayir_i]) if hayir_i is not None and hayir_i < len(row) else 0
            is_ariyor = _evet_mi(row[is_ariyor_i]) if is_ariyor_i is not None and is_ariyor_i < len(row) else 0

            h = _satir_hash(isim, tarih, aciklama)
            ok = aday_ekle(isim, tarih, aciklama, davet, randevu, plan,
                           kayit, takip, hayir, is_ariyor, kaynak_hash=h)
            if ok:
                eklenen += 1
            else:
                atlanan += 1

        return True, f"{eklenen} yeni aday eklendi, {atlanan} zaten mevcuttu."

    except Exception as e:
        return False, f"Excel okuma hatası: {e}"


# ═══════════════════════════════════════════════════════════
# EXCEL DIŞA AKTARMA
# ═══════════════════════════════════════════════════════════
def excel_disa_aktar():
    """Adayları Excel formatında bytes olarak döner."""
    adaylar = adaylari_getir()
    if not adaylar:
        return None

    df = pd.DataFrame(adaylar)

    mapping = {
        'isim': 'ADI SOYADI',
        'davet': 'DAVET YAPILDI',
        'plan': 'PLAN ANLTD',
        'kayit': 'KAYIT',
        'takip': 'TAKIP',
        'hayir': 'YANIT',
        'tarih': 'BAGLANTI TARIHI',
        'randevu': 'RANDEVU OLUSTU',
        'aciklama': 'ACIKLAMA',
        'is_ariyor': 'IS ARIYOR',
    }
    df = df.rename(columns=mapping)

    bool_cols = ['DAVET YAPILDI', 'PLAN ANLTD', 'KAYIT', 'TAKIP',
                 'YANIT', 'RANDEVU OLUSTU', 'IS ARIYOR']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: 'EVET' if x == 1 else 'HAYIR')

    keep = [c for c in [
        'ADI SOYADI', 'DAVET YAPILDI', 'PLAN ANLTD', 'KAYIT',
        'TAKIP', 'YANIT', 'BAGLANTI TARIHI', 'RANDEVU OLUSTU',
        'ACIKLAMA', 'IS ARIYOR'
    ] if c in df.columns]
    df = df[keep]

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Adaylar')
    out.seek(0)
    return out.getvalue()