from flask import Blueprint, jsonify, request
from core.database import adaylari_getir, aday_ekle, aday_sil, tum_adaylari_sil

bp = Blueprint("candidates", __name__, url_prefix="/api/candidates")


@bp.route("", methods=["GET"])
def listele():
    return jsonify(adaylari_getir())


@bp.route("", methods=["POST"])
def ekle():
    d = request.get_json() or {}
    ok = aday_ekle(
        d.get("isim", ""), d.get("tarih", ""), d.get("aciklama", ""),
        d.get("davet", 0), d.get("randevu", 0), d.get("plan", 0),
        d.get("kayit", 0), d.get("takip", 0), d.get("hayir", 0),
        d.get("is_ariyor", 0)
    )
    return jsonify({"ok": ok})


@bp.route("/<int:aday_id>", methods=["DELETE"])
def sil(aday_id):
    aday_sil(aday_id)
    return jsonify({"ok": True})


@bp.route("/hepsi", methods=["DELETE"])
def hepsini_sil():
    tum_adaylari_sil()
    return jsonify({"ok": True})