# scorecard_api.py
import requests
import os

API_KEY = os.getenv("4QRS55UWB366HW2DMBE43LST2U")
BASE_URL = "https://api.golfcourseapi.com"


def fetch_course_metadata(course_name):
    headers = {"Authorization": "Key 4QRS55UWB366HW2DMBE43LST2U"}
    try:
        search_url = f"{BASE_URL}/v1/search?search_query={course_name}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        courses = resp.json().get("courses", [])
        if not courses:
            return None
        course_id = courses[0]["id"]
        details_url = f"{BASE_URL}/v1/courses/{course_id}"
        resp = requests.get(details_url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None

