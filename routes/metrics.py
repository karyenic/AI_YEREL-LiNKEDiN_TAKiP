from flask import Blueprint, jsonify
import pandas as pd
from datetime import datetime
from core.database import adaylari_getir
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
    """Randevusu/plani olup kayit veya red almamis, en uzun suredir
    temassiz kalan adaylar - 'olasilik dusuren' somut sinyal.
    Tarih formati tutarsiz olabilecegi icin pd.to_datetime ile esnek parse."""
    aktif = [
        a for a in adaylar
        if not int(a.get('kayit') or 0) and not int(a.get('hayir') or 0)
    ]
    for a in aktif:
        a['_tarih_dt'] = pd.to_datetime(a.get('tarih'), dayfirst=True, errors='coerce')

    gecerli = [a for a in aktif if pd.notna(a['_tarih_dt'])]
    gecerli.sort(key=lambda a: a['_tarih_dt'])

    bugun = pd.Timestamp.now()
    sonuc = []
    for a in gecerli[:limit]:
        gun = (bugun - a['_tarih_dt']).days
        sonuc.append({
            "isim": a.get("isim", "?"),
            "gun_sayisi": int(gun),
            "asama": ("plan" if a.get('plan') else
                      "randevu" if a.get('randevu') else
                      "davet" if a.get('davet') else "kaba liste"),
        })
    return sonuc


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

    riskli_satir = "\n".join(
        f"  - {r['isim']}: {r['gun_sayisi']} gündür temassız (aşama: {r['asama']})"
        for r in riskli
    ) or "  (temassızlık verisi yok)"

    bugun_str = datetime.now().strftime("%Y-%m-%d (%A)")

    prompt = f"""# ROLE
You are a network-marketing recruiting pipeline strategist. The business goal is NOT just "more invites" — it is moving people through: kaba liste (raw list) -> davet (invited) -> randevu (meeting set, 1:1 or Zoom) -> plan (business plan presented) -> kayit (registered) -> başlatma toplantısı (kickoff meeting). Once someone registers AND has their kickoff meeting, they stop being a "candidate" and become a business partner.

# VERIFIED FUNNEL DATA (bugün: {bugun_str}) — bu rakamlar kesindir, yeniden hesaplama, sadece yorumla
Toplam kaba liste: {h['toplam']}
Davet: {h['davet']}  (kaba listeden davete dönüşüm: %{h['oran_kabadan_davete']})
Randevu: {h['randevu']}  (davetten randevuya dönüşüm: %{h['oran_davetten_randevuya']})
Plan sunumu: {h['plan']}  (randevudan plana dönüşüm: %{h['oran_randevudan_plana']})
Kayıt: {h['kayit']}  (plandan kayda dönüşüm: %{h['oran_plandan_kayda']})
Uçtan uca (kaba listeden kayda) genel başarı oranı: %{h['oran_uctan_uca']}
Red (hayır) oranı: %{h['oran_red']}
Hâlâ süreçte olan (ne kayıt ne red): {h['aktif_takipte']}

# EN UZUN SÜREDİR TEMASSIZ KALAN ADAYLAR (öncelik sinyali — kesin veri)
{riskli_satir}

# TASK
In TURKISH, produce exactly three short sections:

1. **Huni Durumu** — Hangi adımda darboğaz var (en düşük dönüşüm oranına sahip adım) tek-iki cümle, rakamlarla.
2. **Öncelikli Adaylar (Olasılık Değerlendirmesi)** — Yukarıdaki temassızlık listesinden somut isimlerle, hangisiyle NEDEN şimdi ilgilenilmeli (örn. "X, randevu aşamasında 9 gündür temassız — sıcaklığı kaybetme riski yüksek, bugün aranmalı").
3. **Haftalık İletişim Planı** — 7 güne yayılmış, somut ve kısa bir öneri (örn. "Pazartesi: risk listesindeki ilk 3 kişiye takip mesajı, Çarşamba: randevusu olup plan sunumu yapılmamışlara hatırlatma...").

Be concise and decision-ready — toplam 10-12 satırı geçme. Rakam uydurma, sadece yukarıdaki verilen rakamları kullan. No markdown headers beyond the three bold section titles above."""

    try:
        metin = ""
        for parca in chat_stream([{"role": "user", "content": prompt}],
                                  model=DEFAULT_MODEL, fallback=DEFAULT_FALLBACK):
            metin += parca
        return jsonify({"ozet": metin.strip(), "huni": h})
    except Exception as e:
        return jsonify({"ozet": f"Strateji oluşturulamadı: {e}"}), 500
