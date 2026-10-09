#!/usr/bin/env python3
"""Standard-library-only, fail-closed importer of approved Greenhouse employer boards."""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data/vacancy-sources.json"
OUTPUT = ROOT / "data/vacancies.json"
MAX_JOBS = 10000

def fetch_board(token):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{2,80}", token):
        raise ValueError("Invalid board token")
    url = "https://boards-api.greenhouse.io/v1/boards/" + token + "/jobs"
    request = urllib.request.Request(url, headers={"User-Agent": "VerveNVeda-Finance-Jobs/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("Board payload too large")
    payload = json.loads(raw)
    if not isinstance(payload.get("jobs"), list):
        raise ValueError("Invalid board response")
    return payload["jobs"]

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    boards = config.get("greenhouse_boards", [])
    if not isinstance(boards, list) or not boards:
        print("No approved boards configured; leaving existing vacancy dataset untouched.")
        return 0
    if len(boards) > 30:
        raise ValueError("Too many boards")
    records = {}
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    for entry in boards:
        if not isinstance(entry, dict) or entry.get("approved") is not True:
            raise ValueError("Every board requires explicit approval")
        token = entry["token"]
        company = entry["company"]
        if not isinstance(company, str) or not company.strip() or len(company) > 120:
            raise ValueError("Invalid company")
        for item in fetch_board(token):
            if not isinstance(item, dict) or item.get("internal_job_id") is None:
                continue
            link = item.get("absolute_url", "")
            if not isinstance(link, str) or not link.startswith("https://"):
                continue
            title = item.get("title", "")
            if not isinstance(title, str) or not title.strip():
                continue
            location = (item.get("location") or {}).get("name", "")
            if not isinstance(location, str):
                location = ""
            updated = str(item.get("updated_at", ""))[:10]
            try:
                dt.date.fromisoformat(updated)
            except ValueError:
                updated = today
            job_id = str(item.get("id", ""))
            if not job_id.isdigit():
                continue
            record = {
                "id": token + ":" + job_id,
                "title": title[:500],
                "company": company[:500],
                "city": location[:500],
                "state": "",
                "country": "",
                "postal_code": "",
                "work_arrangement": "remote" if "remote" in location.lower() else "onsite",
                "apply_url": link[:500],
                "posted_at": updated,
                "source": "Employer careers (Greenhouse)"
            }
            records[record["id"]] = record
            if len(records) > MAX_JOBS:
                raise ValueError("Job limit exceeded")
    if not records:
        raise ValueError("No jobs returned: refusing to replace existing dataset")
    data = {"schema_version": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "jobs": sorted(records.values(), key=lambda j: j["id"])}
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUTPUT)
    print("Validated jobs:", len(records))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("REFRESH FAILED (existing data preserved):", exc, file=sys.stderr)
        sys.exit(1)
