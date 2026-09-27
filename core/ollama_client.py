import ollama
import time
import psutil
from config import (MODEL_CONTEXT_MAP, DEFAULT_NUM_CTX, KEEP_ALIVE,
                    DEFAULT_MODEL, DEFAULT_FALLBACK)

_warmed_models = set()


def _get_num_ctx(model_adi):
    """Model bazli akilli num_ctx dondurur."""
    return MODEL_CONTEXT_MAP.get(model_adi, DEFAULT_NUM_CTX)


def warm_up(model_adi=DEFAULT_MODEL):
    """Modeli VRAM e yukler. Uygulama acilisinda bir kere cagrilir."""
    if model_adi in _warmed_models:
        return True
    try:
        num_ctx = _get_num_ctx(model_adi)
        print(f"Warm-up: {model_adi} (num_ctx: {num_ctx})")
        ollama.chat(
            model=model_adi,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_ctx": num_ctx, "num_predict": 1},
            keep_alive=KEEP_ALIVE
        )
        _warmed_models.add(model_adi)
        print(f"OK: {model_adi} VRAM e yuklendi")
        return True
    except Exception as e:
        print(f"UYARI: Warm-up hatasi ({model_adi}): {e}")
        return False


def _sistem_prompt(df_ozet):
    return f"""# ROLE
You are the dedicated AI Operations Analyst embedded inside a LinkedIn candidate-tracking (ATS) desktop tool. You are not a general chatbot - you exist only to interpret the candidate table below and support the recruiter decisions.

# DATA CONTRACT (READ CAREFULLY)
Below is the CURRENT, COMPLETE snapshot of the candidate database. It is your only source of truth.
```
{df_ozet}
```
Columns you may see: isim (name), tarih (date), aciklama (notes), davet (invited), randevu (meeting set), plan (business plan presented), kayit (registered), takip (follow-up), hayir (declined), is_ariyor (actively job-seeking).
Boolean-style columns are 1 (yes/happened) or 0 (no/not yet).

# HARD RULES (NON-NEGOTIABLE)
1. GROUNDING: Every factual claim about a candidate MUST be traceable to a row in the table above.
2. NO SILENT GUESSING: If the requested information is not derivable from the table, say "Bu bilgi elimdeki veride yok" instead of guessing.
3. NUMBERS ARE EXACT: When asked for counts or percentages, compute them precisely.
4. NO FABRICATED CONTACT INFO: Never invent phone numbers, emails, or links.
5. SCOPE: You do not answer general knowledge, coding, or unrelated questions.

# WHAT YOU ARE GOOD FOR
- Funnel analysis: invite -> meeting -> plan -> registration conversion rates.
- Flagging candidates stuck at a stage too long.
- Prioritization: which candidates to follow up with today.
- Short, decision-ready summaries.

# OUTPUT STYLE
- Be concise and structured (short paragraphs or bullet lists).
- When making a recommendation, always name the specific candidate(s).

# LANGUAGE - MANDATORY
Regardless of what language the user writes in, your ENTIRE reply must be in fluent, natural, professional Turkish."""


def chat_stream(mesajlar, model=DEFAULT_MODEL, fallback=DEFAULT_FALLBACK, durum=None):
    """Generator: Ollama dan gelen chunk lari yield eder. Fallback li."""
    if durum is None:
        durum = {}
    durum["model"] = model
    durum["fallback"] = False

    def _deneme(m):
        t0 = time.time()
        num_ctx = _get_num_ctx(m)
        print(f"{m} cagriliyor (num_ctx: {num_ctx})...")
        full = ollama.chat(
            model=m,
            messages=mesajlar,
            options={"num_ctx": num_ctx},
            keep_alive=KEEP_ALIVE,
            stream=True
        )
        ilk = True
        for chunk in full:
            if ilk:
                print(f"{m} ilk token: {time.time()-t0:.1f}sn")
                ilk = False
            yield chunk["message"]["content"]

    try:
        yield from _deneme(model)
    except Exception as e:
        print(f"{model} hata verdi, fallback: {fallback} ({e})")
        durum["fallback"] = True
        durum["model"] = fallback
        yield f"\n\n*(Not: {model} yanit vermedigi icin {fallback} ile yanitlaniyor)*\n\n"
        try:
            yield from _deneme(fallback)
        except Exception as e2:
            yield f"\n\nFallback de basarisiz: {e2}"


def sistem_mesaji_olustur(df_ozet):
    return {"role": "system", "content": _sistem_prompt(df_ozet)}


def _alan(obj, ad, varsayilan=None):
    """dict veya pydantic-tarzi objeden guvenli alan okuma."""
    if obj is None:
        return varsayilan
    if hasattr(obj, "get"):
        try:
            v = obj.get(ad, varsayilan)
            if v is not None:
                return v
        except Exception:
            pass
    return getattr(obj, ad, varsayilan)


def durum_ozeti():
    """Nav daki durum pili icin: Ollama ayakta mi, hangi model VRAM de?"""
    try:
        ps = ollama.ps()
        modeller = _alan(ps, "models", []) or []
        sonuc = []
        for m in modeller:
            sonuc.append({
                "name": _alan(m, "model") or _alan(m, "name"),
                "size": _alan(m, "size"),
                "vram": _alan(m, "size_vram", 0) or 0,
                "until": str(_alan(m, "expires_at", "")) or "",
            })
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
        except Exception:
            cpu_pct = None
        return {
            "ok": True,
            "models": sonuc,
            "cpu_percent": cpu_pct,
            "gpu_aktif": len(sonuc) > 0,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "models": [], "cpu_percent": None, "gpu_aktif": False}