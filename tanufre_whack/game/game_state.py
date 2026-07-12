from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Sequence

import pygame

from tanufre_whack.game.mole import Mole
from tanufre_whack.input.base import InputPoint


@dataclass(frozen=True)
class MoleSpec:
    name: str
    normal_asset: str
    hit_asset: str
    width: int
    points: int


class GameState:
    def __init__(
        self,
        moles: Sequence[Mole],
        game_seconds: float,
        screen_rect: pygame.Rect,
        sign_rect: pygame.Rect,
        menu_button_rect: pygame.Rect,
    ) -> None:
        self.moles = list(moles)
        self.game_seconds = float(game_seconds)
        self.screen_rect = screen_rect
        self.sign_rect = sign_rect
        self.menu_button_rect = menu_button_rect
        self.remaining_seconds = float(game_seconds)
        self.score = 0
        self.screen = "start"
        self.spawn_timer = 0.0
        self.speed_up_timer = 0.0
        self.last_speed_phase = 0
        self.last_points: list[InputPoint] = []

    def start(self) -> None:
        self.score = 0
        self.remaining_seconds = self.game_seconds
        self.screen = "playing"
        self.spawn_timer = 0.15
        self.speed_up_timer = 0.0
        self.last_speed_phase = 0
        for mole in self.moles:
            mole.state = "hidden"
            mole.visible_amount = 0.0
            mole.visible_timer = 0.0
            mole.hit_timer = 0.0
            mole.cooldown = 0.0
            mole.hidden_center = self.sign_rect.center
            mole.target_center = self.sign_rect.center

    def update(self, dt: float, points: Sequence[InputPoint]) -> None:
        self.last_points = list(points)
        if self.screen != "playing":
            return

        self.remaining_seconds = max(0.0, self.remaining_seconds - dt)
        if self.remaining_seconds <= 0.0:
            self.screen = "result"
            self._hide_all_moles()
            return

        current_phase = self.speed_phase
        if current_phase > self.last_speed_phase:
            self.last_speed_phase = current_phase
            self.speed_up_timer = 1.5
        if self.speed_up_timer > 0.0:
            self.speed_up_timer = max(0.0, self.speed_up_timer - dt)

        for mole in self.moles:
            mole.update(dt)

        for point in points:
            if not point.active:
                continue
            for mole in self.moles:
                if mole.hitbox.collidepoint(point.x, point.y):
                    self.score += mole.hit()

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self._spawn_random_mole()
            self.spawn_timer = random.uniform(*self.spawn_interval_range)

    def handle_menu_click(self, events: Sequence[pygame.event.Event]) -> None:
        if self.screen == "playing":
            return
        for event in events:
            if self.screen == "start" and self._is_confirm_event(event):
                self.start()
            elif self.screen == "result" and self._is_confirm_event(event):
                self.screen = "start"

    @property
    def running(self) -> bool:
        return self.screen == "playing"

    @property
    def finished(self) -> bool:
        return self.screen == "result"

    @property
    def speed_phase(self) -> int:
        elapsed_seconds = self.game_seconds - self.remaining_seconds
        phase_seconds = self.game_seconds / 3
        if elapsed_seconds >= phase_seconds * 2:
            return 2
        if elapsed_seconds >= phase_seconds:
            return 1
        return 0

    @property
    def spawn_interval_range(self) -> tuple[float, float]:
        if self.speed_phase == 2:
            return (0.38, 0.82)
        if self.speed_phase == 1:
            return (0.68, 1.10)
        return (1.15, 1.85)

    @property
    def visible_seconds_range(self) -> tuple[float, float]:
        if self.speed_phase == 2:
            return (0.75, 1.25)
        if self.speed_phase == 1:
            return (1.05, 1.55)
        return (1.55, 2.20)

    @property
    def motion_seconds(self) -> tuple[float, float]:
        if self.speed_phase == 2:
            return (0.22, 0.20)
        if self.speed_phase == 1:
            return (0.34, 0.30)
        return (0.56, 0.48)

    def _is_confirm_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.menu_button_rect.collidepoint(event.pos)
        return event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)

    def _hide_all_moles(self) -> None:
        for mole in self.moles:
            mole.state = "hidden"
            mole.visible_amount = 0.0
            mole.visible_timer = 0.0
            mole.hit_timer = 0.0

    def _spawn_random_mole(self) -> None:
        active_count = sum(1 for mole in self.moles if mole.active)
        max_active = 2
        if active_count >= max_active:
            return
        choices = [mole for mole in self.moles if mole.state == "hidden" and mole.cooldown <= 0.0]
        if not choices:
            return
        random.shuffle(choices)
        for mole in choices:
            spawn = self._find_non_overlapping_spawn(mole)
            if spawn is None:
                continue
            edge, hidden_center, target_center = spawn
            rise_seconds, fall_seconds = self.motion_seconds
            mole.spawn(
                random.uniform(*self.visible_seconds_range),
                edge,
                hidden_center,
                target_center,
                rise_seconds,
                fall_seconds,
            )
            return

    def _find_non_overlapping_spawn(
        self, mole: Mole
    ) -> Optional[tuple[str, tuple[float, float], tuple[float, float]]]:
        edges = ["top", "right", "bottom", "left"]
        for _ in range(24):
            edge = random.choice(edges)
            hidden_center, target_center = self._spawn_centers(mole, edge)
            target_rect = self._rect_at(mole, target_center).inflate(28, 28)
            if not self._overlaps_active_moles(mole, target_rect):
                return edge, hidden_center, target_center
        return None

    def _overlaps_active_moles(self, candidate: Mole, target_rect: pygame.Rect) -> bool:
        for mole in self.moles:
            if mole is candidate or not mole.active:
                continue
            other_target_rect = self._rect_at(mole, mole.target_center).inflate(28, 28)
            if target_rect.colliderect(other_target_rect):
                return True
        return False

    def _rect_at(self, mole: Mole, center: tuple[float, float]) -> pygame.Rect:
        return mole.image.get_rect(center=(round(center[0]), round(center[1])))

    def _spawn_centers(
        self, mole: Mole, edge: str
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        image = mole.image
        half_w = image.get_width() / 2
        half_h = image.get_height() / 2

        min_x = max(self.screen_rect.left + half_w, self.sign_rect.left + half_w)
        max_x = min(self.screen_rect.right - half_w, self.sign_rect.right - half_w)
        min_y = max(self.screen_rect.top + half_h, self.sign_rect.top + half_h)
        max_y = min(self.screen_rect.bottom - half_h, self.sign_rect.bottom - half_h)

        if edge == "top":
            x = random.uniform(min_x, max_x)
            return (x, self.sign_rect.top + half_h), (x, self.sign_rect.top - 2)
        if edge == "bottom":
            x = random.uniform(min_x, max_x)
            return (x, self.sign_rect.bottom - half_h), (x, self.sign_rect.bottom + 2)
        if edge == "left":
            y = random.uniform(min_y, max_y)
            return (self.sign_rect.left + half_w, y), (self.sign_rect.left - 2, y)

        y = random.uniform(min_y, max_y)
        return (self.sign_rect.right - half_w, y), (self.sign_rect.right + 2, y)
