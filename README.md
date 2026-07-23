# Tanufre Whack

Pygame based whack-a-mole style prototype for projector display.

The first playable version uses mouse input. The input layer is separated so an Ultraleap provider can be wired in later without changing the game rules.

## Setup

```powershell
uv sync
uv run tanufre-whack
```

For development, the keyboard fallback can also hit targets with `1`, `2`, and `3`.

## Web build

The browser build uses pygbag.

```powershell
uv sync --dev
uv run python tools/prepare_web_build.py
uv run pygbag --build --ume_block 0 --width 1600 --height 900 --app_name tanufre-whack web-src
```

The static site is generated under `web-src/build/web`.

GitHub Pages deployment is handled by `.github/workflows/deploy-pages.yml`.
