"""Rebuild news.json from AT2 News (~520 records) using the legislation.json shape.

Output schema:
  {
    "generated_at": ISO8601,
    "total": int,
    "rows": [ ...520 ],
    "facets": { region: {...}, story_type: {...}, tags: {...}, authority: {...} }
  }

Each row has: id, slug, headline, summary, source_url, date_published, jurisdiction_name,
iso, region, authority, story_type, tags (list), verified_status.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import collections
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
OUT = _ROOT / "news.json"
SLUG_MAP = _ROOT / "news_slug_map.json"
STATS = _ROOT / "stats.json"
NEWS_TABLE = "tbl15HFEi0fXTLZQc"


def fetch_all_news():
    base = os.environ["AIRTABLE_AT2_BASE"]
    token = os.environ["AIRTABLE_AT2_TOKEN"]
    url = f"https://api.airtable.com/v0/{base}/{NEWS_TABLE}"
    headers = {"Authorization": f"Bearer {token}"}
    records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.2)  # be polite to the AT API
    return records


def first(xs):
    return xs[0] if xs else None


_MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def fmt_date_display(iso):
    """ISO 'YYYY-MM-DD' -> '1 May 2026' (PAI house style; matches juris-page fmtDate)."""
    if not iso or len(iso) < 10:
        return None
    try:
        y, m, d = int(iso[0:4]), int(iso[5:7]), int(iso[8:10])
        return f"{d} {_MONTHS_SHORT[m - 1]} {y}"
    except (ValueError, IndexError):
        return None


def to_row(rec, slug_map):
    f = rec.get("fields", {})
    rid = rec["id"]
    headline = f.get("Name") or ""
    summary = f.get("Summary") or ""
    authority = first(f.get("Name (from Authorities)")) or None
    date_published = f.get("Date Published") or None
    return {
        "id": rid,
        "at2_id": rid,           # alias — older loaders read at2_id
        "slug": slug_map.get(rid),
        "headline": headline,
        "title": headline,        # alias — older loaders read .title
        "summary": summary,
        "source_url": f.get("Source URL") or "",
        "date_published": date_published,
        "date_display": fmt_date_display(date_published),  # alias — pre-formatted for legacy loaders ("1 May 2026")
        "jurisdiction_name": first(f.get("Name (from Jurisdiction)")) or None,
        "jurisdictions": f.get("Name (from Jurisdiction)") or [],
        "juris_isos": f.get("ISO Code (from Jurisdiction)") or [],
        "iso": first(f.get("ISO Code (from Jurisdiction)")) or None,
        "region": first(f.get("Region (from Jurisdiction)")) or None,
        "authority": authority,
        "body_name": authority,   # alias — older loaders read .body_name (the "body" = the regulator)
        "authority_type": first(f.get("Type (from Authorities)")) or None,
        "story_type": f.get("Story Type") or None,
        "tags": f.get("Tags") or [],
        "topic": (f.get("Tags") or [None])[0],   # legacy single-value field
        "verified_status": f.get("Verified Status") or None,
        "is_lead": bool(f.get("Is Lead")),   # editorial flag from AT2 News "Is Lead" checkbox; drives hero card on home + juris pages
    }


def build_facets(rows):
    """Pre-compute per-facet counts so the page doesn't have to."""
    fc = {
        "region": collections.Counter(),
        "story_type": collections.Counter(),
        "tags": collections.Counter(),
        "authority": collections.Counter(),
        "verified_status": collections.Counter(),
    }
    for r in rows:
        if r["region"]:
            fc["region"][r["region"]] += 1
        if r["story_type"]:
            fc["story_type"][r["story_type"]] += 1
        for t in r["tags"]:
            fc["tags"][t] += 1
        if r["authority"]:
            fc["authority"][r["authority"]] += 1
        if r["verified_status"]:
            fc["verified_status"][r["verified_status"]] += 1
    return {k: dict(v.most_common()) for k, v in fc.items()}


def main():
    print(f"Fetching AT2 News...", file=sys.stderr)
    records = fetch_all_news()
    print(f"Got {len(records)} records", file=sys.stderr)

    slug_map = json.loads(SLUG_MAP.read_text())
    rows = [to_row(r, slug_map) for r in records]
    # Sort by date_published desc (most recent first)
    rows.sort(key=lambda r: (r["date_published"] or ""), reverse=True)

    facets = build_facets(rows)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "rows": rows,
        "facets": facets,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} ({len(rows)} rows)", file=sys.stderr)

    # Update stats.json's news_count
    if STATS.exists():
        stats = json.loads(STATS.read_text())
        stats["news_count"] = len(rows)
        stats["generated_at"] = out["generated_at"]
        STATS.write_text(json.dumps(stats, indent=2))
        print(f"Updated {STATS} news_count -> {len(rows)}", file=sys.stderr)

    # Print facet summary
    print()
    for fname, counts in facets.items():
        print(f"=== {fname} ({len(counts)} unique) ===")
        for k, v in list(counts.items())[:10]:
            print(f"  {k or '(none)':30s} {v}")
        if len(counts) > 10:
            print(f"  ... and {len(counts) - 10} more")


if __name__ == "__main__":
    main()
