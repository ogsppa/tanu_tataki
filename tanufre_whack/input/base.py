from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import pygame


@dataclass(frozen=True)
class InputPoint:
    x: float
    y: float
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    active: bool = False
    source: str = "unknown"


class InputProvider(Protocol):
    def get_points(self, events: Sequence[pygame.event.Event]) -> list[InputPoint]:
        ...
