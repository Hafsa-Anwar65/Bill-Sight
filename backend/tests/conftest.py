import io
import json
from pathlib import Path

import pytest
from PIL import Image

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


ALL = sorted(p.stem for p in FIXTURES.glob("*.json"))


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    from app import cache
    from app.config import settings

    object.__setattr__(settings, "cache_dir", tmp_path / "cache")
    object.__setattr__(settings, "db_path", tmp_path / "test.db")
    if settings.database_url:  # running the suite against Postgres: start every test empty
        from app import db

        with db.connect() as conn:
            conn.execute("TRUNCATE users, sessions, bills RESTART IDENTITY CASCADE")
    yield cache


@pytest.fixture
def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (40, 60), "white").save(buf, format="PNG")
    return buf.getvalue()
