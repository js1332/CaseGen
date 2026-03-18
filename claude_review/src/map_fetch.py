import osmnx as ox, json, re
from pathlib import Path
import difflib
import pandas as pd
from shapely.geometry import shape, Point as ShapelyPoint

CACHE = Path(__file__).parent.parent / "data_cache"
CACHE_VERSION = 3
CACHE.mkdir(exist_ok=True)


def slugify(name):
    return re.sub(r'\W+', '_', name.lower()).strip('_')


def search_courses(query, limit=5):
    def normalize_name(s: str) -> str:
        s = (s or '').lower()
        s = re.sub(r"\b(golf|club|course|the)\b", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def token_score(a: str, b: str) -> float:
        stop = {"golf", "club", "course", "the"}
        ta = [t for t in re.split(r"\W+", a.lower()) if t and t not in stop]
        tb = [t for t in re.split(r"\W+", b.lower()) if t and t not in stop]
        if not ta or not tb:
            return 0.0
        inter = len(set(ta) & set(tb))
        union = len(set(ta) | set(tb))
        return inter / union

    location_gdf = ox.geocode_to_gdf(query)
    if location_gdf.empty:
        return []

    center_geom = location_gdf.iloc[0].geometry.centroid
    lat, lon = center_geom.y, center_geom.x

    golf_boundaries = ox.features_from_point(
        (lat, lon),
        tags={'leisure': 'golf_course'},
        dist=3000
    )

    if golf_boundaries.empty:
        return []

    q_norm = normalize_name(query)
    candidates = []
    for _, row in golf_boundaries.iterrows():
        course_name = row.get('name', 'Unnamed')
        geom_centroid = row.geometry.centroid
        distance = ox.distance.great_circle(lat, lon, geom_centroid.y, geom_centroid.x)
        sim = difflib.SequenceMatcher(None, query.lower(), course_name.lower()).ratio()
        tok = token_score(query, course_name)
        norm_eq = 1 if normalize_name(course_name) == q_norm else 0
        candidates.append((norm_eq, tok, sim, -distance, row, course_name, geom_centroid))

    filtered = [c for c in candidates if (c[0] == 1) or (c[1] >= 0.5) or (c[2] >= 0.85)]
    if not filtered:
        filtered = [c for c in candidates if (-c[3]) <= 3000]

    filtered.sort(key=lambda t: (t[0], t[1], t[2], t[3]), reverse=True)

    out = []
    for tpl in filtered[:limit]:
        _, _, _, _, row, course_name, geom_centroid = tpl
        out.append({
            "display_name": course_name,
            "lat": geom_centroid.y,
            "lon": geom_centroid.x,
            "osm_id": row.name[1],
            "slug": slugify(course_name)
        })
    return out


def fetch_and_cache_course(course):
    from shapely.geometry import box

    slug = course['slug']
    cache = CACHE / f"{slug}.geojson"
    MIN_GOLF_FEATURES = 150
    if cache.exists():
        cached = json.loads(cache.read_text())
        cache_ver = cached.get('cache_version', 0)
        golf_count_cached = sum(1 for f in cached.get('features', []) if (f.get('properties', {}).get('golf') or '') != '')
        if cache_ver >= CACHE_VERSION and golf_count_cached >= MIN_GOLF_FEATURES:
            return cached

    boundary_tags = {'leisure': 'golf_course'}
    boundary_gdf = ox.features_from_point(
        (course['lat'], course['lon']),
        tags=boundary_tags,
        dist=7000
    )

    if boundary_gdf.empty:
        return None

    selected_row = None
    if course.get('osm_id') is not None:
        try:
            match = boundary_gdf.loc[boundary_gdf.index.get_level_values(1) == course['osm_id']]
            if not match.empty:
                selected_row = match.iloc[0]
        except Exception:
            selected_row = None

    if selected_row is None:
        center_point = ShapelyPoint(course['lon'], course['lat'])
        boundary_gdf = boundary_gdf.copy()
        boundary_gdf['__centroid'] = boundary_gdf.geometry.centroid
        boundary_gdf['__distance'] = boundary_gdf['__centroid'].distance(center_point)
        candidates = boundary_gdf.sort_values('__distance').head(20)
        best = None
        for _, row in candidates.iterrows():
            geom = row.geometry
            try:
                gf = ox.features_from_polygon(geom, tags={'golf': True})
                golf_count = len(gf)
            except Exception:
                golf_count = 0
            name = (row.get('name') or '').lower()
            sim = difflib.SequenceMatcher(None, (course['display_name'] or '').lower(), name).ratio()
            score = (golf_count, sim)
            if best is None or score > best[0]:
                best = (score, row)
        selected_row = best[1]

    course_boundary_geom = selected_row.geometry if hasattr(selected_row.geometry, 'geom_type') else shape(selected_row.geometry)

    try:
        filtered_golf = ox.features_from_polygon(course_boundary_geom, tags={'golf': True})
    except Exception:
        golf_features_gdf = ox.features_from_point((course['lat'], course['lon']), tags={'golf': True}, dist=2000)
        golf_features_gdf['within_boundary'] = golf_features_gdf.geometry.apply(
            lambda geom: geom.within(course_boundary_geom) or geom.intersects(course_boundary_geom)
        )
        filtered_golf = golf_features_gdf[golf_features_gdf['within_boundary']]

    final_gdf = filtered_golf
    drop_cols = [c for c in final_gdf.columns if c.startswith('__')]
    if drop_cols:
        final_gdf = final_gdf.drop(columns=drop_cols, errors='ignore')
    gj = json.loads(final_gdf.to_json())
    gj['cache_version'] = CACHE_VERSION
    cache.write_text(json.dumps(gj))
    return gj

