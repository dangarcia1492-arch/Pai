"""Rebuild guidance.json from AT2 Guidance Documents table, mirroring build_news_json.py.

Output schema:
  {
    "generated_at": ISO8601,
    "total": int,
    "rows": [...],
    "facets": { region, status, topics, authority, jurisdiction }
  }

Each row has: id, at2_id, slug, title, summary, status, source_url, decision_date,
published_date, jurisdictions, juris_isos, iso, regions, region, authorities,
authority_types, authority, topics, archived.
"""
import collections
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
OUT = _ROOT / "guidance.json"
GUIDANCE_TABLE = "tblYJbTFOlj13Rs8Y"


def fetch_all(table_id):
    base = os.environ["AIRTABLE_AT2_BASE"]
    token = os.environ["AIRTABLE_AT2_TOKEN"]
    url = f"https://api.airtable.com/v0/{base}/{table_id}"
    headers = {"Authorization": f"Bearer {token}"}
    records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.2)
    return records


def first(xs):
    return xs[0] if xs else None


def kebab_slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return s or "untitled"


def assign_slugs(records):
    seen = {}
    out = {}
    for rec in records:
        base = kebab_slug(rec.get("fields", {}).get("Title") or "")
        n = seen.get(base, 0) + 1
        seen[base] = n
        out[rec["id"]] = base if n == 1 else f"{base}-{n}"
    return out


def to_row(rec, slug_map):
    f = rec.get("fields", {})
    rid = rec["id"]
    title = f.get("Title") or ""
    authority = first(f.get("Name (from Authorities)")) or None
    return {
        "id": rid,
        "at2_id": rid,
        "slug": slug_map.get(rid),
        "title": title,
        "summary": f.get("Summary") or "",
        "status": f.get("Status") or None,
        "source_url": f.get("Source URL") or "",
        "decision_date": f.get("Decision Date") or None,
        "published_date": f.get("Published Date") or None,
        "jurisdictions": f.get("Name (from Jurisdictions)") or [],
        "juris_isos": f.get("ISO Code (from Jurisdictions)") or [],
        "iso": first(f.get("ISO Code (from Jurisdictions)")) or None,
        "regions": f.get("Region (from Jurisdictions)") or [],
        "region": first(f.get("Region (from Jurisdictions)")) or None,
        "authorities": f.get("Name (from Authorities)") or [],
        "authority_types": f.get("Type (from Authorities)") or [],
        "authority": authority,
        "topics": f.get("Topics") or [],
        "archived": bool(f.get("Archived")),
    }


def build_facets(rows):
    fc = {
        "region": collections.Counter(),
        "status": collections.Counter(),
        "topics": collections.Counter(),
        "authority": collections.Counter(),
        "jurisdiction": collections.Counter(),
    }
    for r in rows:
        if r["region"]:
            fc["region"][r["region"]] += 1
        if r["status"]:
            fc["status"][r["status"]] += 1
        if r["authority"]:
            fc["authority"][r["authority"]] += 1
        for t in r["topics"]:
            fc["topics"][t] += 1
        for j in r["jurisdictions"]:
            fc["jurisdiction"][j] += 1
    return {k: dict(v.most_common()) for k, v in fc.items()}


def main():
    print("Fetching AT2 Guidance Documents...", file=sys.stderr)
    records = fetch_all(GUIDANCE_TABLE)
    print(f"Got {len(records)} records", file=sys.stderr)

    slug_map = assign_slugs(records)
    rows = [to_row(r, slug_map) for r in records]
    rows.sort(key=lambda r: (r["published_date"] or r["decision_date"] or ""), reverse=True)

    facets = build_facets(rows)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "rows": rows,
        "facets": facets,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} ({len(rows)} rows)", file=sys.stderr)

    print()
    for fname, counts in facets.items():
        print(f"=== {fname} ({len(counts)} unique) ===")
        for k, v in list(counts.items())[:10]:
            print(f"  {k or '(none)':30s} {v}")
        if len(counts) > 10:
            print(f"  ... and {len(counts) - 10} more")


if __name__ == "__main__":
    main()
