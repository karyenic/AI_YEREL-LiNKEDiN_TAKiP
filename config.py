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

# ------------------------------------------------------------------
# MODEL BAZLI AKILLI CONTEXT PENCERESI (num_ctx)
# ------------------------------------------------------------------
MODEL_CONTEXT_MAP = {
    "deepseek-r1-64k": 65536,
    "qwen2.5-coder:14b": 32768,
    "deepseek-r1:7b": 16384,
    "qwen2.5:7b": 16384,
    "qwen2.5:14b": 8192,
    "llama3.1:latest": 8192,
        "qwen2.5:3b": 4096,
    "gemma2:2b": 4096,
}

# ------------------------------------------------------------------
# MODEL BAZLI AKILLI TEMPERATURE AYARLARI
# ------------------------------------------------------------------
MODEL_TEMP_MAP = {
    "deepseek-r1-64k": 0.6,
    "qwen2.5-coder:14b": 0.2,
    "deepseek-r1:7b": 0.7,
    "qwen2.5:7b": 0.7,
    "llama3.1:latest": 0.7,
    "qwen2.5:3b": 0.5,
}

DEFAULT_NUM_CTX = 8192
NUM_CTX = DEFAULT_NUM_CTX
KEEP_ALIVE = "30m"

# Model listeleri
PRIMARY_MODELS = ["deepseek-r1-64k", "qwen2.5:7b"]
FALLBACK_MODELS = ["qwen2.5:7b", "qwen2.5:3b"]
DEFAULT_MODEL = "deepseek-r1-64k"
DEFAULT_FALLBACK = "qwen2.5:7b"

# Flask
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = False

# ------------------------------------------------------------------
# MODEL ROUTER - Soru tipine gore model secimi
# ------------------------------------------------------------------
MODEL_ROUTER = {
    "basit":  "qwen2.5:3b",
    "normal": "qwen2.5:7b",
    "analiz": "deepseek-r1-64k",
    "kod":    "qwen2.5-coder:14b",
}

# Basit soru tetikleyicileri
BASIT_TETIKLEYICILER = ["kac", "ka?", "toplam", "sayi", "say?", "adet", "liste"]

# ------------------------------------------------------------------
# ADAY OLAYLARI (context icin)
# ------------------------------------------------------------------
ADAY_OLAY_LIMIT = 3
ADAY_PROMPT_LIMIT = 50