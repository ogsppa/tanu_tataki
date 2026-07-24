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
        self.source_background = background
        self.source_sign = sign
        self.width, self.height = screen.get_size()
        self._build_layout()

    def resize(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()
        self._build_layout()

    def _build_layout(self) -> None:
        self.background = self._cover(self.source_background, self.width, self.height)
        self.sign = self._fit(self.source_sign, int(self.width * 0.54), int(self.height * 0.46))
        self.sign_rect = self.sign.get_rect(center=(self.width // 2, self.height // 2))
        self.visible_sign_rect = self._alpha_world_rect(self.sign, self.sign_rect)
        self.sign_opaque_mask = pygame.mask.from_surface(self.sign, 0)
        self.sign_alpha_mask = self._alpha_mask(self.sign)
        font_name = self._font_name()
        self.font_title = pygame.font.SysFont(font_name, 76, bold=True)
        self.font_large = pygame.font.SysFont(font_name, 64, bold=True)
        self.font_medium = pygame.font.SysFont(font_name, 34, bold=True)
        self.font_small = pygame.font.SysFont(font_name, 24, bold=True)

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
            self._center_label("タヌたたき", self.visible_sign_rect.top - 82, self.font_title)
            start_button_rect = self.button_rect_for("start")
            self._button_label("すたーと！", start_button_rect)
            self._center_plain_label(
                "35点以上を取って限定ステッカーをげっとしよう！",
                start_button_rect.bottom + 44,
                self.font_small,
                (18, 46, 88),
            )
        elif state.screen == "countdown":
            self._center_label(state.countdown_text, self._countdown_y(state.countdown_text), self.font_title)
        elif state.screen == "result":
            self._center_label(f"FINISH  SCORE {state.score}", self.visible_sign_rect.top - 78, self.font_large)
            result_button_rect = self.button_rect_for("result")
            if state.has_prize_score:
                self._message_lines(
                    [
                        "おめでとう！限定ステッカーげっとだよ！",
                        "スタッフさんに",
                        "『タヌキとともだちになった！』",
                        "という合言葉を伝えてね",
                    ],
                    self._result_message_y(4, result_button_rect),
                )
            else:
                self._message_lines(
                    ["おしかった！", "よかったらまたあそんでね！"],
                    self._result_message_y(2, result_button_rect),
                )
            self._button_label("さいしょにもどる", result_button_rect)
        elif state.speed_up_timer > 0.0:
            self._center_label("SPEED UP", self.visible_sign_rect.top - 78, self.font_large)

    def _draw_debug(self, state: GameState) -> None:
        for point in state.last_points:
            color = (255, 238, 88) if point.active else (255, 255, 255)
            pygame.draw.circle(self.screen, color, (round(point.x), round(point.y)), 10, 2)

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

    def _center_plain_label(
        self, text: str, y: float, font: pygame.font.Font, color: tuple[int, int, int]
    ) -> None:
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(self.width // 2, round(y)))
        self.screen.blit(surface, rect)

    def _button_label(self, text: str, button_rect: pygame.Rect) -> None:
        surface = self.font_medium.render(text, True, (255, 255, 255))
        shadow = self.font_medium.render(text, True, (20, 24, 34))
        rect = surface.get_rect(center=button_rect.center)
        pygame.draw.rect(self.screen, (28, 42, 61), button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, width=2, border_radius=8)
        self.screen.blit(shadow, rect.move(3, 3))
        self.screen.blit(surface, rect)

    def _message_lines(self, lines: list[str], start_y: float) -> None:
        for index, line in enumerate(lines):
            self._center_label(line, start_y + index * 34, self.font_small)

    def _countdown_y(self, text: str) -> float:
        text_height = self.font_title.size(text)[1]
        safe_bottom = self.visible_sign_rect.top - 48
        desired = safe_bottom - text_height / 2
        return max(72, desired)

    def _result_message_y(self, line_count: int, button_rect: pygame.Rect) -> float:
        desired = self.visible_sign_rect.bottom + 36
        last_line_y = desired + (line_count - 1) * 34
        if last_line_y > button_rect.top - 26:
            desired = button_rect.top - 26 - (line_count - 1) * 34
        return max(self.visible_sign_rect.bottom + 28, desired)

    @property
    def menu_button_rect(self) -> pygame.Rect:
        return self.button_rect_for("start")

    def button_rect_for(self, screen_name: str) -> pygame.Rect:
        if screen_name == "result":
            center_y = self.height - 70
        else:
            center_y = max(self.visible_sign_rect.bottom + 74, self.height - 112)
        center = (self.width // 2, round(center_y))
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

    def _font_name(self) -> str:
        candidates = [
            "yugothic",
            "yu gothic",
            "meiryo",
            "noto sans cjk jp",
            "noto sans jp",
            "hiragino sans",
            "arial unicode ms",
            "arial",
        ]
        available = pygame.font.get_fonts()
        for candidate in candidates:
            key = candidate.replace(" ", "").lower()
            if key in available:
                return candidate
        return "arial"
