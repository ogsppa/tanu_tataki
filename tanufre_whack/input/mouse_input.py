from __future__ import annotations

from typing import Sequence

import pygame

from tanufre_whack.input.base import InputPoint


class MouseInput:
    def get_points(self, events: Sequence[pygame.event.Event]) -> list[InputPoint]:
        x, y = pygame.mouse.get_pos()
        active = any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 for event in events
        )
        return [InputPoint(x=float(x), y=float(y), active=active, source="mouse")]
