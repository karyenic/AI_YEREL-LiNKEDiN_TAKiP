import ollama
import time
import psutil
from config import NUM_CTX, KEEP_ALIVE, DEFAULT_MODEL, DEFAULT_FALLBACK

_warmed_models = set()


def warm_up(model_adi=DEFAULT_MODEL):
    """Modeli VRAM'e yükler. Uygulama açılışında bir kere çağrılır."""
    if model_adi in _warmed_models:
        return True
    try:
        ollama.chat(
            model=model_adi,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_ctx": NUM_CTX, "num_predict": 1},
            keep_alive=KEEP_ALIVE
        )
        _warmed_models.add(model_adi)
        print(f"✅ {model_adi} VRAM'e yüklendi")
        return True
    except Exception as e:
        print(f"⚠️ Warm-up hatası ({model_adi}): {e}")
        return False


def _sistem_prompt(df_ozet):
    return f"""# ROLE
You are the dedicated AI Operations Analyst embedded inside a LinkedIn candidate-tracking (ATS) desktop tool. You are not a general chatbot — you exist only to interpret the candidate table below and support the recruiter's decisions.

# DATA CONTRACT (READ CAREFULLY)
Below is the CURRENT, COMPLETE snapshot of the candidate database. It is your only source of truth.
```
{df_ozet}
```
Columns you may see: isim (name), tarih (date), aciklama (notes), davet (invited), randevu (meeting set), plan (business plan presented), kayit (registered), takip (follow-up), hayir (declined), is_ariyor (actively job-seeking).
Boolean-style columns are 1 (yes/happened) or 0 (no/not yet).

# HARD RULES (NON-NEGOTIABLE)
1. GROUNDING: Every factual claim about a candidate MUST be traceable to a row in the table above. If the table is empty or a name isn't in it, say so explicitly — never invent a candidate, a date, or a status.
2. NO SILENT GUESSING: If the requested information isn't derivable from the table, say "Bu bilgi elimdeki veride yok" (or the exact reason) instead of guessing.
3. NUMBERS ARE EXACT: When asked for counts, percentages or funnel stages, compute them precisely from the rows shown — do not round narratively or approximate.
4. NO FABRICATED CONTACT INFO: Never invent phone numbers, emails, or links not present in the data.
5. SCOPE: You do not answer general knowledge, coding, or unrelated questions. If asked something outside candidate-tracking/recruiting analysis, politely redirect to your actual purpose in one sentence.

# WHAT YOU'RE GOOD FOR
- Funnel analysis: invite → meeting → plan → registration conversion rates.
- Flagging candidates stuck at a stage too long, or contradictory statuses (e.g. "kayit=1" but "davet=0").
- Prioritization: which candidates to follow up with today, and why (grounded in their row).
- Short, decision-ready summaries — not essays.

# OUTPUT STYLE
- Be concise and structured (short paragraphs or bullet lists), not verbose.
- When making a recommendation, always name the specific candidate(s) it applies to.
- If the data is insufficient for a solid recommendation, say so instead of padding the answer.

# LANGUAGE — MANDATORY
Regardless of what language the user writes in, your ENTIRE reply must be in fluent, natural, professional Turkish. Never reply in English."""


def chat_stream(mesajlar, model=DEFAULT_MODEL, fallback=DEFAULT_FALLBACK, durum=None):
    """Generator: Ollama'dan gelen chunk'ları yield eder. Fallback'li.
    durum: çağıran taraf {} verirse, gerçekte hangi modelin kullanıldığını
    ve fallback'e düşülüp düşülmediğini buraya yazarız (rozet/DB için)."""
    if durum is None:
        durum = {}
    durum["model"] = model
    durum["fallback"] = False

    def _deneme(m):
        t0 = time.time()
        print(f"🔄 {m} çağrılıyor...")
        full = ollama.chat(
            model=m,
            messages=mesajlar,
            options={"num_ctx": NUM_CTX},
            keep_alive=KEEP_ALIVE,
            stream=True
        )
        ilk = True
        for chunk in full:
            if ilk:
                print(f"✅ {m} ilk token: {time.time()-t0:.1f}sn")
                ilk = False
            yield chunk['message']['content']

    try:
        yield from _deneme(model)
    except Exception as e:
        print(f"⚠️ {model} hata verdi, fallback: {fallback} ({e})")
        durum["fallback"] = True
        durum["model"] = fallback
        yield f"\n\n*(Not: {model} yanıt vermediği için {fallback} ile yanıtlanıyor)*\n\n"
        try:
            yield from _deneme(fallback)
        except Exception as e2:
            yield f"\n\n⚠️ Fallback de başarısız: {e2}"


def sistem_mesaji_olustur(df_ozet):
    return {"role": "system", "content": _sistem_prompt(df_ozet)}


def _alan(obj, ad, varsayilan=None):
    """dict veya pydantic-tarzı SubscriptableBaseModel'den güvenli alan okuma."""
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
    """Nav'daki durum pili için: Ollama ayakta mı, hangi model VRAM'de?
    NOT: ollama python paketi (>=0.2) ps()'ten düz dict değil, pydantic-tarzı
    bir obje döndürür - isinstance(x, dict) hep False'tur, bu yüzden hem
    .get() hem getattr() ile deniyoruz."""
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
        # NOT: Intel/IPEX backend /api/ps üzerinden gerçek VRAM kullanımını
        # raporlamıyor (CUDA/ROCm'e özgü bir alan). Bu yüzden "GPU aktif mi"
        # sorusunu, en az bir model VRAM'de/yüklüyse GPU offload'un devrede
        # olduğunu varsayarak cevaplıyoruz (Baslat.bat IPEX exe'siyle
        # başlatıldığı sürece bu doğrudur). Gerçek canlı % kullanım için
        # Windows GPU Engine sayaçlarının okunması gerekir - ayrı bir iş.
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