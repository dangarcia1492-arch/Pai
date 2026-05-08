"""Filter news.json to rows whose slug has a real pai-app-news-story-{slug}.html file.

Mirrors the Phase D.1 logic (commit 32847a12) — keeps the wire from showing
links that 404. Run AFTER build_news_json.py.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEWS_JSON = ROOT / "news.json"


def main():
    with open(NEWS_JSON) as f:
        data = json.load(f)
    rows = data.get("rows", [])
    before = len(rows)

    # Build set of existing story slugs from disk
    existing = set()
    for entry in os.listdir(ROOT):
        if entry.startswith("pai-app-news-story-") and entry.endswith(".html"):
            slug = entry[len("pai-app-news-story-"):-len(".html")]
            existing.add(slug)

    kept = [r for r in rows if r.get("slug") and r["slug"] in existing]
    after = len(kept)
    dropped = before - after
    data["rows"] = kept
    data["total"] = after
    # Recompute facets from kept rows
    import collections
    fc = {k: collections.Counter() for k in ["region", "story_type", "tags", "authority", "verified_status"]}
    for r in kept:
        if r.get("region"): fc["region"][r["region"]] += 1
        if r.get("story_type"): fc["story_type"][r["story_type"]] += 1
        for t in r.get("tags", []) or []: fc["tags"][t] += 1
        if r.get("authority"): fc["authority"][r["authority"]] += 1
        if r.get("verified_status"): fc["verified_status"][r["verified_status"]] += 1
    data["facets"] = {k: dict(v.most_common()) for k, v in fc.items()}

    with open(NEWS_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Filtered news.json: {before} -> {after} (dropped {dropped} with no story page)")
    print(f"Existing story files on disk: {len(existing)}")


if __name__ == "__main__":
    main()
