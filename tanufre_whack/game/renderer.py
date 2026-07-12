from __future__ import annotations

import pygame

from tanufre_whack.game.game_state import GameState
from tanufre_whack.game.mole import Mole


class Renderer:
    def __init__(
        self,
        screen: pygame.Surface,
        background: pygame.Surface,
        sign: pygame.Surface,
        show_debug_cursor: bool,
    ) -> None:
        self.screen = screen
        self.show_debug_cursor = show_debug_cursor
        self.width, self.height = screen.get_size()
        self.background = self._cover(background, self.width, self.height)
        self.sign = self._fit(sign, int(self.width * 0.58), int(self.height * 0.56))
        self.sign_rect = self.sign.get_rect(center=(self.width // 2, self.height // 2))
        self.visible_sign_rect = self._alpha_world_rect(self.sign, self.sign_rect)
        self.font_large = pygame.font.SysFont("arial", 64, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 34, bold=True)
        self.font_small = pygame.font.SysFont("arial", 22, bold=True)

    def draw(self, state: GameState) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_moles(state.moles)
        self.screen.blit(self.sign, self.sign_rect)
        self._draw_hud(state)
        if self.show_debug_cursor:
            self._draw_debug(state)
        pygame.display.flip()

    def _draw_moles(self, moles: list[Mole]) -> None:
        for mole in moles:
            if mole.state == "hidden":
                continue
            image = mole.image
            rect = mole.draw_rect
            clip = self._outside_sign_clip(mole.edge)
            previous_clip = self.screen.get_clip()
            self.screen.set_clip(clip)
            self.screen.blit(image, rect)
            self.screen.set_clip(previous_clip)

    def _draw_hud(self, state: GameState) -> None:
        self._label(f"SCORE {state.score}", 28, 24, self.font_medium)
        self._label(f"TIME {int(state.remaining_seconds + 0.999):02d}", self.width - 190, 24, self.font_medium)
        if not state.running:
            headline = "TANUFRE WHACK"
            prompt = "CLICK OR PRESS SPACE"
            if state.finished:
                headline = f"FINISH  SCORE {state.score}"
                prompt = "CLICK TO RESTART"
            self._center_label(headline, self.height * 0.30, self.font_large)
            self._center_label(prompt, self.height * 0.43, self.font_medium)

    def _draw_debug(self, state: GameState) -> None:
        for point in state.last_points:
            color = (255, 238, 88) if point.active else (255, 255, 255)
            pygame.draw.circle(self.screen, color, (round(point.x), round(point.y)), 10, 2)
        for index, mole in enumerate(state.moles, start=1):
            pygame.draw.rect(self.screen, (80, 230, 180), mole.hitbox, 2)
            self._label(str(index), mole.hitbox.centerx - 7, mole.hitbox.top - 26, self.font_small)
        pygame.draw.rect(self.screen, (255, 238, 88), self.visible_sign_rect, 2)

    def _label(self, text: str, x: float, y: float, font: pygame.font.Font) -> None:
        surface = font.render(text, True, (255, 255, 255))
        shadow = font.render(text, True, (20, 24, 34))
        self.screen.blit(shadow, (x + 3, y + 3))
        self.screen.blit(surface, (x, y))

    def _center_label(self, text: str, y: float, font: pygame.font.Font) -> None:
        surface = font.render(text, True, (255, 255, 255))
        shadow = font.render(text, True, (20, 24, 34))
        rect = surface.get_rect(center=(self.width // 2, round(y)))
        self.screen.blit(shadow, rect.move(4, 4))
        self.screen.blit(surface, rect)

    def _cover(self, image: pygame.Surface, width: int, height: int) -> pygame.Surface:
        scale = max(width / image.get_width(), height / image.get_height())
        size = (round(image.get_width() * scale), round(image.get_height() * scale))
        scaled = pygame.transform.smoothscale(image, size)
        rect = scaled.get_rect(center=(width // 2, height // 2))
        surface = pygame.Surface((width, height))
        surface.blit(scaled, rect)
        return surface

    def _fit(self, image: pygame.Surface, max_width: int, max_height: int) -> pygame.Surface:
        scale = min(max_width / image.get_width(), max_height / image.get_height())
        size = (round(image.get_width() * scale), round(image.get_height() * scale))
        return pygame.transform.smoothscale(image, size)

    def _outside_sign_clip(self, edge: str) -> pygame.Rect:
        if edge == "top":
            return pygame.Rect(0, 0, self.width, self.visible_sign_rect.top)
        if edge == "bottom":
            return pygame.Rect(
                0,
                self.visible_sign_rect.bottom,
                self.width,
                self.height - self.visible_sign_rect.bottom,
            )
        if edge == "left":
            return pygame.Rect(0, 0, self.visible_sign_rect.left, self.height)
        return pygame.Rect(
            self.visible_sign_rect.right,
            0,
            self.width - self.visible_sign_rect.right,
            self.height,
        )

    def _alpha_world_rect(self, image: pygame.Surface, image_rect: pygame.Rect) -> pygame.Rect:
        local_rect = image.get_bounding_rect(1)
        return local_rect.move(image_rect.topleft)
