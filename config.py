from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Veritabanlari
ADAY_DB = DATA_DIR / "linkedin_takip.db"
CHAT_DB = DATA_DIR / "sohbet_gecmisi.db"

# Izlenen Excel dosyasi (watcher bunu izler)
IZLENEN_EXCEL = DATA_DIR / "izlenen_adaylar.xlsx"

# Ollama ayarlari
OLLAMA_HOST = "http://127.0.0.1:11434"

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MODEL AYARLARI â€” Intel Arc 140V (16 GB VRAM) iÃ§in optimize
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# --- Aktif Modeller ---
# Ana sohbet modeli (kalite odaklÄ±)
DEFAULT_MODEL = "qwen2.5:14b"

# Model Ã§Ã¶kerse veya bulunamazsa devreye girer
DEFAULT_FALLBACK = "qwen2.5:7b"

# ArayÃ¼z dropdown'Ä±nda gÃ¶sterilecek modeller (sÄ±ralÄ±)
PRIMARY_MODELS = [
    "qwen2.5:14b",       # yÃ¼ksek kalite
    "qwen2.5:7b",        # dengeli (hÄ±zlÄ±)
    "qwen2.5:3b",        # Ã§ok hÄ±zlÄ± (basit sorular)
    "llama3.1:latest",   # alternatif
]

# Fallback zinciri (sÄ±rayla denenir)
FALLBACK_MODELS = [
    "qwen2.5:7b",
    "qwen2.5:3b",
]

# --- Model BaÅŸÄ±na Context (num_ctx) ---
# Daha bÃ¼yÃ¼k context = daha fazla KV cache = daha yavaÅŸ
MODEL_CONTEXT_MAP = {
    "qwen2.5:14b": 8192,
    "qwen2.5:7b": 8192,
    "qwen2.5:3b": 4096,        # 3B için 4096 yeterli
    "llama3.1:latest": 8192,
}

# --- Model BaÅŸÄ±na Temperature ---
# DÃ¼ÅŸÃ¼k = tutarlÄ±, YÃ¼ksek = yaratÄ±cÄ±
MODEL_TEMP_MAP = {
    "qwen2.5:14b": 0.35,       # ana model — tutarlı/kaliteli
    "qwen2.5:7b": 0.45,        # fallback
    "qwen2.5:3b": 0.40,        # hızlı işler
    "llama3.1:latest": 0.50,   # alternatif
}

# --- Genel Sabitler ---
DEFAULT_NUM_CTX = 8192
NUM_CTX = DEFAULT_NUM_CTX

# Modelin VRAM'de kalma sÃ¼resi (24h = sÃ¼rekli hazÄ±r, reload yok)
KEEP_ALIVE = "24h"

# --- Aday OlaylarÄ± (context iÃ§in) ---
ADAY_OLAY_LIMIT = 3
ADAY_PROMPT_LIMIT = 50



# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FLASK
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = False