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

        # -- YENI v10 FINAL: iki BAGIMSIZ liste (email / telefon) --
        _tel_s, _mail_s, _adres_s, _bos_s = 0, 0, 0, 0
        _email_liste = []
        _tel_liste = []
        try:
            _conn_c = sqlite3.connect(str(ADAY_DB))
            _conn_c.row_factory = sqlite3.Row
            _c_c = _conn_c.cursor()
            _p_rows = _c_c.execute(
                "SELECT isim, telefon, email, adres FROM aday_profil ORDER BY isim"
            ).fetchall()
            for _p in _p_rows:
                _n = (_p["isim"] or "").strip()
                _t = (_p["telefon"] or "").strip()
                _m = (_p["email"] or "").strip()
                _a = (_p["adres"] or "").strip()
                if _t: _tel_s += 1
                if _m: _mail_s += 1
                if _a: _adres_s += 1
                if not (_t or _m or _a): _bos_s += 1
                if _m:
                    _ek = f" | ayrica tel: {_t}" if _t else ""
                    _email_liste.append(f"{_n} ({_m}){_ek}")
                if _t:
                    _ek = f" | ayrica email: {_m}" if _m else ""
                    _tel_liste.append(f"{_n} ({_t}){_ek}")
            _conn_c.close()
        except Exception as _e:
            print(f"[UYARI] Iletisim ozeti okunamadi: {_e}")

        basliklar.append("")
        basliklar.append("=== TUM EMAILI OLANLAR (bagimsiz liste) ===")
        for _x in _email_liste: basliklar.append(f"  - {_x}")
        basliklar.append("")
        basliklar.append("=== TUM TELEFONU OLANLAR (bagimsiz liste) ===")
        for _x in _tel_liste: basliklar.append(f"  - {_x}")
        basliklar.append("")
        basliklar.append("=== TOPLAM SAYILAR (onceden hesaplandi) ===")
        basliklar.append(f"  Email kayitli TOPLAM: {_mail_s}")
        basliklar.append(f"  Telefon kayitli TOPLAM: {_tel_s}")
        basliklar.append(f"  Adres kayitli TOPLAM: {_adres_s}")
        basliklar.append(f"  Hic iletisim bilgisi olmayan: {_bos_s}")

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
                    _tel = (kart.get("telefon") or "").strip()
                    _mail = (kart.get("email") or "").strip()
                    _parcalar = []
                    if _tel: _parcalar.append(f"Tel:{_tel}")
                    if _mail: _parcalar.append(f"Mail:{_mail}")
                    _ek = (" " + " ".join(_parcalar)) if _parcalar else ""
                    satirlar.append(f"{i}. {isim} [{durum}]{_ek}")
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