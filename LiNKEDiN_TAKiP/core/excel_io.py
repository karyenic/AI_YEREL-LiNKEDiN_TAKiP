import pandas as pd
import io
import hashlib
from datetime import datetime
from pathlib import Path
from core.database import aday_ekle, adaylari_getir


def _temiz_kolon(col):
    if pd.isna(col):
        return ""
    v = str(col).strip().upper()
    return (v.replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G')
             .replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C'))


def _evet_mi(val):
    return 1 if str(val).strip().lower() in ['evet', 'yes', 'true', '1', 'var', 'x', '✓', 'doğru'] else 0


def _satir_hash(isim, tarih, aciklama):
    raw = f"{isim}|{tarih}|{aciklama}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def excel_ice_aktar(dosya_yolu):
    """Excel dosyasını okur ve yeni adayları DB'ye ekler. Duplicate'leri atlar."""
    try:
        df = pd.read_excel(dosya_yolu, header=1)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    except Exception as e:
        return False, f"Excel okuma hatası: {e}"

    raw_cols = list(df.columns)
    clean_cols = [_temiz_kolon(c) for c in raw_cols]

    eklenen = 0
    atlanan = 0

    for _, row in df.iterrows():
        r = {'isim': '', 'tarih': '', 'aciklama': '',
             'davet': 0, 'randevu': 0, 'plan': 0, 'kayit': 0,
             'takip': 0, 'hayir': 0, 'is_ariyor': 0}

        for orig, c in zip(raw_cols, clean_cols):
            val = row[orig]
            if pd.isna(val):
                val = ""
            if any(k in c for k in ["ADI", "SOYADI", "ISIM", "NAME"]):
                r['isim'] = str(val)
            elif any(k in c for k in ["TARIH", "DATE", "BAGLANTI"]):
                if val != "":
                    try:
                        r['tarih'] = pd.to_datetime(val).strftime('%d %m %y')
                    except Exception:
                        r['tarih'] = str(val)
            elif "DAVET" in c:
                r['davet'] = _evet_mi(val)
            elif "RANDEVU" in c:
                r['randevu'] = _evet_mi(val)
            elif "PLAN" in c:
                r['plan'] = _evet_mi(val)
            elif "KAYIT" in c:
                r['kayit'] = _evet_mi(val)
            elif "TAKIP" in c:
                r['takip'] = _evet_mi(val)
            elif "YANIT" in c or "HAYIR" in c:
                r['hayir'] = _evet_mi(val)
            elif "IS ARIYOR" in c or "IS_ARIYOR" in c:
                r['is_ariyor'] = _evet_mi(val)
            elif any(k in c for k in ["ACIKLAMA", "NOT", "DETAIL"]):
                r['aciklama'] = str(val)

        if r['isim'].strip() == "" or r['isim'].isdigit():
            continue
        if r['tarih'] == "":
            r['tarih'] = datetime.now().strftime("%d %m %y")

        h = _satir_hash(r['isim'], r['tarih'], r['aciklama'])
        if aday_ekle(r['isim'], r['tarih'], r['aciklama'],
                     r['davet'], r['randevu'], r['plan'], r['kayit'],
                     r['takip'], r['hayir'], r['is_ariyor'], kaynak_hash=h):
            eklenen += 1
        else:
            atlanan += 1

    return True, f"{eklenen} yeni aday eklendi, {atlanan} zaten mevcuttu."


def excel_disa_aktar():
    """Adayları Excel'e çevirir, bytes döner."""
    adaylar = adaylari_getir()
    if not adaylar:
        return None

    df = pd.DataFrame(adaylar)
    mapping = {
        'isim': 'ADI SOYADI', 'davet': 'DAVET YAPILDI',
        'plan': 'PLAN ANLTD', 'kayit': 'KAYIT', 'takip': 'TAKIP',
        'hayir': 'YANIT', 'tarih': 'BAGLANTI TARIHI',
        'randevu': 'RANDEVU OLUSTU', 'aciklama': 'ACIKLAMA',
        'is_ariyor': 'IS ARIYOR'
    }
    df = df.rename(columns=mapping)
    bool_cols = ['DAVET YAPILDI', 'PLAN ANLTD', 'KAYIT', 'TAKIP',
                 'YANIT', 'RANDEVU OLUSTU', 'IS ARIYOR']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: 'EVET' if x == 1 else 'HAYIR')

    # gereksiz kolonları at
    keep = [c for c in ['ADI SOYADI', 'DAVET YAPILDI', 'PLAN ANLTD', 'KAYIT',
                        'TAKIP', 'YANIT', 'BAGLANTI TARIHI', 'RANDEVU OLUSTU',
                        'ACIKLAMA', 'IS ARIYOR'] if c in df.columns]
    df = df[keep]

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name='Adaylar')
    out.seek(0)
    return out.getvalue()