"""Rebuild authorities.json from AT2 Authorities (~2,400 records), AT2-direct pattern.

Replaces the deprecated pai-intake/scripts/build_authorities.py (PG-mirror →
pai-intake/www/authorities.json, output unused as of 2026-05-12).

Output: flat JSON list (preserves existing Pai-edit/authorities.json shape).
Each row matches the legacy keys consumer pages already read.

Run:
    set -a; . /Users/claude-sandbox/secrets/intake.env; set +a
    python3 scripts/build_authorities.py

Refs PRI-157, PRI-156.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
OUT = _ROOT / "authorities.json"

AUTH_TBL = "tbllcAd8ZqWdLmVyr"   # AT2 Authorities
JURIS_TBL = "tblE2iljzLCoMqIS5"  # AT2 Jurisdictions (for linked-record dereference)


def fetch_all(table_id):
    """Paginated fetch of every record in an AT2 table."""
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
        time.sleep(0.2)  # be polite to the AT2 API
    return records


def first(xs):
    return xs[0] if xs else None


def build_juris_map(juris_records):
    """{recId: name} for resolving linked Jurisdiction fields."""
    m = {}
    for rec in juris_records:
        name = (rec.get("fields") or {}).get("Name")
        if name:
            m[rec["id"]] = name
    return m


def to_row(rec, juris_map, synced_at):
    """Map one AT2 Authorities record → output row matching legacy schema."""
    f = rec.get("fields") or {}
    juris_id = first(f.get("Jurisdiction") or [])
    juris_name = juris_map.get(juris_id) if juris_id else None
    return {
        "id": rec["id"],
        "name": f.get("Name") or "",
        "jurisdiction": juris_name,
        "type": f.get("Type"),
        "status": f.get("Verified Status"),
        "url": f.get("URL"),
        # Legacy fields from the deprecated PG-mirror schema. Kept as null so existing
        # consumer pages that read these keys don't break. Future: drop entirely once
        # consumers are audited (separate ticket).
        "major_source": f.get("Major"),
        "confidence_score": None,
        "confidence_level": None,
        "items_per_week": None,
        "last_new_content": None,
        # New from AT2 (not in legacy schema, additive)
        "acronym": f.get("Acronym"),
        "verified_date": f.get("Verified Date"),
        "synced_at": synced_at,
    }


def main():
    if not os.environ.get("AIRTABLE_AT2_BASE") or not os.environ.get("AIRTABLE_AT2_TOKEN"):
        sys.exit("ERROR: source /Users/claude-sandbox/secrets/intake.env first")

    print("Fetching AT2 Jurisdictions (for linked-record deref)...", file=sys.stderr)
    juris = fetch_all(JURIS_TBL)
    juris_map = build_juris_map(juris)
    print(f"  {len(juris_map)} jurisdictions loaded", file=sys.stderr)

    print("Fetching AT2 Authorities...", file=sys.stderr)
    auths = fetch_all(AUTH_TBL)
    print(f"  {len(auths)} authorities fetched", file=sys.stderr)

    synced_at = datetime.now(timezone.utc).isoformat()
    rows = [to_row(r, juris_map, synced_at) for r in auths]

    # Sort: jurisdiction (None last), then name — matches legacy ordering
    rows.sort(key=lambda r: ((r.get("jurisdiction") or "￿"), r.get("name") or ""))

    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} ({len(rows)} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
