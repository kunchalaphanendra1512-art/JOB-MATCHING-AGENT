import json
import urllib.request
from urllib.error import HTTPError, URLError

BASE = "http://localhost:3000"

def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            print(f"GET {path} -> {r.status}")
            print(r.read().decode())
    except Exception as e:
        print(f"GET {path} failed: {e}")


def post_job():
    job = {
        "title": "Integration Test Job",
        "required_skills": ["python"],
        "preferred_skills": [],
        "min_experience": 0,
        "location": "Remote",
        "role_type": "remote"
    }
    data = json.dumps(job).encode("utf-8")
    req = urllib.request.Request(BASE + "/api/jobs", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"POST /api/jobs -> {r.status}")
            print(r.read().decode())
    except HTTPError as he:
        body = he.read().decode() if he.fp else ""
        print(f"HTTPError {he.code}: {body}")
    except URLError as ue:
        print(f"URLError: {ue}")
    except Exception as e:
        print(f"POST failed: {e}")


if __name__ == '__main__':
    get("/")
    post_job()
    get("/api/jobs")
