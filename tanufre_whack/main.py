# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio

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


async def main_async() -> None:
    settings = load_settings()
    pygame.init()
    try:
        flags = pygame.FULLSCREEN if settings.get("fullscreen") else pygame.RESIZABLE
        screen = pygame.display.set_mode(
            (int(settings["screen_width"]), int(settings["screen_height"])), flags
        )
        pygame.display.set_caption("タヌたたき")
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
            renderer.visible_sign_rect,
            renderer.menu_button_rect,
            renderer.sign_rect,
            renderer.sign_opaque_mask,
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
                elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                    if not settings.get("fullscreen"):
                        size = getattr(event, "size", screen.get_size())
                        screen = pygame.display.set_mode(size, flags)
                    renderer.resize(screen)
                    state.update_layout(
                        screen.get_rect(),
                        renderer.visible_sign_rect,
                        renderer.button_rect_for(state.screen),
                        renderer.sign_rect,
                        renderer.sign_opaque_mask,
                    )

            state.menu_button_rect = renderer.button_rect_for(state.screen)
            state.handle_menu_click(events)
            points = []
            for provider in providers:
                points.extend(provider.get_points(events))
            state.update(dt, points)
            renderer.draw(state)
            await asyncio.sleep(0)
    finally:
        pygame.quit()


def main() -> None:
    asyncio.run(main_async())


def _make_mole(spec: MoleSpec) -> Mole:
    normal = _scale_to_width(_load_asset(spec.normal_asset), spec.width)
    hit = _scale_to_width(_load_asset(spec.hit_asset), spec.width)
    normal_mask = pygame.mask.from_surface(normal, 0)
    hit_mask = pygame.mask.from_surface(hit, 0)
    return Mole(spec.name, normal, hit, normal_mask, hit_mask, spec.width, spec.points)


def _load_asset(name: str) -> pygame.Surface:
    return pygame.image.load(str(ASSET_DIR / name)).convert_alpha()


def _scale_to_width(image: pygame.Surface, width: int) -> pygame.Surface:
    ratio = width / image.get_width()
    size = (width, round(image.get_height() * ratio))
    return pygame.transform.smoothscale(image, size)


if __name__ == "__main__":
    main()
