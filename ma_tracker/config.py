from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Project root and data dir
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database location (SQLite by default)
DB_URL = os.getenv("DB_URL", f"sqlite:///{(DATA_DIR / 'ma_tracker.db').as_posix()}")
