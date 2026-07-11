from __future__ import annotations

import pygame

from tanufre_whack.game.game_state import GameState, MoleSpec
from tanufre_whack.game.mole import Mole
from tanufre_whack.game.renderer import Renderer
from tanufre_whack.game.settings import ASSET_DIR, load_settings
from tanufre_whack.input import KeyboardInput, MouseInput


MOLE_SPECS = [
    MoleSpec("tanuki", "tanuki_normal.png", "tanuki_hit.png", 210, 1),
    MoleSpec("boar", "boar_normal.png", "boar_hit.png", 230, 1),
    MoleSpec("hamster", "hamster_normal.png", "hamster_hit.png", 190, 1),
]


def main() -> None:
    settings = load_settings()
    pygame.init()
    try:
        flags = pygame.FULLSCREEN if settings.get("fullscreen") else 0
        screen = pygame.display.set_mode(
            (int(settings["screen_width"]), int(settings["screen_height"])), flags
        )
        pygame.display.set_caption("Tanufre Whack")
        clock = pygame.time.Clock()

        renderer = Renderer(
            screen,
            _load_asset("background.png"),
            _load_asset("sign.png"),
            bool(settings["show_debug_cursor"]),
        )
        moles = [_make_mole(spec) for spec in MOLE_SPECS]
        state = GameState(
            moles,
            float(settings["game_seconds"]),
            screen.get_rect(),
            renderer.sign_rect,
        )
        providers = [
            MouseInput(),
            KeyboardInput(lambda: [(mole.draw_rect.centerx, mole.draw_rect.centery) for mole in moles]),
        ]

        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            state.handle_menu_click(events)
            points = []
            for provider in providers:
                points.extend(provider.get_points(events))
            state.update(dt, points)
            renderer.draw(state)
    finally:
        pygame.quit()


def _make_mole(spec: MoleSpec) -> Mole:
    normal = _scale_to_width(_load_asset(spec.normal_asset), spec.width)
    hit = _scale_to_width(_load_asset(spec.hit_asset), spec.width)
    return Mole(spec.name, normal, hit, spec.width, spec.points)


def _load_asset(name: str) -> pygame.Surface:
    return pygame.image.load(str(ASSET_DIR / name)).convert_alpha()


def _scale_to_width(image: pygame.Surface, width: int) -> pygame.Surface:
    ratio = width / image.get_width()
    size = (width, round(image.get_height() * ratio))
    return pygame.transform.smoothscale(image, size)


if __name__ == "__main__":
    main()
