from __future__ import annotations

from typing import Sequence

import pygame

from tanufre_whack.input.base import InputPoint


class KeyboardInput:
    def __init__(self, target_points: Sequence[tuple[float, float]]) -> None:
        self._target_points = list(target_points)
        self._keys = [pygame.K_1, pygame.K_2, pygame.K_3]

    def get_points(self, events: Sequence[pygame.event.Event]) -> list[InputPoint]:
        points: list[InputPoint] = []
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key not in self._keys:
                continue
            index = self._keys.index(event.key)
            if index >= len(self._target_points):
                continue
            x, y = self._target_points[index]
            points.append(InputPoint(x=x, y=y, active=True, source="keyboard"))
        return points
