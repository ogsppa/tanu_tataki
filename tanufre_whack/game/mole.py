from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Mole:
    name: str
    normal_image: pygame.Surface
    hit_image: pygame.Surface
    x: float
    base_y: float
    width: int
    points: int = 1
    state: str = "hidden"
    visible_amount: float = 0.0
    visible_timer: float = 0.0
    hit_timer: float = 0.0
    cooldown: float = 0.0

    def update(self, dt: float) -> None:
        if self.cooldown > 0.0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if self.state == "rising":
            self.visible_amount = min(1.0, self.visible_amount + dt / 0.22)
            if self.visible_amount >= 1.0:
                self.state = "visible"
        elif self.state == "visible":
            self.visible_timer -= dt
            if self.visible_timer <= 0.0:
                self.state = "falling"
        elif self.state == "hit":
            self.hit_timer -= dt
            if self.hit_timer <= 0.0:
                self.state = "falling"
        elif self.state == "falling":
            self.visible_amount = max(0.0, self.visible_amount - dt / 0.20)
            if self.visible_amount <= 0.0:
                self.state = "hidden"
                self.cooldown = 0.15

    def spawn(self, visible_seconds: float) -> None:
        if self.state != "hidden" or self.cooldown > 0.0:
            return
        self.state = "rising"
        self.visible_amount = 0.0
        self.visible_timer = visible_seconds

    def hit(self) -> int:
        if self.state != "visible":
            return 0
        self.state = "hit"
        self.hit_timer = 0.16
        return self.points

    @property
    def active(self) -> bool:
        return self.state != "hidden"

    @property
    def image(self) -> pygame.Surface:
        return self.hit_image if self.state == "hit" else self.normal_image

    @property
    def draw_rect(self) -> pygame.Rect:
        image = self.image
        visible_offset = int((1.0 - self.visible_amount) * image.get_height() * 0.76)
        rect = image.get_rect(midbottom=(round(self.x), round(self.base_y + visible_offset)))
        return rect

    @property
    def hitbox(self) -> pygame.Rect:
        rect = self.draw_rect
        return rect.inflate(-rect.width * 0.34, -rect.height * 0.36)
