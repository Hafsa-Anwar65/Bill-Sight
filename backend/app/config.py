"""Settings, read once from environment variables (and a .env file if present)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # project root (contains backend/ and frontend/)
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")


@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    model: str = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite").strip()
    temperature: float = 0.0
    seed: int = 42
    max_attempts: int = int(os.getenv("EXTRACT_MAX_ATTEMPTS", "3"))
    cache_dir: Path = Path(os.getenv("CACHE_DIR", str(ROOT / "backend" / ".cache")))
    db_path: Path = Path(os.getenv("DB_PATH", str(ROOT / "backend" / "data" / "billsight.db")))
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))
    secure_cookies: bool = os.getenv("SECURE_COOKIES", "0") == "1"  # set to 1 when served over HTTPS
    frontend_dist: Path = ROOT / "frontend" / "dist"


settings = Settings()
