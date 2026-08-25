from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_BUILD = ROOT / "web-src" / "build" / "web"
INDEX = WEB_BUILD / "index.html"
ARCHIVES = ["web-src.tar.gz", "web-src.apk"]
VIEWPORT_CSS = """
        html, body {
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }

        canvas.emscripten {
            width: 100vw !important;
            height: 100vh !important;
            max-width: none !important;
            max-height: none !important;
        }
"""


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    html = _inject_viewport_css(html)
    for archive_name in ARCHIVES:
        archive = WEB_BUILD / archive_name
        if not archive.exists():
            continue
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()[:12]
        cache_busted_name = f"{archive_name}?v={digest}"
        html = html.replace(f'"{archive_name}"', f'"{cache_busted_name}"')
    INDEX.write_text(html, encoding="utf-8")


def _inject_viewport_css(html: str) -> str:
    marker = "    </style>"
    if "width: 100vw;" in html and "height: 100vh;" in html:
        return html
    if marker not in html:
        return html
    return html.replace(marker, f"{VIEWPORT_CSS}{marker}", 1)


if __name__ == "__main__":
    main()
