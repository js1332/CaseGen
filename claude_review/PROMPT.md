# CLAUDE REVIEW PROMPT (copy/paste)

You are reviewing a small webapp that wraps an existing Python golf-map renderer.

## Goal
Improve the webapp quality (UX, performance, reliability, and code cleanliness) while keeping behavior the same:
- User enters a location/course query
- App searches OSM for candidate `golf_course` polygons
- User selects a theme
- App renders a PNG and shows it in the browser

## What to inspect
- `web_app.py` (Flask API + error handling + response types)
- `templates/index.html` (UI behavior, loading states, robustness)
- `src/map_fetch.py` (search + caching logic; check correctness/perf)

## Known omissions / stubs
- `src/svg_render.py` is **intentionally stubbed** in this review folder because the real file in the main project is very large.
- If you need renderer internals to propose a change, say so explicitly and request the missing file or focus only on the web layer.

## Requested improvements (prioritize)
1. **Fix correctness issues**:
   - The UI currently builds a “course results list” but the backend rendering currently uses only the first search candidate. Make the selected course actually render (pass an `osm_id` or similar to `/api/render`).
2. **Performance**:
   - Add caching/avoiding repeated renders where possible.
   - Add request concurrency safeguards (avoid multiple expensive renders at once).
3. **Reliability & UX**:
   - Add better client-side loading/progress states, disable buttons while rendering, and handle slow requests gracefully.
   - Improve API error messages so the UI can show actionable feedback.
4. **Security hygiene**:
   - Ensure no API keys are embedded in responses or frontend.
   - Add basic protections (input validation, rate limiting hooks if appropriate).
5. **API design**:
   - Consider changing `/api/render` to accept structured JSON or more explicit params (`osm_id`, `slug`, etc.).
   - Make route responses consistent.

## Output format
Return:
1) A short bullet list of the highest-impact issues you found.
2) A concrete step-by-step plan to fix them.
3) If you propose code changes, provide complete updated code blocks for the specific files changed (or explain diffs precisely).

