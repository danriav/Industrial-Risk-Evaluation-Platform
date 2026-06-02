from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import app


OUTPUT_PATH = Path("docs/openapi.json")


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Exported OpenAPI schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
