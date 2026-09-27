from flask import Blueprint, jsonify
from core.database import adaylari_getir

bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")


@bp.route("", methods=["GET"])
def hesapla():
    adaylar = adaylari_getir()
    if not adaylar:
        return jsonify({"toplam": 0})

    toplam = len(adaylar)
    def s(k):
        return sum(int(a.get(k) or 0) for a in adaylar)

    davet, randevu, plan = s('davet'), s('randevu'), s('plan')
    kayit, takip, hayir = s('kayit'), s('takip'), s('hayir')
    is_ariyor = s('is_ariyor')

    return jsonify({
        "toplam": toplam,
        "davet": davet, "randevu": randevu, "plan": plan,
        "kayit": kayit, "takip": takip, "hayir": hayir,
        "is_ariyor": is_ariyor,
        "davet_randevu_oran": round(randevu / davet * 100, 1) if davet else 0,
        "plan_kayit_oran": round(kayit / plan * 100, 1) if plan else 0,
    })