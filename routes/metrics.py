from flask import Blueprint, jsonify
import pandas as pd
from datetime import datetime
from core.database import adaylari_getir, tarih_parse
from core.ollama_client import chat_stream
from config import DEFAULT_MODEL, DEFAULT_FALLBACK

bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")


def _huni_hesapla(adaylar):
    """Kaba listeden kayda kadar GERÇEK huni (bir onceki adima gore %).
    Bu rakamlar LLM'e DOGRU VERI olarak verilir - LLM kendi hesaplamaz,
    hesaplanmis rakami yorumlar (halusinasyonu engeller)."""
    toplam = len(adaylar)

    def s(k):
        return sum(int(a.get(k) or 0) for a in adaylar)

    davet, randevu, plan = s('davet'), s('randevu'), s('plan')
    kayit, takip, hayir = s('kayit'), s('takip'), s('hayir')
    is_ariyor = s('is_ariyor')

    def oran(pay, payda):
        return round(pay / payda * 100, 1) if payda else 0.0

    # Hala surecte olan (ne kayit oldu ne red aldi)
    aktif_takipte = sum(
        1 for a in adaylar
        if not int(a.get('kayit') or 0) and not int(a.get('hayir') or 0)
    )

    return {
        "toplam": toplam,
        "davet": davet, "randevu": randevu, "plan": plan,
        "kayit": kayit, "takip": takip, "hayir": hayir,
        "is_ariyor": is_ariyor,
        "aktif_takipte": aktif_takipte,
        # Zincirdeki her adimin BIR ONCEKI adima gore donusum orani
        "oran_kabadan_davete": oran(davet, toplam),
        "oran_davetten_randevuya": oran(randevu, davet),
        "oran_randevudan_plana": oran(plan, randevu),
        "oran_plandan_kayda": oran(kayit, plan),
        # Ucdan uca: kaba listeden kayda genel basari orani
        "oran_uctan_uca": oran(kayit, toplam),
        "oran_red": oran(hayir, toplam),
        # Eskiye uyumluluk
        "davet_randevu_oran": oran(randevu, davet),
        "plan_kayit_oran": oran(kayit, plan),
    }


