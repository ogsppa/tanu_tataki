# Tanufre Whack

Pygame based whack-a-mole style prototype for projector display.

The first playable version uses mouse input. The input layer is separated so an Ultraleap provider can be wired in later without changing the game rules.

## Setup

```powershell
uv sync
uv run tanufre-whack
```

For development, the keyboard fallback can also hit targets with `1`, `2`, and `3`.
