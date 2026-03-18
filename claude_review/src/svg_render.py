# NOTE:
# This file is intentionally not fully copied here because `src/svg_render.py`
# is very large (~2500 lines). For Claude Code review, point it to the
# original `src/svg_render.py` in your main repo, or attach it separately.
#
# If you want, I can instead create a full copy, but it will be large and
# may exceed Claude’s upload limits.

from pathlib import Path

# Provide a minimal shim so Claude can at least run type-level reasoning.
STYLE_COLORS = {"minimalist": {"fairway": "#ffffff", "outline": "#00481A", "text": "#00481A"}}

def render_direct_to_png(*args, **kwargs):
    raise RuntimeError("Stub: please use src/svg_render.py from the main project.")