def _riskli_adaylar(adaylar, limit=10):
    """Her aktif aday icin: gercek temas ayrimi + son 5 olay.
    Excel Geçmişi ve Aday Kaydı = VERI GIRISI, temas DEGIL."""
    from core.database import aday_karti_getir

    # Bu olay tipleri temas SAYILMAZ (otomatik/veri girisi)
    TEMAS_DISI = ("Excel Geçmişi", "Excel Gecmisi", "Aday Kaydı", "Aday Kaydi")

    aktif = [
        a for a in adaylar
        if not int(a.get('kayit') or 0) and not int(a.get('hayir') or 0)
    ]

    bugun = pd.Timestamp.now().normalize()
    sonuc = []

    for a in aktif:
        kart = aday_karti_getir(a.get("id"))
        if not kart:
            continue
        gecmis = kart.get("gecmis", []) or []
        if not gecmis:
            continue

        # Tum gecmis tarihleri
        tum_tarihler = []
        gercek_temas_tarihleri = []
        for o in gecmis:
            t = tarih_parse(o.get("tarih"))
            if pd.isna(t):
                continue
            tum_tarihler.append(t)
            tip = (o.get("olay_tipi") or "").strip()
            if tip not in TEMAS_DISI:
                gercek_temas_tarihleri.append(t)

        if not tum_tarihler:
            continue

        # Sisteme kayit tarihi = ilk olay
        ilk_t = min(tum_tarihler)
        # Gercek temas = Excel/Aday Kaydi HARIC son olay
        if gercek_temas_tarihleri:
            son_gercek_t = max(gercek_temas_tarihleri)
            gercek_temas_var = True
            gun_temassiz = int((bugun - son_gercek_t.normalize()).days)
            son_temas_str = son_gercek_t.strftime("%d.%m.%Y")
        else:
            son_gercek_t = None
            gercek_temas_var = False
            # Hic temas yoksa, sisteme kayittan beri gecen sure
            gun_temassiz = int((bugun - ilk_t.normalize()).days)
            son_temas_str = "-"

        # Asama (net etiketler)
        if not gercek_temas_var:
            asama = "hic_temas_yok"
        elif a.get('plan'):
            asama = "plan_yapildi"
        elif a.get('randevu'):
            asama = "randevu_var"
        elif a.get('davet'):
            asama = "davet_edildi"
        else:
            asama = "kaba_listede"

        # Son 5 olay
        olaylar = []
        for o in gecmis[:5]:
            metin = (o.get("olay_metni") or "").strip()
            if len(metin) > 400:
                metin = metin[:400] + "..."
            olaylar.append({
                "tarih": o.get("tarih", ""),
                "tip": o.get("olay_tipi", ""),
                "metin": metin,
            })

        sonuc.append({
            "isim": a.get("isim", "?"),
            "durum": kart.get("durum", "?"),
            "telefon": (kart.get("telefon") or "").strip(),
            "email": (kart.get("email") or "").strip(),
            "gercek_temas_var": gercek_temas_var,
            "gun_temassiz": gun_temassiz,
            "asama": asama,
            "sisteme_kayit": ilk_t.strftime("%d.%m.%Y"),
            "son_gercek_temas": son_temas_str,
            "olaylar": olaylar,
            "_sort": -gun_temassiz,
        })

    ASAMA_ONCELIK = {"plan_yapildi": 0, "randevu_var": 1, "davet_edildi": 2, "kaba_listede": 3, "hic_temas_yok": 4}
    sonuc.sort(key=lambda x: (ASAMA_ONCELIK.get(x["asama"], 99), x["_sort"]))
    return sonuc[:limit]

