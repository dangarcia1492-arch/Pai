#!/usr/bin/env python3
"""Rebuild news_slug_map.json by reverse-matching disk files to AT2 records.

Default: dry-run (prints stats, does not write). Pass --write to update the map.

Diagnosis: May-8 AT2 Name rewrite regenerated truncated slugs that no longer
match historical pai-app-news-story-*.html filenames on disk. This rebuilds
the map by matching each AT2 record to its on-disk story file via:
  1. Normalized Source URL match against slug-form filenames (preferred)
  2. Rec-id-form filename as fallback (pai-app-news-story-{rid}.html)
"""
import json, os, re, sys, time
import urllib.request, urllib.parse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG_MAP = ROOT / "news_slug_map.json"
NEWS_TABLE = "tbl15HFEi0fXTLZQc"

INTERNAL_HOSTS = (
    'fonts.googleapis', 'fonts.gstatic', 'principlesai.org',
    'cdnjs', 'jsdelivr', 'unpkg', 'tailwindcss',
)


def fetch_at2_records():
    base = os.environ["AIRTABLE_AT2_BASE"]
    token = os.environ["AIRTABLE_AT2_TOKEN"]
    url_base = f"https://api.airtable.com/v0/{base}/{NEWS_TABLE}"
    headers = {"Authorization": f"Bearer {token}"}
    records, offset = [], None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        full = url_base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.2)
    return records


def normalize_url(u):
    if not u:
        return ''
    u = u.strip().lower()
    u = re.sub(r'^https?://(www\.)?', '', u)
    u = u.split('?')[0].split('#')[0].rstrip('/')
    return u


def extract_source_url(html):
    """First external href that isn't a font / CDN / internal pai link."""
    for m in re.finditer(r'href="(https?://[^"]+)"', html):
        u = m.group(1)
        if any(h in u for h in INTERNAL_HOSTS):
            continue
        return u
    return None


def main():
    write = '--write' in sys.argv
    rec_pat = re.compile(r'^pai-app-news-story-(rec[A-Za-z0-9]{14,17})\.html$')

    rec_files = {}
    slug_files = {}
    skipped_no_url = []

    for entry in os.listdir(ROOT):
        if not (entry.startswith('pai-app-news-story-') and entry.endswith('.html')):
            continue
        m = rec_pat.match(entry)
        if m:
            rec_files[m.group(1)] = m.group(1)
            continue
        slug = entry[len('pai-app-news-story-'):-len('.html')]
        try:
            html = (ROOT / entry).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        src = extract_source_url(html)
        if src:
            slug_files[normalize_url(src)] = slug
        else:
            skipped_no_url.append(slug)

    print("Disk inventory:")
    print(f"  Rec-id-form files: {len(rec_files)}")
    print(f"  Slug-form files w/ source URL: {len(slug_files)}")
    print(f"  Slug-form files w/o source URL (skipped): {len(skipped_no_url)}")

    print("\nFetching AT2 News records...")
    records = fetch_at2_records()
    print(f"  AT2 records returned: {len(records)}")

    new_map = {}
    by_url = by_rid = unmapped = no_juris = 0
    juris_kept = Counter()
    juris_dropped = Counter()
    for r in records:
        rid = r['id']
        f = r.get('fields', {})
        src = normalize_url(f.get('Source URL', ''))
        juris_raw = (f.get('Name (from Jurisdiction)') or [None])[0]
        juris = juris_raw or '(none)'
        # Skip records with no jurisdiction — they're test/stub records in AT2
        if not juris_raw:
            no_juris += 1
            continue
        if src and src in slug_files:
            new_map[rid] = slug_files[src]
            by_url += 1
            juris_kept[juris] += 1
        elif rid in rec_files:
            new_map[rid] = rec_files[rid]
            by_rid += 1
            juris_kept[juris] += 1
        else:
            unmapped += 1
            juris_dropped[juris] += 1

    print("\nMapping result:")
    print(f"  Matched via Source URL: {by_url}")
    print(f"  Matched via rec-id only: {by_rid}")
    print(f"  Total mapped: {len(new_map)}")
    print(f"  Unmapped: {unmapped}")
    print(f"  Skipped (no jurisdiction in AT2): {no_juris}")

    print("\nJurisdictions in mapped set (top 30):")
    for k, v in juris_kept.most_common(30):
        print(f"  {v:4d}  {k}")

    if juris_dropped:
        print("\nJurisdictions of unmapped records:")
        for k, v in juris_dropped.most_common():
            print(f"  {v:4d}  {k}")

    current = {}
    if SLUG_MAP.exists():
        current = json.loads(SLUG_MAP.read_text())
    unchanged = sum(1 for rid in new_map if rid in current and current[rid] == new_map[rid])
    changed = sum(1 for rid in new_map if rid in current and current[rid] != new_map[rid])
    added = sum(1 for rid in new_map if rid not in current)
    removed = sum(1 for rid in current if rid not in new_map)
    print(f"\nDiff vs current news_slug_map.json (size {len(current)}):")
    print(f"  Unchanged: {unchanged}")
    print(f"  Changed:   {changed}")
    print(f"  Added:     {added}")
    print(f"  Removed:   {removed}")

    if write:
        SLUG_MAP.write_text(json.dumps(new_map, indent=2, ensure_ascii=False))
        print(f"\nWrote {SLUG_MAP} ({len(new_map)} entries)")
    else:
        print(f"\nDry-run only. Pass --write to update {SLUG_MAP.name}.")


if __name__ == '__main__':
    main()
