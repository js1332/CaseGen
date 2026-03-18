# Golf Map Generator (Web Review Pack)

This folder exists to make it easy to review/improve the web app layer with Claude Code.

## What’s included

- `web_app.py`: Flask API (search + render)
- `templates/index.html`: Front-end UI
- `src/map_fetch.py`: OSM/OSMNX course search + GeoJSON fetch/caching
- `src/svg_render.py`: **Stubbed** renderer for keeping this review pack small
- `requirements.txt`: Python dependencies

## Important: renderer is stubbed

This review pack intentionally contains a small stub at `src/svg_render.py`.
As a result, `/api/render` will fail until you replace the stub with the real
renderer file from your main project:

- Replace `claude_review/src/svg_render.py` with the full `src/svg_render.py`
  from `golfmap_generator/src/svg_render.py`.

## Run locally (after installing deps)

```bash
cd claude_review
pip install -r requirements.txt
python web_app.py
```

Then open:

- `http://127.0.0.1:5000/`

## Notes for GitHub

- Do not commit runtime-generated caches (if/when created), e.g. `data_cache/`.
- If you want a fully working web app on other computers, you must include
  the full `src/svg_render.py` (not the stub).