def _firsat_adaylar(adaylar, limit=10):
    """Son 7 gundeki olumlu sinyalleri tarar, firsat adaylarini dondurur."""
    from core.database import aday_karti_getir

    def _norm(s):
        if not s:
            return ""
        tr = str.maketrans(
            "\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc",
            "cgiosuCGIOSU"
        )
        return s.translate(tr).lower()

    # (kod, agirlik, etiket, anahtar_kelimeler)
    SINYALLER = [
        ("baglanti_istegi", 10, "Kendi baglanti istegi gonderdi",
         ["baglanti istegi gonderdi", "baglanti istegi gonderd",
          "istek gonderdi", "baglanti istegini kabul"]),
        ("telefon_verdi",   12, "Telefon numarasi verdi",
         ["telefon numarasini", "telefon numarasi",
          "telefonunu ver", "telefon paylast"]),
        ("bilgi_istedi",     7, "Bilgi/detay istedi",
         ["bilgi istedi", "detay istedi", "detaylari ned",
          "daha fazla bilgi", "bilgi almak istiyor"]),
        ("davet_kabul",      6, "LinkedIn davetini kabul etti",
         ["davetimi kabul", "daveti kabul",
          "baglanti istegimi kabul", "baglanti davetimi kabul"]),
        ("is_birligi_ilgi",  7, "Is birligine ilgi gosterdi",
         ["is birligi firsat", "is birligi",
          "degerlendir", "ilgi duyuyor"]),
        ("olumlu_yanit",     5, "Olumlu yanit / tesekkur",
         ["tesekkur ederim", "memnuniyet",
          "memnun oldum", "nazik mesaj"]),
        ("mesaj_gonderdi",   4, "Iki yonlu mesaj",
         ["mesaj gonderdi", "yanit gonderdi", "mesaj gonder"]),
    ]

    aktif = [
        a for a in adaylar
        if not int(a.get('kayit') or 0) and not int(a.get('hayir') or 0)
    ]

    bugun = pd.Timestamp.now().normalize()
    PENCERE = 7

    sonuc = []

    for a in aktif:
        kart = aday_karti_getir(a.get("id"))
        if not kart:
            continue
        gecmis = kart.get("gecmis", []) or []
        if not gecmis:
            continue

        bulunan_sinyaller = []
        toplam_agirlik = 0

        for o in gecmis:
            t = tarih_parse(o.get("tarih"))
            if pd.isna(t):
                continue
            gun_fark = int((bugun - t.normalize()).days)
            if gun_fark > PENCERE or gun_fark < 0:
                continue

            metin = (o.get("olay_metni") or "")
            metin_norm = _norm(metin)

            for kod, agirlik, etiket, kelimeler in SINYALLER:
                if any(s["kod"] == kod for s in bulunan_sinyaller):
                    continue
                for k in kelimeler:
                    if k in metin_norm:
                        bulunan_sinyaller.append({
                            "kod": kod,
                            "etiket": etiket,
                            "agirlik": agirlik,
                            "tarih": o.get("tarih", ""),
                            "metin": metin[:150],
                        })
                        toplam_agirlik += agirlik
                        break

        # Olumsuz sinyal kontrolu - son 7 gunde olumsuz kelime varsa firsat degil
        OLUMSUZ_KELIMELER = ("ilgilenmedi", "olumsuz", "reddetti",
                              "istemiyor", "hayir dedi", "uyumsuz",
                              "net hayir", "kesinlikle hayir", "asla",
                              "yanit vermedi", "donmedi")
        olumsuz_var = False
        for o in gecmis:
            t = tarih_parse(o.get("tarih"))
            if pd.isna(t):
                continue
            if int((bugun - t.normalize()).days) > PENCERE:
                continue
            m = _norm(o.get("olay_metni") or "")
            if any(k in m for k in OLUMSUZ_KELIMELER):
                olumsuz_var = True
                break

        if olumsuz_var:
            continue

        if not bulunan_sinyaller:
            continue

        tarihler = [tarih_parse(s["tarih"]) for s in bulunan_sinyaller]
        tarihler = [t for t in tarihler if not pd.isna(t)]
        if tarihler:
            son_temas_str = max(tarihler).strftime("%d.%m.%Y")
            gun_temassiz = int((bugun - max(tarihler).normalize()).days)
        else:
            son_temas_str = "-"
            gun_temassiz = 999

        olaylar = []
        for o in gecmis[:5]:
            metin = (o.get("olay_metni") or "").strip()
            if len(metin) > 400:
                metin = metin[:400] + "..."
            olaylar.append({
                "tarih": o.get("tarih", ""),
                "tip": o.get("olay_tipi", ""),
                "metin": metin,
            })

        sonuc.append({
            "isim": a.get("isim", "?"),
            "durum": kart.get("durum", "?"),
            "telefon": (kart.get("telefon") or "").strip(),
            "email": (kart.get("email") or "").strip(),
            "sinyaller": bulunan_sinyaller,
            "sinyal_gucu": toplam_agirlik,
            "son_temas": son_temas_str,
            "gun_temassiz": gun_temassiz,
            "olaylar": olaylar,
            "_sort": -toplam_agirlik,
        })

    sonuc.sort(key=lambda x: (x["_sort"], x["gun_temassiz"]))
    return sonuc[:limit]


@bp.route("", methods=["GET"])
def hesapla():
    adaylar = adaylari_getir()
    if not adaylar:
        return jsonify({"toplam": 0})
    return jsonify(_huni_hesapla(adaylar))


