from flask import Blueprint, jsonify, request

from core.database import (
    adaylari_getir,
    aday_ekle,
    aday_sil,
    tum_adaylari_sil,
    aday_karti_getir,
    aday_profil_guncelle,
    aday_gelisme_ekle
)

bp = Blueprint(
    "candidates",
    __name__,
    url_prefix="/api/candidates"
)


@bp.route("", methods=["GET"])
def listele():
    return jsonify(adaylari_getir())


@bp.route("", methods=["POST"])
def ekle():
    d = request.get_json() or {}

    ok = aday_ekle(
        d.get("isim", ""),
        d.get("tarih", ""),
        d.get("aciklama", ""),
        d.get("davet", 0),
        d.get("randevu", 0),
        d.get("plan", 0),
        d.get("kayit", 0),
        d.get("takip", 0),
        d.get("hayir", 0),
        d.get("is_ariyor", 0),
        linkedin_url=d.get("linkedin_url", None)
    )

    return jsonify({"ok": ok})


@bp.route("/<int:aday_id>", methods=["GET"])
def kart(aday_id):
    data = aday_karti_getir(aday_id)

    if data is None:
        return jsonify({
            "ok": False,
            "error": "Aday bulunamadı."
        }), 404

    return jsonify({
        "ok": True,
        "data": data
    })


@bp.route("/<int:aday_id>/profil", methods=["PUT"])
def profil_guncelle(aday_id):
    d = request.get_json() or {}

    ok = aday_profil_guncelle(
        aday_id,
        d.get("telefon", ""),
        d.get("email", ""),
        d.get("adres", "")
    )

    if not ok:
        return jsonify({
            "ok": False,
            "error": "Aday profili bulunamadı."
        }), 404

    return jsonify({
        "ok": True,
        "message": "Aday bilgileri güncellendi."
    })


@bp.route("/<int:aday_id>/gelisme", methods=["POST"])
def gelisme_ekle(aday_id):
    d = request.get_json() or {}

    tarih = str(d.get("tarih", "")).strip()
    olay_tipi = str(d.get("olay_tipi", "Not")).strip()
    olay_metni = str(d.get("olay_metni", "")).strip()
    durum = str(d.get("durum", "")).strip()

    if not olay_metni:
        return jsonify({
            "ok": False,
            "error": "Gelişme açıklaması boş bırakılamaz."
        }), 400

    ok, msg = aday_gelisme_ekle(
        aday_id,
        tarih,
        olay_tipi,
        olay_metni,
        durum
    )

    if not ok:
        return jsonify({
            "ok": False,
            "error": msg
        }), 404

    return jsonify({
        "ok": True,
        "message": msg
    })


@bp.route("/<int:aday_id>", methods=["DELETE"])
def sil(aday_id):
    aday_sil(aday_id)
    return jsonify({"ok": True})


@bp.route("/hepsi", methods=["DELETE"])
def hepsini_sil():
    tum_adaylari_sil()
    return jsonify({"ok": True})



@bp.route("/<int:aday_id>/linkedin", methods=["PUT"])
def linkedin_guncelle(aday_id):
    """Adayin LinkedIn URL'sini gunceller."""
    from core.database import aday_linkedin_guncelle
    d = request.get_json() or {}
    linkedin_url = str(d.get("linkedin_url", "")).strip()

    if not linkedin_url:
        return jsonify({"ok": False, "error": "URL bos olamaz."}), 400

    ok = aday_linkedin_guncelle(aday_id, linkedin_url)

    if not ok:
        return jsonify({"ok": False, "error": "Aday bulunamadi."}), 404

    return jsonify({"ok": True, "message": "LinkedIn URL guncellendi."})
