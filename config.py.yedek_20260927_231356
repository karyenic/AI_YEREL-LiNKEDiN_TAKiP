from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Veritabanları
ADAY_DB = DATA_DIR / "linkedin_takip.db"
CHAT_DB = DATA_DIR / "sohbet_gecmisi.db"

# İzlenen Excel dosyası (watcher bunu izler)
IZLENEN_EXCEL = DATA_DIR / "izlenen_adaylar.xlsx"

# Ollama ayarları
OLLAMA_HOST = "http://127.0.0.1:11434"
NUM_CTX = 16384
KEEP_ALIVE = "30m"

# Model listesi
PRIMARY_MODELS = ["qwen2.5:7b", "deepseek-r1:7b", "ministral-3:14b", "llama3.1:latest"]
FALLBACK_MODELS = ["qwen2.5:3b", "gemma2:2b"]
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_FALLBACK = "qwen2.5:3b"

# Flask
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = False