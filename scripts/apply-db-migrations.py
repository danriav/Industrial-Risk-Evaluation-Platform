from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine


MIGRATIONS = [
    Path("src/db/migrations/001_iso14224_assets.sql"),
]


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required to apply database migrations.")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    with engine.begin() as connection:
        for migration_path in MIGRATIONS:
            sql = migration_path.read_text(encoding="utf-8")
            connection.exec_driver_sql(sql)
            print(f"Applied migration: {migration_path}")


if __name__ == "__main__":
    main()
