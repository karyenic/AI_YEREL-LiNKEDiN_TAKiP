import sqlite3
from flask import Blueprint, jsonify, request, Response
import json
import pandas as pd
from core.database import (chat_mesajlari_getir, chat_mesaj_ekle, chat_temizle,
                          adaylari_getir, aday_karti_getir)
from core.ollama_client import chat_stream, sistem_mesaji_olustur
from config import (ADAY_OLAY_LIMIT, ADAY_PROMPT_LIMIT, DEFAULT_MODEL,
                    DEFAULT_FALLBACK, PRIMARY_MODELS, ADAY_DB, ADAY_STATULERI)

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
    # NOT: "fallback" frontend'den hic gonderilmiyor, bu yuzden None kalirdi.
    # None, chat_stream icinde ikinci modele dusulurken pydantic hatasiyla
    # cokerdi - "or DEFAULT_FALLBACK" ile garanti altina aliyoruz.
    #
    # v7 4C-BUG: Frontend bazen model="otomatik" gonderir. Bu ad Ollama'da
    # model olmadigi icin "model not found" hatasi cikar ve 7b'ye dusulur.
    # Whitelist kontrolu ile bilinmeyen adlar DEFAULT_MODEL'a cevrilir.
    model_ham = (d.get("model") or "").strip()
    if model_ham in PRIMARY_MODELS:
        model = model_ham
    else:
        model = DEFAULT_MODEL
        if model_ham and model_ham not in ("", "otomatik", "auto", "default"):
            print(f"[MODEL] Bilinmeyen model '{model_ham}' -> '{DEFAULT_MODEL}'")

    fallback = d.get("fallback") or DEFAULT_FALLBACK
    if fallback not in PRIMARY_MODELS:
        fallback = DEFAULT_FALLBACK

    if not kullanici_mesaji:
        return jsonify({"error": "Mesaj bos"}), 400

    # Kullanici mesajini kaydet
    chat_mesaj_ekle("user", kullanici_mesaji)

    # DB ozetini hazirla - istatistikler + her adayin son olaylari
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

        # v8 4D: Statu-merkezli ozet (UI ile birebir uyumlu)
        statu_sayilari = {}
        for _s_item in ADAY_STATULERI:
            statu_sayilari[_s_item["tam"]] = 0
        statu_sayilari["(durum yok)"] = 0

        try:
            _conn_s = sqlite3.connect(str(ADAY_DB))
            _conn_s.row_factory = sqlite3.Row
            _c_s = _conn_s.cursor()
            _rows_s = _c_s.execute(
                "SELECT durum, COUNT(*) AS adet FROM aday_profil GROUP BY durum"
            ).fetchall()
            for _r in _rows_s:
                _d = (_r["durum"] or "").strip()
                if _d in statu_sayilari:
                    statu_sayilari[_d] += _r["adet"]
                else:
                    statu_sayilari["(durum yok)"] += _r["adet"]
            _conn_s.close()
        except Exception as _e:
            print(f"[UYARI] Statu dagilimi okunamadi: {_e}")

        _blok_sayisi = 0
        _toplam_gorunur = toplam
        try:
            _conn_b = sqlite3.connect(str(ADAY_DB))
            _c_b = _conn_b.cursor()
            _blok_sayisi = _c_b.execute(
                "SELECT COUNT(*) FROM adaylar WHERE COALESCE(blok,0)=1"
            ).fetchone()[0]
            _toplam_gorunur = _c_b.execute(
                "SELECT COUNT(*) FROM adaylar WHERE COALESCE(blok,0)=0"
            ).fetchone()[0]
            _conn_b.close()
        except Exception:
            pass

        basliklar = [
            f"TOPLAM ADAY: {_toplam_gorunur} (bloklular haric)",
            "STATU DAGILIMI:",
        ]
        for _s_item in ADAY_STATULERI:
            if _s_item["kod"] == "blok":
                continue
            basliklar.append(
                f"  {_s_item['tam']}: {statu_sayilari.get(_s_item['tam'], 0)}"
            )
        basliklar.append(f"  (Blok: {_blok_sayisi} - gizli)")
        basliklar.append("")
        basliklar.append(
            f"DETAYLI LISTE (ilk {ADAY_PROMPT_LIMIT} aday, son gelismeleriyle):"
        )

        # Her aday icin son N olayi ekle
        satirlar = []
        for i, aday in enumerate(df.head(ADAY_PROMPT_LIMIT).to_dict("records"), 1):
            isim = aday.get("isim", "?")
            try:
                kart = aday_karti_getir(aday.get("id"))
                if kart and kart.get("gecmis"):
                    durum = kart.get("durum", "Aktif")
                    satirlar.append(f"{i}. {isim} (durum: {durum})")
                    for olay in kart["gecmis"][-ADAY_OLAY_LIMIT:]:
                        tarih = olay.get("tarih", "")
                        tip = olay.get("olay_tipi", "")
                        metin = olay.get("olay_metni", "")
                        metin_kisa = metin[:120] + ("..." if len(metin) > 120 else "")
                        satirlar.append(f"   - {tarih} [{tip}]: {metin_kisa}")
                else:
                    satirlar.append(f"{i}. {isim}")
            except Exception:
                satirlar.append(f"{i}. {isim}")

        df_ozet = "\n".join(basliklar) + "\n" + "\n".join(satirlar)
    else:
        df_ozet = "(Veritabani bos)"

    # Mesaj gecmisini olustur
    gecmis = chat_mesajlari_getir()
    # Son 6 mesaj (3 soru + 3 cevap) - KV cache kirlenmesini onler
    son_gecmis = gecmis[-6:] if len(gecmis) > 6 else gecmis
    ollama_msgs = [sistem_mesaji_olustur(df_ozet)]
    for m in son_gecmis:
        ollama_msgs.append({"role": m["role"], "content": m["content"]})

    def generate():
        toplam_yanit = ""
        durum = {}
        kesildi = False
        try:
            # Router: soru tipine gore model sec
            model_secili = model if model else DEFAULT_MODEL  # Frontend'den gelen veya default
            for parca in chat_stream(ollama_msgs, model=model_secili, fallback=fallback, durum=durum, profil="analiz"):
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