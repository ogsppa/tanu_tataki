# -*- coding: utf-8 -*-
from __future__ import annotations

import pygame

from tanufre_whack.game.game_state import GameState
from tanufre_whack.game.mole import Mole
from tanufre_whack.game.settings import ASSET_DIR


class Renderer:
    def __init__(
        self,
        screen: pygame.Surface,
        background: pygame.Surface,
        menu_background: pygame.Surface,
        sign: pygame.Surface,
        title: pygame.Surface,
        instruction_tanu: pygame.Surface,
        instruction_ino: pygame.Surface,
        show_debug_cursor: bool,
    ) -> None:
        self.screen = screen
        self.show_debug_cursor = show_debug_cursor
        self.source_background = background
        self.source_menu_background = menu_background
        self.source_sign = sign
        self.source_title = title
        self.source_instruction_tanu = instruction_tanu
        self.source_instruction_ino = instruction_ino
        self.width, self.height = screen.get_size()
        self._build_layout()

    def resize(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()
        self._build_layout()

    def _build_layout(self) -> None:
        self.background = self._cover(self.source_background, self.width, self.height)
        square_size = self.height
        self.menu_square_rect = pygame.Rect(0, 0, square_size, square_size)
        self.menu_square_rect.center = (self.width // 2, self.height // 2)
        self.menu_background = self._cover(self.source_menu_background, self.width, self.height)
        self.sign = self._fit(self.source_sign, int(self.width * 0.54), int(self.height * 0.46))
        self.sign_rect = self.sign.get_rect(center=(self.width // 2, self.height // 2))
        self.visible_sign_rect = self._alpha_world_rect(self.sign, self.sign_rect)
        self.sign_opaque_mask = pygame.mask.from_surface(self.sign, 0)
        self.sign_alpha_mask = self._alpha_mask(self.sign)
        self.title = self._fit(self.source_title, int(self.width * 0.52), int(self.height * 0.46))
        self.instruction_tanu = self._fit(
            self.source_instruction_tanu, int(self.width * 0.22), int(self.height * 0.30)
        )
        self.instruction_ino = self._fit(
            self.source_instruction_ino, int(self.width * 0.24), int(self.height * 0.30)
        )
        self.font_title = self._font(76)
        self.font_large = self._font(64)
        self.font_reaction = self._font(48)
        self.font_combo = self._font(46)
        self.font_medium = self._font(34)
        self.font_small = self._font(24)
        self.font_instruction = self._font(30)

    def draw(self, state: GameState) -> None:
        if state.screen in ("start", "instructions"):
            self._draw_menu_background()
        else:
            self.screen.blit(self.background, (0, 0))
        if state.screen in ("playing", "countdown", "result"):
            self._draw_moles(state.moles)
            self.screen.blit(self.sign, self.sign_rect)
            self._draw_hit_reactions(state.moles)
        self._draw_hud(state)
        if self.show_debug_cursor:
            self._draw_debug(state)
        pygame.display.flip()

    def _draw_menu_background(self) -> None:
        self.screen.blit(self.menu_background, (0, 0))
        pygame.draw.rect(self.screen, (255, 255, 255), self.menu_square_rect)

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

    def _draw_hit_reactions(self, moles: list[Mole]) -> None:
        reactions = {"tanuki": "うわ！", "boar": "ギャ！", "hamster": "ぴー！"}
        for mole in moles:
            if mole.state != "hit":
                continue
            text = reactions.get(mole.name)
            if text is None:
                continue
            self._reaction_label(text, self._reaction_position(mole))

    def _reaction_position(self, mole: Mole) -> tuple[int, int]:
        rect = mole.draw_rect
        x = rect.centerx
        y = rect.top - 18
        if mole.edge == "bottom":
            y = rect.bottom + 22
        elif mole.edge == "left":
            x = rect.left - 46
            y = rect.centery
        elif mole.edge == "right":
            x = rect.right + 46
            y = rect.centery
        return (
            round(max(88, min(self.width - 88, x))),
            round(max(88, min(self.height - 62, y))),
        )

    def _draw_hud(self, state: GameState) -> None:
        if state.screen in ("playing", "countdown", "result"):
            self._label(f"SCORE {state.score}", 28, 24, self.font_medium)
            self._label(f"TIME {int(state.remaining_seconds + 0.999):02d}", self.width - 190, 24, self.font_medium)
        if state.screen == "playing" and state.combo_count >= 2:
            self._combo_label(f"{state.combo_count}れんぞく！", 132, state.combo_bonus_timer > 0.0)
        if state.screen == "start":
            title_rect = self.title.get_rect(center=(self.width // 2, round(self.height * 0.34)))
            self.screen.blit(self.title, title_rect)
            start_button_rect = self.button_rect_for("start")
            self._button_label("すたーと！", start_button_rect)
            self._center_plain_label(
                "50てんいじょうで 合言葉をげっとしよう！",
                start_button_rect.bottom + 44,
                self.font_small,
                (18, 46, 88),
            )
        elif state.screen == "instructions":
            self._draw_instructions()
        elif state.screen == "countdown":
            self._center_label(state.countdown_text, self._countdown_y(state.countdown_text), self.font_title)
        elif state.screen == "result":
            self._center_label(f"FINISH  SCORE {state.score}", self.visible_sign_rect.top - 78, self.font_large)
            result_button_rect = self.button_rect_for("result")
            if state.has_prize_score:
                self._message_lines(
                    [
                        "もくひょうクリアー！おめでとう♪",
                        "合言葉は「てんさい」だよ！",
                    ],
                    self._result_message_y(2, result_button_rect),
                    (18, 46, 88),
                )
            else:
                self._message_lines(
                    ["おしかった！", "よかったらまたあそんでね！"],
                    self._result_message_y(2, result_button_rect),
                    (18, 46, 88),
                )
            self._button_label("さいしょにもどる", result_button_rect)
        elif state.speed_up_timer > 0.0:
            self._center_label("SPEED UP", 64, self.font_large)

    def _draw_instructions(self) -> None:
        lines = [
            "まんなかのかんばんから、",
            "タヌキ、イノシシさん、ハムさんがとびだすよ！",
            "でてきたらタップしよう！",
        ]
        for index, line in enumerate(lines):
            self._center_plain_label(line, 118 + index * 42, self.font_instruction, (18, 46, 88))

        total_width = self.instruction_tanu.get_width() + self.instruction_ino.get_width() + 72
        left = self.width // 2 - total_width // 2
        image_bottom = self.height - 190
        tanu_rect = self.instruction_tanu.get_rect(bottomleft=(left, image_bottom))
        ino_rect = self.instruction_ino.get_rect(bottomleft=(tanu_rect.right + 72, image_bottom))
        self.screen.blit(self.instruction_tanu, tanu_rect)
        self.screen.blit(self.instruction_ino, ino_rect)
        self._button_label("げーむすたーと", self.button_rect_for("instructions"))

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

    def _reaction_label(self, text: str, center: tuple[int, int]) -> None:
        stroke = self.font_reaction.render(text, True, (18, 46, 88))
        surface = self.font_reaction.render(text, True, (255, 217, 74))
        rect = surface.get_rect(center=center)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
            self.screen.blit(stroke, rect.move(dx, dy))
        self.screen.blit(surface, rect)

    def _combo_label(self, text: str, y: float, show_bonus: bool) -> None:
        stroke = self.font_combo.render(text, True, (18, 46, 88))
        surface = self.font_combo.render(text, True, (255, 217, 74))
        rect = surface.get_rect(center=(self.width // 2, round(y)))
        for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)):
            self.screen.blit(stroke, rect.move(dx, dy))
        self.screen.blit(surface, rect)
        if show_bonus:
            bonus_stroke = self.font_medium.render("+3", True, (18, 46, 88))
            bonus = self.font_medium.render("+3", True, (255, 217, 74))
            bonus_rect = bonus.get_rect(center=(rect.right + 48, rect.centery))
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
                self.screen.blit(bonus_stroke, bonus_rect.move(dx, dy))
            self.screen.blit(bonus, bonus_rect)

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

    def _message_lines(
        self, lines: list[str], start_y: float, color: tuple[int, int, int] | None = None
    ) -> None:
        for index, line in enumerate(lines):
            y = start_y + index * 34
            if color is None:
                self._center_label(line, y, self.font_small)
            else:
                self._center_plain_label(line, y, self.font_small, color)

    def _countdown_y(self, text: str) -> float:
        return self._notice_y(text, self.font_title)

    def _notice_y(self, text: str, font: pygame.font.Font) -> float:
        text_height = font.size(text)[1]
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
        elif screen_name == "instructions":
            center_y = self.height - 76
        elif screen_name == "start":
            center_y = self.height - 158
        else:
            center_y = self.visible_sign_rect.bottom + 74
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

    def _font(self, size: int) -> pygame.font.Font:
        font_path = ASSET_DIR / "fonts" / "NotoSansJP-VF.ttf"
        if font_path.exists():
            font = pygame.font.Font(str(font_path), size)
        else:
            font = pygame.font.SysFont(self._font_name(), size, bold=True)
        font.set_bold(True)
        return font

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
