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
uv run python tools/finalize_web_build.py
```

The static site is generated under `web-src/build/web`.

## Lightweight JavaScript build

`web-js` contains a Canvas version for older tablets and browsers. It does not load Python, WebAssembly, pygame, or the bundled Japanese font.

Open `web-js/index.html` directly, or serve the folder as a static site.

## Cloudflare Workers Builds

`wrangler.toml` points Cloudflare Workers static assets at the lightweight JavaScript build:

```text
web-js
```

Use this build command for the lightweight JavaScript build:

```text
echo "No build step"
```

Use this deploy command:

```text
npx wrangler deploy
```

Leave Version command and Root directory blank unless Cloudflare asks for a custom value.

GitHub Pages deployment is handled by `.github/workflows/deploy-pages.yml`.
