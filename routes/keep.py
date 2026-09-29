"""Keep'ten aday aktarma."""
from flask import Blueprint, jsonify, request
from datetime import datetime
from core.database import aday_ekle
from core.excel_io import _satir_hash

bp = Blueprint("keep", __name__, url_prefix="/api/keep")


def _parse_keep(metin):
    """Keep notunu parse eder. Format: • [🟡/🟢] İsim: Açıklama"""
    adaylar = []
    satirlar = metin.split("\n")

    for satir in satirlar:
        satir = satir.strip()

        # Boş veya başlık satırlarını atla
        if not satir or not satir.startswith("•"):
            continue

        # • işaretini kaldır
        satir = satir.lstrip("•").strip()

        # Renk tespiti
        durum = "belirsiz"
        for emoji, d in [("🟡", "sarı"), ("🟨", "sarı"),
                         ("🟢", "yeşil"), ("🟩", "yeşil"),
                         ("🔴", "kırmızı"), ("🟥", "kırmızı"),
                         ("🟠", "turuncu"), ("🟧", "turuncu")]:
            if emoji in satir:
                durum = d
                satir = satir.replace(emoji, "").strip()
                break

        # İsim: Açıklama ayır
        if ":" in satir:
            parcalar = satir.split(":", 1)
            isim = parcalar[0].strip()
            aciklama = parcalar[1].strip() if len(parcalar) > 1 else ""
        else:
            isim = satir
            aciklama = ""

        if not isim:
            continue

        adaylar.append({
            "isim": isim,
            "aciklama": aciklama,
            "durum": durum
        })

    return adaylar


@bp.route("/parse", methods=["POST"])
def parse():
    """Keep metnini parse eder (DB'ye eklemez), önizleme döner."""
    d = request.get_json() or {}
    metin = d.get("metin", "").strip()

    if not metin:
        return jsonify({"ok": False, "error": "Metin boş"}), 400

    adaylar = _parse_keep(metin)

    # Renk dağılımı
    yesil = sum(1 for a in adaylar if a["durum"] == "yeşil")
    sari = sum(1 for a in adaylar if a["durum"] == "sarı")

    return jsonify({
        "ok": True,
        "adaylar": adaylar,
        "toplam": len(adaylar),
        "yesil": yesil,
        "sari": sari
    })


@bp.route("/import", methods=["POST"])
def import_route():
    """Keep metnini parse eder ve DB'ye ekler."""
    d = request.get_json() or {}
    metin = d.get("metin", "").strip()

    if not metin:
        return jsonify({"ok": False, "error": "Metin boş"}), 400

    adaylar = _parse_keep(metin)

    if not adaylar:
        return jsonify({
            "ok": False,
            "error": "Hiç aday bulunamadı. Format: • [🟡/🟢] İsim: Açıklama"
        }), 400

    bugun = datetime.now().strftime("%d %m %y")
    eklenen = 0
    atlanan = 0

    for a in adaylar:
        # Açıklamaya durum emojisi ekle
        aciklama = a["aciklama"]
        if a["durum"] != "belirsiz":
            emoji = {"yeşil": "🟢", "sarı": "🟡", "kırmızı": "🔴", "turuncu": "🟠"}.get(a["durum"], "")
            aciklama = f"{emoji} {aciklama}"

        h = _satir_hash(a["isim"], bugun, aciklama)
        ok = aday_ekle(
            a["isim"], bugun, aciklama,
            0, 0, 0, 0, 0, 0,
            1,  # is_ariyor = 1 (Keep'ten gelenler iş arıyor)
            kaynak_hash=h
        )
        if ok:
            eklenen += 1
        else:
            atlanan += 1

    return jsonify({
        "ok": True,
        "eklenen": eklenen,
        "atlanan": atlanan,
        "mesaj": f"{eklenen} yeni aday eklendi, {atlanan} zaten mevcuttu"
    })
