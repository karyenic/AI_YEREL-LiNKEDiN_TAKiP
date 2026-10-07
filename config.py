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

# ═══════════════════════════════════════════════════════════════════
# MODEL AYARLARI — Intel Arc 140V (16 GB VRAM) için optimize
# ═══════════════════════════════════════════════════════════════════

# --- Aktif Modeller ---
# Ana sohbet modeli (kalite odaklı)
DEFAULT_MODEL = "qwen2.5:14b"

# Model çökerse veya bulunamazsa devreye girer
DEFAULT_FALLBACK = "qwen2.5:7b"

# Arayüz dropdown'ında gösterilecek modeller (sıralı)
PRIMARY_MODELS = [
    "qwen2.5:14b",       # yüksek kalite
    "qwen2.5:7b",        # dengeli (hızlı)
    "qwen2.5:3b",        # çok hızlı (basit sorular)
    "llama3.1:latest",   # alternatif
    "ministral-3:14b",
]

# Fallback zinciri (sırayla denenir)
FALLBACK_MODELS = [
    "qwen2.5:7b",
    "qwen2.5:3b",
]

# --- Model Başına Context (num_ctx) ---
# Daha büyük context = daha fazla KV cache = daha yavaş
MODEL_CONTEXT_MAP = {
    "qwen2.5:14b": 8192,      # ~1 GB KV cache
    "qwen2.5:7b": 8192,       # ~1 GB
    "qwen2.5:3b": 8192,        # ~300 MB
    "llama3.1:latest": 8192,
    "ministral-3:14b": 8192
}

# --- Model Başına Temperature ---
# Düşük = tutarlı, Yüksek = yaratıcı
MODEL_TEMP_MAP = {
    "qwen2.5:14b": 0.4,        # kalite/dengeli
    "qwen2.5:7b": 0.7,         # standart
    "qwen2.5:3b": 0.5,         # kısa cevaplar
    "llama3.1:latest": 0.7,
    "ministral-3:14b": 0.5,
}

# --- Genel Sabitler ---
DEFAULT_NUM_CTX = 8192
NUM_CTX = DEFAULT_NUM_CTX

# Modelin VRAM'de kalma süresi (24h = sürekli hazır, reload yok)
KEEP_ALIVE = "24h"

# --- Aday Olayları (context için) ---
ADAY_OLAY_LIMIT = 3
ADAY_PROMPT_LIMIT = 50



# ═══════════════════════════════════════════════════════════════════
# FLASK
# ═══════════════════════════════════════════════════════════════════

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = False