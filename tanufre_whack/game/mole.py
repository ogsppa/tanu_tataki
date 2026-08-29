from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Mole:
    name: str
    normal_image: pygame.Surface
    hit_image: pygame.Surface
    normal_mask: pygame.mask.Mask
    hit_mask: pygame.mask.Mask
    width: int
    points: int = 1
    state: str = "hidden"
    visible_amount: float = 0.0
    visible_timer: float = 0.0
    hit_timer: float = 0.0
    cooldown: float = 0.0
    edge: str = "top"
    hidden_center: tuple[float, float] = (0.0, 0.0)
    target_center: tuple[float, float] = (0.0, 0.0)
    rise_seconds: float = 0.22
    fall_seconds: float = 0.20

    def update(self, dt: float) -> None:
        if self.cooldown > 0.0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if self.state == "rising":
            self.visible_amount = min(1.0, self.visible_amount + dt / self.rise_seconds)
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
            self.visible_amount = max(0.0, self.visible_amount - dt / self.fall_seconds)
            if self.visible_amount <= 0.0:
                self.state = "hidden"
                self.cooldown = 0.15

    def spawn(
        self,
        visible_seconds: float,
        edge: str,
        hidden_center: tuple[float, float],
        target_center: tuple[float, float],
        rise_seconds: float = 0.22,
        fall_seconds: float = 0.20,
    ) -> None:
        if self.state != "hidden" or self.cooldown > 0.0:
            return
        self.edge = edge
        self.hidden_center = hidden_center
        self.target_center = target_center
        self.rise_seconds = rise_seconds
        self.fall_seconds = fall_seconds
        self.state = "rising"
        self.visible_amount = 0.0
        self.visible_timer = visible_seconds

    def hit(self) -> int:
        if self.state != "visible":
            return 0
        self.state = "hit"
        self.hit_timer = 0.16
        return self.points

    def collide_point(self, x: float, y: float) -> bool:
        if self.state != "visible":
            return False
        rect = self.draw_rect
        local_x = round(x - rect.left)
        local_y = round(y - rect.top)
        padding = 14
        if (
            local_x < -padding
            or local_y < -padding
            or local_x >= rect.width + padding
            or local_y >= rect.height + padding
        ):
            return False
        return self._near_opaque_pixel(local_x, local_y, padding)

    def _near_opaque_pixel(self, local_x: int, local_y: int, padding: int) -> bool:
        if 0 <= local_x < self.mask.get_size()[0] and 0 <= local_y < self.mask.get_size()[1]:
            if self.mask.get_at((local_x, local_y)):
                return True
        for dy in range(-padding, padding + 1, 4):
            for dx in range(-padding, padding + 1, 4):
                sample_x = local_x + dx
                sample_y = local_y + dy
                if sample_x < 0 or sample_y < 0:
                    continue
                if sample_x >= self.mask.get_size()[0] or sample_y >= self.mask.get_size()[1]:
                    continue
                if dx * dx + dy * dy <= padding * padding and self.mask.get_at((sample_x, sample_y)):
                    return True
        return False

    @property
    def active(self) -> bool:
        return self.state != "hidden"

    @property
    def image(self) -> pygame.Surface:
        return self.hit_image if self.state == "hit" else self.normal_image

    @property
    def mask(self) -> pygame.mask.Mask:
        return self.hit_mask if self.state == "hit" else self.normal_mask

    @property
    def draw_rect(self) -> pygame.Rect:
        image = self.image
        start_x, start_y = self.hidden_center
        end_x, end_y = self.target_center
        x = start_x + (end_x - start_x) * self.visible_amount
        y = start_y + (end_y - start_y) * self.visible_amount
        return image.get_rect(center=(round(x), round(y)))

    @property
    def hitbox(self) -> pygame.Rect:
        rect = self.draw_rect
        return rect.inflate(-rect.width * 0.34, -rect.height * 0.36)
