from __future__ import annotations

from typing import Mapping, Sequence

import pygame

from tanufre_whack.input.base import InputPoint


class UltraleapInput:
    def __init__(self, settings: Mapping[str, object]) -> None:
        self._settings = settings

    def get_points(self, events: Sequence[pygame.event.Event]) -> list[InputPoint]:
        return []

    def map_to_screen(self, hand_x: float, hand_y: float) -> tuple[float, float]:
        width = float(self._settings["screen_width"])
        height = float(self._settings["screen_height"])
        min_x = float(self._settings["leap_min_x"])
        max_x = float(self._settings["leap_max_x"])
        min_y = float(self._settings["leap_min_y"])
        max_y = float(self._settings["leap_max_y"])

        x = (hand_x - min_x) / (max_x - min_x) * width
        y = height - (hand_y - min_y) / (max_y - min_y) * height
        return x, y
