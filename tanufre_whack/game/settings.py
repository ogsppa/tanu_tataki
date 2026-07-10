from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = PACKAGE_DIR / "assets"
CONFIG_DIR = PACKAGE_DIR / "config"


def load_settings() -> dict[str, Any]:
    with (CONFIG_DIR / "settings.json").open("r", encoding="utf-8") as file:
        return json.load(file)
