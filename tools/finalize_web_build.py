from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_BUILD = ROOT / "web-src" / "build" / "web"
INDEX = WEB_BUILD / "index.html"
ARCHIVES = ["web-src.tar.gz", "web-src.apk"]


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for archive_name in ARCHIVES:
        archive = WEB_BUILD / archive_name
        if not archive.exists():
            continue
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()[:12]
        cache_busted_name = f"{archive_name}?v={digest}"
        html = html.replace(f'"{archive_name}"', f'"{cache_busted_name}"')
    INDEX.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
