#!/usr/bin/env python3

import json
import pandas as pd
from pathlib import Path
from map_fetch import fetch_and_cache_course, slugify, CACHE
import csv


def extract_hole_data_from_geojson(geojson, course_name):
    hole_data = []
    if not geojson or "features" not in geojson:
        return hole_data
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        golf_type = (props.get("golf") or "").lower()
        if golf_type == "hole":
            hole_number = props.get("ref", props.get("ref:golf", ""))
            hole_name = props.get("name", "")
            par = props.get("par", "")
            length = props.get("length", "")
            if hole_number:
                hole_data.append({
                    "course_name": course_name,
                    "hole_number": hole_number,
                    "hole_name": hole_name,
                    "par": par,
                    "length": length
                })
    return hole_data


def export_all_courses_to_csv(csv_path="golf_courses_top20_per_city.csv", output_path="golf_course_holes.csv"):
    course_data = []
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_data.append(row)
    except Exception:
        return

    all_hole_data = []
    for i, course in enumerate(course_data, 1):
        course_name = course.get("course_name", "Unknown")
        try:
            course_obj = {
                "display_name": course_name,
                "lat": float(course.get("lat", 0)),
                "lon": float(course.get("lon", 0)),
                "osm_id": course.get("osm_id", ""),
                "slug": course.get("slug", slugify(course_name))
            }
            has_valid_coords = course_obj["lat"] != 0 and course_obj["lon"] != 0
            if not has_valid_coords:
                cache_file = CACHE / f"{course_obj['slug']}.geojson"
                if cache_file.exists():
                    geojson = json.loads(cache_file.read_text())
                else:
                    continue
            else:
                geojson = fetch_and_cache_course(course_obj)
            if geojson:
                hole_data = extract_hole_data_from_geojson(geojson, course_name)
                all_hole_data.extend(hole_data)
        except Exception:
            continue

    if all_hole_data:
        df = pd.DataFrame(all_hole_data)
        df['hole_number'] = pd.to_numeric(df['hole_number'], errors='coerce')
        df = df.sort_values(['course_name', 'hole_number'])
        df.to_csv(output_path, index=False)


if __name__ == "__main__":
    export_all_courses_to_csv()

