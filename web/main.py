from __future__ import annotations

import asyncio

import pygame  # Imported here so pygbag bundles the pygame runtime.

from tanufre_whack.main import main_async


asyncio.run(main_async())
