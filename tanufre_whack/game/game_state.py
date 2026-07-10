from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

import pygame

from tanufre_whack.game.mole import Mole
from tanufre_whack.input.base import InputPoint


@dataclass(frozen=True)
class MoleSpec:
    name: str
    normal_asset: str
    hit_asset: str
    x: float
    base_y: float
    width: int
    points: int


class GameState:
    def __init__(self, moles: Sequence[Mole], game_seconds: float) -> None:
        self.moles = list(moles)
        self.game_seconds = float(game_seconds)
        self.remaining_seconds = float(game_seconds)
        self.score = 0
        self.running = False
        self.finished = False
        self.spawn_timer = 0.0
        self.last_points: list[InputPoint] = []
        self.message = "CLICK START"

    def start(self) -> None:
        self.score = 0
        self.remaining_seconds = self.game_seconds
        self.running = True
        self.finished = False
        self.spawn_timer = 0.15
        self.message = ""
        for mole in self.moles:
            mole.state = "hidden"
            mole.visible_amount = 0.0
            mole.visible_timer = 0.0
            mole.hit_timer = 0.0
            mole.cooldown = 0.0

    def update(self, dt: float, points: Sequence[InputPoint]) -> None:
        self.last_points = list(points)
        if not self.running:
            return

        self.remaining_seconds = max(0.0, self.remaining_seconds - dt)
        if self.remaining_seconds <= 0.0:
            self.running = False
            self.finished = True
            self.message = "TIME UP"

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
            self.spawn_timer = random.uniform(0.38, 0.82)

    def handle_menu_click(self, events: Sequence[pygame.event.Event]) -> None:
        if self.running:
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.start()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start()

    def _spawn_random_mole(self) -> None:
        active_count = sum(1 for mole in self.moles if mole.active)
        max_active = 2
        if active_count >= max_active:
            return
        choices = [mole for mole in self.moles if mole.state == "hidden" and mole.cooldown <= 0.0]
        if not choices:
            return
        random.choice(choices).spawn(random.uniform(0.75, 1.25))
