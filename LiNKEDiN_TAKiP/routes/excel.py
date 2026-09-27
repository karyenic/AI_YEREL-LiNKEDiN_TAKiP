from flask import Blueprint, jsonify, send_file
import io
from core.excel_io import excel_disa_aktar, excel_ice_aktar
from config import IZLENEN_EXCEL

bp = Blueprint("excel", __name__, url_prefix="/api/excel")


@bp.route("/import", methods=["POST"])
def import_route():
    """Elle tetiklenen içe aktarma - watcher'ı beklemeden mevcut dosyayı okur."""
    if not IZLENEN_EXCEL.exists():
        return jsonify({"ok": False, "msg": f"Dosya bulunamadı: {IZLENEN_EXCEL}"}), 404
    ok, msg = excel_ice_aktar(IZLENEN_EXCEL)
    return jsonify({"ok": ok, "msg": msg})


@bp.route("/export", methods=["GET"])
def export():
    data = excel_disa_aktar()
    if data is None:
        return jsonify({"error": "Veri yok"}), 404
    return send_file(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="linkedin_adaylar.xlsx"
    )