@bp.route("/ozet", methods=["POST"])
def ozet():
    """Girislerden (huni verisi + temassizlik suresi) CALISMA STRATEJISI,
    OLASILIK degerlendirmesi ve haftalik iletisim plani uretir.
    Rakamlar Python'da hesaplanir (asla LLM'e hesaplatilmaz), LLM sadece
    bu dogrulanmis verileri yorumlayip somut bir eylem plani cikarir."""
    adaylar = adaylari_getir()
    if not adaylar:
        return jsonify({"ozet": "Veritabanı boş, henüz bir strateji çıkarılamaz."})

    h = _huni_hesapla(adaylar)
    riskli = _riskli_adaylar(adaylar, limit=10)
    firsat = _firsat_adaylar(adaylar, limit=10)

    # Riskli adaylari DETAYLI formatta hazirla
    asama_etiket = {
        "hic_temas_yok": "HIC TEMAS EDILMEDI (sisteme kayitli, kimse aramadi)",
        "kaba_listede": "Kaba listede, sadece kayitli",
        "davet_edildi": "Davet edildi, cevap bekleniyor",
        "randevu_var": "Randevu verildi",
        "plan_yapildi": "PLAN ANLATILDI - TAKIP ASAMASI (plan gonderildi, geri bildirim bekleniyor)",
    }

    riskli_bloklar = []
    for r in riskli:
        asama_str = asama_etiket.get(r['asama'], r['asama'])
        # Iptal tespiti: son olayda iptal/duzeltme kelimesi var mi?
        _IPTAL_KEL = ("iptal", "gorusulmedi", "hatali kayit", "yanlis kayit",
                       "duzeltme", "gecersiz", "olmadi", "yapilmadi")
        _OLUMSUZ_KEL = ("ilgilenmedi", "olumsuz", "reddetti", "istemiyor",
                         "hayir dedi", "uyumsuz", "net hayir",
                         "kesinlikle hayir")
        _son_metin = (r["olaylar"][0]["metin"].lower()
                       if r.get("olaylar") else "")
        _iptal_var = any(k in _son_metin for k in _IPTAL_KEL)
        _olumsuz_var = any(k in _son_metin for k in _OLUMSUZ_KEL)
        if r['gercek_temas_var']:
            baslik = f"### {r['isim']}  |  Durum: {r['durum']}  |  {r['gun_temassiz']} gundur gercek temas yok"
            baslik += f"\n  Asama: {asama_str}"
            baslik += f"\n  Son gercek temas: {r['son_gercek_temas']}"
            if _iptal_var:
                baslik += "\n  !!! SON NOT IPTAL/DUZELTME ICERIYOR - ONCEKI KAYITLAR GECERSIZ !!!"
                baslik += "\n  !!! Bu adayla GORUSULMEMIS olabilir, notlari dikkatli oku. !!!"
            if _olumsuz_var:
                baslik += "\n  !!! SON NOT OLUMSUZ - ILGI KAYBI - HAFTALIK PLANA EKLEME !!!"
        else:
            baslik = f"### {r['isim']}  |  Durum: {r['durum']}  |  HIC TEMAS EDILMEDI"
            baslik += f"\n  Sisteme kayit: {r['sisteme_kayit']} ({r['gun_temassiz']} gun once)"

        if r['telefon'] or r['email']:
            ilet = []
            if r['telefon']: ilet.append(f"Tel:{r['telefon']}")
            if r['email']: ilet.append(f"Mail:{r['email']}")
            baslik += "\n  Iletisim: " + " | ".join(ilet)
        baslik += "\n  Gecmis:"
        for o in r['olaylar']:
            baslik += f"\n    - {o['tarih']} [{o['tip']}]: {o['metin']}"
        riskli_bloklar.append(baslik)

    riskli_metin = "\n\n".join(riskli_bloklar) if riskli_bloklar else "(temassizlik verisi yok)"

    # Firsat adaylarini DETAYLI formatta hazirla
    firsat_bloklar = []
    for f_item in firsat:
        baslik = f"### {f_item['isim']}  |  FIRSAT ADAYI  |  Sinyal Gucu: {f_item['sinyal_gucu']}"
        baslik += "\n  Durum: OLUMLU SINYAL veren aday (son 7 gunde)"
        baslik += f"\n  Son temas: {f_item['son_temas']} ({f_item['gun_temassiz']} gun once)"
        if f_item['telefon'] or f_item['email']:
            ilet = []
            if f_item['telefon']: ilet.append(f"Tel:{f_item['telefon']}")
            if f_item['email']: ilet.append(f"Mail:{f_item['email']}")
            baslik += "\n  Iletisim: " + " | ".join(ilet)
        baslik += "\n  Sinyaller:"
        for sg in f_item['sinyaller']:
            baslik += f"\n    - [{sg['etiket']}] {sg['tarih']}"
        firsat_bloklar.append(baslik)

    firsat_metin = "\n\n".join(firsat_bloklar) if firsat_bloklar else "(firsat sinyali yok)"

    bugun_str = datetime.now().strftime("%d.%m.%Y (%A)")

    prompt = f"""# ROL
Sen deneyimli bir network marketing is gelistirme kocusun. Adaylarla yapilan gorusmelerin notlarini okuyup STRATEJIK oneriler veriyorsun.

# IS AKISI
kaba liste -> davet -> randevu (1:1 veya Zoom) -> plan sunumu -> kayit -> baslatma toplantisi

# KRITIK BILGI: "TEMAS" TANIMI (IHALAL EDILEMEZ)
Asagidaki olay tipleri TEMAS SAYILMAZ — bunlar sadece VERI GIRISI:
- "Excel Geçmişi"  (adayin eski verisi sisteme aktarildi)
- "Aday Kaydı"     (aday sisteme eklendi, kimse aramadi)

Yani bir adayda sadece bu olaylar varsa -> "HIC TEMAS EDILMEDI" demektir.

# KRONOLOJI VE IPTAL (COK ONEMLI)
Notlar TARIH SIRASINA gore okunur. EN SON not = GUNCEL gercek.

IPTAL/DUZELTME notu tanimi: Son notta su kelimelerden biri geciyorsa:
  "iptal", "gorusulmedi", "hatali kayit", "yanlis kayit", "duzeltme",
  "gecersiz", "olmadi", "yapilmadi"
-> Bu, ONCEKI KAYITLARIN GECERSIZ oldugu anlamina gelir.

ORNEK:
  Davet (12.10): "telefon gorusmesi yapildi, randevu olusturuldu"
  Davet (12.10): "randevu olustu"  <- flag randevu=1
  Not (12.10): "randevu iptal ... hatali kayit, adayla gorusulmedi"
  -> DOGRU OKUMA: Randevu IPTAL, adayla GORUSULMEDI.
     Yeniden temas gerekiyor, "randevu var" SAYILMAZ.
  -> YANLIS OKUMA: "randevu var, plan sunumu yap" (flag yuzunden)

KURAL: randevu=1/plan=1 flag leri SON NOT iptal iceriyorsa GECERSIZDIR.
Bu durumda "gecen gorusmemizde" gibi GECMISE ATIF YAPMA. Boyle bir gorusme OLMADI.

# HUNI VERISI (bugun: {bugun_str}) — bu rakamlar kesin, yeniden hesaplama
Toplam kaba liste: {h['toplam']}
Davet: {h['davet']}  (kaba listeden davete: %{h['oran_kabadan_davete']})
Randevu: {h['randevu']}  (davetten randevuya: %{h['oran_davetten_randevuya']})
Plan sunumu: {h['plan']}  (randevudan plana: %{h['oran_randevudan_plana']})
Kayit: {h['kayit']}  (plandan kayda: %{h['oran_plandan_kayda']})
Ucdan uca: %{h['oran_uctan_uca']}
Red orani: %{h['oran_red']}
Hala surecte: {h['aktif_takipte']}

# FIRSAT ADAYLAR - YUKSEK ONCELIK (olumlu sinyaller)
Asagidaki adaylar son 7 gunde OLUMLU sinyal verdi. Ilk sirada bunlari ele al.
{firsat_metin}

# RİSKLI ADAYLAR - TAKIP LAZIM (notlari dahil)
{riskli_metin}

# GOREV
Asagidaki 4 basligi TURKCE uret:

**1. Huni Durumu**
Hangi adimda darbogaz var (en dusuk donusum), tek-iki cumle, rakamlarla.

**2. Aday Bazli Stratejik Oneri** (EN AZ 5 ADAY - ZORUNLU)
ONCE FIRSAT adaylarindan basla (olumlu sinyal verenler), sonra riskli adaylara gec.
Her aday icin:
- **Durum**: 1 cumle (gercek temas var mi, yok mu — buna gore cumle kur)
- **Yorum**: Adayin notundan cikarim (meslegi, motivasyonu, ilgisi)
- **Aksiyon**: Bugun/yarin tam olarak ne yapilmali
- **Mesaj metni onerisi**:
  * HIC TEMAS YOKSA → "tanisma mesaji" tonu:
    "Merhaba X Hanim/Bey, sizi [sebep] dolayisiyla ekibimize dahil etmek istiyoruz. Müsait oldugunuzda kisa bir gorusme planlayabilir miyiz?"
  * GECMIS TEMAS VARSA → samimi takip tonu.

**3. Haftalik Optimal Calisma Plani**
7 gun (Pazartesi-Pazar). Her gun somut aday isimleri + eylem. Oncelikliler hafta basina.
Her gune TARIH ekle (gg.aa.yyyy formatinda, bugunden baslayarak).
Son notu OLUMSUZ olan adaylari ("ilgilenmedi", "olumsuz", "reddetti") plana EKLEME.
Once FIRSAT adaylarindan basla, sonra riskli adaylara gec.

**4. Gozden Kacan Firsatlar**
Huni verisinde anomali veya firsat var mi?

YAZIM KURALLARI (ZORUNLU):
- "fırsat" yaz (fırst degil)
- "müsait" yaz (musait degil)
- "teşekkür" yaz (tesekkur degil)
- "görüşme" yaz (gorusme degil)
- Tum cumlelerde Turkce karakterleri DOGRU kullan.

# KURALLAR (IHALAL EDILEMEZ)
1. SADECE TURKCE. Tek kelime bile Ingilizce/Cince YAZMA.
2. Rakam UYDURMA, verilen rakamlari kullan.
3. Aday isimlerini notlardan al, uydurma.
4. HALUSINASYON YASAGI: "gecen gorusmemizde", "onceki konusmamizda", "bahsettigimiz gibi" gibi ifadeler SADECE notta ACIKCA yaziyorsa kullanilabilir. Emin degilsen KULLANMA. Notta "gorusulmedi" yaziyorsa HIC KULLANMA.
5. Somut ol. "Iletisime gec" yerine NE SOYLEYECEGINI yaz.
6. LaTeX/Markdown matematik YASAK.
7. Toplam 25-35 satir.
8. YAZIM KONTROLU: yarinrandaki yerine yarinki, firsa yerine firsat, musait yerine müsait, gorusmeme yerine gorusmeye. Nokta-virgul karistirma."""

    try:
        metin = ""
        for parca in chat_stream([{"role": "user", "content": prompt}],
                                  model=DEFAULT_MODEL, fallback=DEFAULT_FALLBACK,
                                  profil="analiz"):
            metin += parca
        return jsonify({"ozet": metin.strip(), "huni": h})
    except Exception as e:
        return jsonify({"ozet": f"Strateji oluşturulamadı: {e}"}), 500


@bp.route("/hatirlatmalar", methods=["GET"])
def hatirlatmalar():
    """v11: 4 asamali randevu bildirim listesi."""
    from core.database import randevu_hatirlatmalari_getir
    return jsonify(randevu_hatirlatmalari_getir())

