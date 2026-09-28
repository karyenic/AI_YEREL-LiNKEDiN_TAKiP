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
# Her modelin ihtiyaci farkli:
#   - qwen2.5:7b    -> Aday takibi + sohbet icin 8K fazlasiyla yeterli
#   - deepseek-r1   -> Reasoning modeli, uzun dusunme icin 16K gerekli
#   - kucuk fallback-> 4K yeterli, VRAM tasarrufu
# Haritada olmayan model icin DEFAULT_NUM_CTX kullanilir.
# ------------------------------------------------------------------
MODEL_CONTEXT_MAP = {
    "qwen2.5:7b": 16384,
    "qwen2.5:3b": 4096,
    "qwen2.5:14b": 8192,
    "deepseek-r1:7b": 16384,
    "gemma2:2b": 4096,
    "llama3.1:latest": 8192,
    "ministral-3:14b": 8192,
}

DEFAULT_NUM_CTX = 8192

# Geriye donuk uyumluluk icin (artik kullanilmiyor)
NUM_CTX = DEFAULT_NUM_CTX

KEEP_ALIVE = "30m"

# Model listesi
PRIMARY_MODELS = ["qwen2.5:7b"]
FALLBACK_MODELS = ["qwen2.5:3b"]
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_FALLBACK = "qwen2.5:7b"

# Flask
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = False

# ------------------------------------------------------------------
# MODEL ROUTER - Soru tipine gore model secimi
# ------------------------------------------------------------------
MODEL_ROUTER = {
    "basit":  "qwen2.5:3b",     # Sayisal/basit sorular icin hizli model
    "normal": "qwen2.5:7b",     # Genel sohbet
    "analiz": "qwen2.5:7b",     # Derin analiz
}

# Basit soru tetikleyicileri (bu kelimeler varsa 3b kullanilir)
BASIT_TETIKLEYICILER = ["kac", "ka?", "toplam", "sayi", "say?", "adet", "liste"]

# ------------------------------------------------------------------
# ADAY OLAYLARI (context icin)
# ------------------------------------------------------------------
ADAY_OLAY_LIMIT = 3           # Her aday icin son N olay prompt'a eklenir
ADAY_PROMPT_LIMIT = 50        # Prompt'a eklenecek maksimum aday sayisi
