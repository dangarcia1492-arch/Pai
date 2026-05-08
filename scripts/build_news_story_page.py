"""Refresh pai-app-news-story-{slug}.html files with current AT2 News content.

Updates ONLY the head <title>, status-bar scope chip, story-eyebrow, story-title,
story-deck. Leaves story-body, story-ops, story-sources untouched — those carry
content (real bodies, operational notes, source citations) that AT2 doesn't own.

For each AT2 News record with a slug in news_slug_map.json:
  - Locate pai-app-news-story-{slug}.html
  - Replace <title>, ps-scope-chip, story-eyebrow inner, story-title, story-deck
  - Skip if file missing (story page never built)
  - Skip if no real change

Usage:
  python3 scripts/build_news_story_page.py --dry-run
  python3 scripts/build_news_story_page.py --apply
  python3 scripts/build_news_story_page.py --apply --limit 5
"""
import argparse
import collections
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG_MAP = ROOT / "news_slug_map.json"
NEWS_TBL = "tbl15HFEi0fXTLZQc"

TYPE_PILL_CLASS = {
    "Enforcement": "enf",
    "Guidance": "guid",
    "Update": "",
    "Legislation": "leg",
    "Case law": "case",
    "Analysis": "analy",
    "Blog": "blog",
    "Other": "",
}


def fetch_at2_news():
    base = os.environ["AIRTABLE_AT2_BASE"]
    token = os.environ["AIRTABLE_AT2_TOKEN"]
    url = f"https://api.airtable.com/v0/{base}/{NEWS_TBL}"
    hdr = {"Authorization": f"Bearer {token}"}
    out, offset = [], None
    while True:
        p = {"pageSize": 100}
        if offset:
            p["offset"] = offset
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(p), headers=hdr)
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read())
        out.extend(d.get("records", []))
        offset = d.get("offset")
        if not offset:
            break
        time.sleep(0.15)
    return out


def first(xs):
    return xs[0] if xs else None


def fmt_date_long(iso):
    if not iso:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", iso)
    if not m:
        return iso
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"{d} {months[mo-1]} {y}"


def html_escape(s):
    if s is None:
        return ""
    return html_lib.escape(str(s), quote=True).replace("&#x27;", "&#39;")


def rewrite_block(html, pattern, replacement):
    new, n = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
    return new, n > 0


def update_page(html, rec_fields, slug):
    f = rec_fields
    headline = f.get("Name") or ""
    summary = f.get("Summary") or ""
    juris = first(f.get("Name (from Jurisdiction)") or [])
    auth = first(f.get("Name (from Authorities)") or [])
    story_type = f.get("Story Type") or ""
    date_iso = f.get("Date Published") or ""
    date_long = fmt_date_long(date_iso)
    pill_cls = TYPE_PILL_CLASS.get(story_type, "")

    new_html = html
    changed_any = False

    # 1. <title>...</title>
    new_html, ok = rewrite_block(
        new_html,
        r"<title>.*?</title>",
        lambda m: f"<title>{html_escape(headline)} — PrinciplesAI</title>",
    )
    changed_any |= ok

    # 2. status bar scope chip — replace contents only, keep wrapper
    if juris and story_type:
        new_html, ok = rewrite_block(
            new_html,
            r'<span class="ps-scope-chip">[^<]*</span>',
            lambda m: f'<span class="ps-scope-chip">{html_escape(juris)} · {html_escape(story_type)}</span>',
        )
        changed_any |= ok

    # 3. story-eyebrow inner — replace whole inner block
    if juris:
        eyebrow_inner = (
            f'\n    <span class="eb-juris">{html_escape(juris)}</span>'
            + (f'\n    <span class="eb-auth">{html_escape(auth)}</span>' if auth else "")
            + (f'\n    <span class="eb-dot">·</span>\n    <span class="eb-type {pill_cls}">{html_escape(story_type)}</span>' if story_type else "")
            + (f'\n    <span class="eb-dot">·</span>\n    <span class="eb-date">{html_escape(date_long)}</span>' if date_long else "")
            + "\n  "
        )
        new_html, ok = rewrite_block(
            new_html,
            r'<div class="story-eyebrow">.*?</div>',
            lambda m: f'<div class="story-eyebrow">{eyebrow_inner}</div>',
        )
        changed_any |= ok

    # 4. story-title
    new_html, ok = rewrite_block(
        new_html,
        r'<h1 class="story-title">.*?</h1>',
        lambda m: f'<h1 class="story-title">{html_escape(headline)}</h1>',
    )
    changed_any |= ok

    # 5. story-deck
    if summary:
        new_html, ok = rewrite_block(
            new_html,
            r'<p class="story-deck">.*?</p>',
            lambda m: f'<p class="story-deck">{html_escape(summary)}</p>',
        )
        changed_any |= ok

    return new_html, changed_any


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        sys.exit("Pick --dry-run or --apply")

    print("Fetching AT2 News ...", file=sys.stderr)
    records = fetch_at2_news()
    print(f"Got {len(records)} AT2 records", file=sys.stderr)
    slug_map = json.loads(SLUG_MAP.read_text())

    counts = collections.Counter()
    log = []
    n_processed = 0
    for rec in records:
        rec_id = rec["id"]
        slug = slug_map.get(rec_id)
        if not slug:
            counts["no_slug"] += 1
            continue
        page = ROOT / f"pai-app-news-story-{slug}.html"
        if not page.exists():
            counts["no_page"] += 1
            continue
        html = page.read_text()
        new_html, changed = update_page(html, rec.get("fields", {}), slug)
        if not changed:
            counts["no_change"] += 1
            continue
        if new_html == html:
            counts["no_change"] += 1
            continue
        if args.apply:
            page.write_text(new_html)
            counts["written"] += 1
            log.append({"rec": rec_id, "slug": slug, "headline": rec.get("fields",{}).get("Name","")[:80]})
        else:
            counts["would_write"] += 1
        n_processed += 1
        if args.limit and n_processed >= args.limit:
            break

    print("\nSummary:", file=sys.stderr)
    for k, v in counts.most_common():
        print(f"  {k:20s} {v}", file=sys.stderr)


if __name__ == "__main__":
    main()
