# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys

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
    audio = None
    try:
        audio = AudioController()
        is_web = sys.platform == "emscripten"
        flags = pygame.FULLSCREEN if settings.get("fullscreen") else pygame.RESIZABLE
        screen = pygame.display.set_mode(
            (int(settings["screen_width"]), int(settings["screen_height"])), flags
        )
        pygame.display.set_caption("タヌたたき")
        clock = pygame.time.Clock()

        renderer = Renderer(
            screen,
            _load_asset("background.png"),
            _load_asset("bg.png"),
            _load_asset("sign.png"),
            _load_asset("title.png"),
            _load_asset("instruction_tanu.png"),
            _load_asset("instruction_ino.png"),
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
        audio.play_menu_bgm()

        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED) and not is_web:
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
            previous_screen = state.screen
            state.handle_menu_click(events)
            if state.screen != previous_screen:
                audio.play_ok()
                if state.screen in ("start", "instructions"):
                    audio.play_menu_bgm()
                if previous_screen == "instructions" and state.screen == "countdown":
                    audio.stop_menu_bgm()
                    audio.play_bgm()
            points = []
            for provider in providers:
                points.extend(provider.get_points(events))
            previous_score = state.score
            was_running = state.running
            state.update(dt, points)
            if state.score > previous_score:
                audio.play_hit()
            if was_running and state.screen == "result":
                audio.stop_bgm()
                audio.play_menu_bgm()
            renderer.draw(state)
            await asyncio.sleep(0)
    finally:
        if audio is not None:
            audio.stop_bgm()
            audio.stop_menu_bgm()
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


class AudioController:
    def __init__(self) -> None:
        self.enabled = False
        self.bgm: pygame.mixer.Sound | None = None
        self.menu_bgm: pygame.mixer.Sound | None = None
        self.hit: pygame.mixer.Sound | None = None
        self.ok: pygame.mixer.Sound | None = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.bgm = self._load("bgm.mp3", 0.45)
            self.menu_bgm = self._load("bgm_menu.mp3", 0.45)
            self.hit = self._load("hit.mp3", 0.8)
            self.ok = self._load("ok.mp3", 0.8)
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play_bgm(self) -> None:
        if not self.enabled or self.bgm is None:
            return
        self.bgm.stop()
        self.bgm.play(loops=-1)

    def stop_bgm(self) -> None:
        if self.bgm is not None:
            self.bgm.stop()

    def play_menu_bgm(self) -> None:
        if not self.enabled or self.menu_bgm is None:
            return
        self.stop_bgm()
        self.menu_bgm.stop()
        self.menu_bgm.play(loops=-1)

    def stop_menu_bgm(self) -> None:
        if self.menu_bgm is not None:
            self.menu_bgm.stop()

    def play_hit(self) -> None:
        self._play(self.hit)

    def play_ok(self) -> None:
        self._play(self.ok)

    def _load(self, filename: str, volume: float) -> pygame.mixer.Sound:
        sound = pygame.mixer.Sound(str(ASSET_DIR / "sounds" / filename))
        sound.set_volume(volume)
        return sound

    def _play(self, sound: pygame.mixer.Sound | None) -> None:
        if self.enabled and sound is not None:
            sound.play()


if __name__ == "__main__":
    main()
