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
        self.sign_alpha_mask = self._alpha_mask(self.sign)
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
        mole_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for mole in moles:
            if mole.state == "hidden":
                continue
            image = mole.image
            rect = mole.draw_rect
            mole_layer.blit(image, rect)
        mole_layer.blit(self.sign_alpha_mask, self.sign_rect, special_flags=pygame.BLEND_RGBA_SUB)
        self.screen.blit(mole_layer, (0, 0))

    def _draw_hud(self, state: GameState) -> None:
        self._label(f"SCORE {state.score}", 28, 24, self.font_medium)
        self._label(f"TIME {int(state.remaining_seconds + 0.999):02d}", self.width - 190, 24, self.font_medium)
        if state.screen == "start":
            self._center_label("TANUFRE WHACK", self.visible_sign_rect.top - 78, self.font_large)
            self._button_label("START", self.visible_sign_rect.bottom + 74)
        elif state.screen == "result":
            self._center_label(f"FINISH  SCORE {state.score}", self.visible_sign_rect.top - 78, self.font_large)
            self._button_label("BACK TO START", self.visible_sign_rect.bottom + 74)

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

    def _button_label(self, text: str, y: float) -> None:
        surface = self.font_medium.render(text, True, (255, 255, 255))
        shadow = self.font_medium.render(text, True, (20, 24, 34))
        rect = surface.get_rect(center=(self.width // 2, round(y)))
        button_rect = self.menu_button_rect
        pygame.draw.rect(self.screen, (28, 42, 61), button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, width=2, border_radius=8)
        self.screen.blit(shadow, rect.move(3, 3))
        self.screen.blit(surface, rect)

    @property
    def menu_button_rect(self) -> pygame.Rect:
        center = (self.width // 2, round(self.visible_sign_rect.bottom + 74))
        return pygame.Rect(0, 0, 360, 76).move(center[0] - 180, center[1] - 38)

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

    def _alpha_world_rect(self, image: pygame.Surface, image_rect: pygame.Rect) -> pygame.Rect:
        local_rect = image.get_bounding_rect(1)
        return local_rect.move(image_rect.topleft)

    def _alpha_mask(self, image: pygame.Surface) -> pygame.Surface:
        mask = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        width, height = image.get_size()
        for y in range(height):
            for x in range(width):
                alpha = image.get_at((x, y)).a
                if alpha:
                    mask.set_at((x, y), (0, 0, 0, alpha))
        return mask
