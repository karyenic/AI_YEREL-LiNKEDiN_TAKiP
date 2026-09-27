from flask import Blueprint, jsonify, request, Response
import json
import pandas as pd
from core.database import chat_mesajlari_getir, chat_mesaj_ekle, chat_temizle, adaylari_getir
from core.ollama_client import chat_stream, sistem_mesaji_olustur

bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.route("/gecmis", methods=["GET"])
def gecmis():
    return jsonify(chat_mesajlari_getir())


@bp.route("/temizle", methods=["POST"])
def temizle_route():
    chat_temizle()
    return jsonify({"ok": True})


@bp.route("/stream", methods=["POST"])
def stream():
    d = request.get_json() or {}
    kullanici_mesaji = d.get("mesaj", "").strip()
    model = d.get("model")
    fallback = d.get("fallback")

    if not kullanici_mesaji:
        return jsonify({"error": "Mesaj bos"}), 400

    # Kullanici mesajini kaydet
    chat_mesaj_ekle("user", kullanici_mesaji)

    # DB ozetini hazirla - MODELIN SAYMASINI ENGELLE
    adaylar = adaylari_getir()
    if adaylar:
        df = pd.DataFrame(adaylar)
        cols = ["isim", "tarih", "aciklama", "davet", "randevu",
                "plan", "kayit", "takip", "hayir", "is_ariyor"]
        cols = [c for c in cols if c in df.columns]
        toplam = len(df)

        def _s(k):
            try:
                return int(df[k].fillna(0).sum())
            except Exception:
                return 0

        basliklar = [
            f"TOPLAM ADAY: {toplam}",
            f"Davet: {_s('davet')} | Randevu: {_s('randevu')} | Plan: {_s('plan')} | Kayit: {_s('kayit')}",
            f"Takip: {_s('takip')} | Hayir: {_s('hayir')} | Is ariyor: {_s('is_ariyor')}",
            "",
            f"DETAYLI LISTE ({toplam} aday):",
        ]
        df_ozet = "\n".join(basliklar) + "\n" + df[cols].to_string(index=False)
    else:
        df_ozet = "(Veritabani bos)"

    # Mesaj gecmisini olustur
    gecmis = chat_mesajlari_getir()
    ollama_msgs = [sistem_mesaji_olustur(df_ozet)]
    for m in gecmis:
        ollama_msgs.append({"role": m["role"], "content": m["content"]})

    def generate():
        toplam_yanit = ""
        durum = {}
        kesildi = False
        try:
            for parca in chat_stream(ollama_msgs, model=model, fallback=fallback, durum=durum):
                toplam_yanit += parca
                yield f"data: {json.dumps({'t': parca}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'model': durum.get('model'), 'fallback': durum.get('fallback', False)}, ensure_ascii=False)}\n\n"
        except GeneratorExit:
            kesildi = True
            raise
        except Exception as e:
            yield f"data: {json.dumps({'err': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            if toplam_yanit and not kesildi:
                chat_mesaj_ekle("assistant", toplam_yanit, model=durum.get("model"), fallback=durum.get("fallback", False))

    return Response(generate(), mimetype="text/event-stream")
