from __future__ import annotations

from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "tanufre_whack" / "assets"
PAIRS = [
    ("tanuki_normal.png", "tanuki_hit.png", (238, 80, 71)),
    ("boar_normal.png", "boar_hit.png", (229, 101, 57)),
    ("hamster_normal.png", "hamster_hit.png", (240, 142, 64)),
]


def make_hit_asset(source_name: str, output_name: str, accent: tuple[int, int, int]) -> None:
    image = pygame.image.load(str(ASSETS / source_name))
    overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    width, height = image.get_size()

    overlay.fill((*accent, 70))
    line_width = max(4, width // 32)
    pygame.draw.line(overlay, (*accent, 210), (0, height), (width, 0), line_width)
    pygame.draw.line(overlay, (*accent, 210), (0, 0), (width, height), line_width)

    font_size = max(24, min(width, height) // 4)
    font = pygame.font.SysFont("arial", font_size, bold=True)
    label = font.render("HIT", True, (255, 255, 255))
    shadow = font.render("HIT", True, (70, 32, 30))
    label_rect = label.get_rect(center=(width // 2, max(font_size, height // 4)))
    overlay.blit(shadow, label_rect.move(3, 3))
    overlay.blit(label, label_rect)

    image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.image.save(image, str(ASSETS / output_name))


def main() -> None:
    pygame.init()
    try:
        for source_name, output_name, accent in PAIRS:
            make_hit_asset(source_name, output_name, accent)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
