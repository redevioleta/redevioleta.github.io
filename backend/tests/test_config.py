import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings


def test_postgres_urls_use_psycopg_driver():
    rest = "@host:5432/db"
    for scheme in ("postgres", "postgresql"):
        url = Settings(database_url=scheme + "://u" + ":" + "x" + rest).sqlalchemy_database_url
        assert url.startswith("postgresql+psycopg://")
        assert url.endswith(rest)


def test_sqlite_default_untouched():
    assert Settings().sqlalchemy_database_url.startswith("sqlite:///")


def test_cors_allowlist_includes_pages_and_has_no_wildcard():
    origins = Settings().cors_origin_list
    assert "https://redevioleta.github.io" in origins
    assert "*" not in origins


def test_cors_origins_env_parsing():
    s = Settings(cors_origins=" https://a.example/ , https://b.example ")
    assert s.cors_origin_list == ["https://a.example", "https://b.example"]
