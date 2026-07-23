from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web-src"


def main() -> None:
    if WEB_SRC.exists():
        shutil.rmtree(WEB_SRC)
    WEB_SRC.mkdir()

    shutil.copytree(ROOT / "tanufre_whack", WEB_SRC / "tanufre_whack")
    shutil.copy2(ROOT / "web" / "main.py", WEB_SRC / "main.py")


if __name__ == "__main__":
    main()
