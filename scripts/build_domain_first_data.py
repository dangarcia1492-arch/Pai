"""Build domain-first.json — per-jurisdiction regulatory-shape intelligence by pillar.

For each jurisdiction × each pillar (AI / Privacy / Cyber):
  - lead regulators = authorities with >=3 published news rows in this pillar (named, top 3 shown)
  - others_count   = authorities with 1-2 news rows (lumped, displayed as "+N others")
  - recent         = top 3 most recent news headlines in this pillar
  - top_instruments = top 2 legislation rows tagged with this pillar Topic

Output: Pai-edit-root/domain-first.json keyed by jurisdiction name → pillars dict
Page-side widget reads it at runtime and renders into #view-D of each juris page.
"""
import collections
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "domain-first.json"

NEWS_TBL = "tbl15HFEi0fXTLZQc"
LEG_TBL = "tblwoaDzVyMYQbMMi"
AUTH_TBL = "tbllcAd8ZqWdLmVyr"
JURIS_TBL = "tblE2iljzLCoMqIS5"

PILLARS = ("AI", "Privacy", "Cyber")
LEAD_THRESHOLD = 3      # authority needs >=3 news rows in pillar to be named
LEAD_DISPLAY_CAP = 3    # display max 3 named leads, lump rest into +others
RECENT_CAP = 3
INSTRUMENT_CAP = 2


def fetch_all(table_id):
    base = os.environ["AIRTABLE_AT2_BASE"]
    token = os.environ["AIRTABLE_AT2_TOKEN"]
    url = f"https://api.airtable.com/v0/{base}/{table_id}"
    headers = {"Authorization": f"Bearer {token}"}
    out, offset = [], None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        out.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.15)
    return out


def short_authority(name: str) -> str:
    """Practitioner shorthand. AT2 stores long official names; UI wants 'ICO' not 'Information Commissioner's Office'."""
    if not name:
        return ""
    overrides = {
        "Information Commissioner's Office": "ICO",
        "UK National Cyber Security Centre (NCSC)": "NCSC",
        "AI Security Institute (AISI)": "AISI",
        "Department for Science, Innovation and Technology": "DSIT",
        "Medicines and Healthcare products Regulatory Agency": "MHRA",
        "Commission Nationale de l'Informatique et des Libertes": "CNIL",
        "European Data Protection Board": "EDPB",
        "European Data Protection Supervisor": "EDPS",
        "Federal Trade Commission": "FTC",
        "National Institute of Standards and Technology": "NIST",
    }
    if name in overrides:
        return overrides[name]
    # Try parenthetical short form: "X (Y)" → "Y"
    if "(" in name and ")" in name:
        inside = name.rsplit("(", 1)[1].rstrip(")")
        if 2 <= len(inside) <= 8 and inside.isupper():
            return inside
    return name


def build_pillar_block(juris_name: str, pillar: str, news_for_juris, leg_for_juris):
    # Authority counts (only news rows tagged with this pillar)
    auth_counts = collections.Counter()
    pillar_news = []
    for n in news_for_juris:
        if pillar in (n.get("fields", {}).get("Tags") or []):
            for a in n.get("fields", {}).get("Name (from Authorities)") or []:
                auth_counts[a] += 1
            pillar_news.append(n)

    # Leads = >=3 rows; sorted by count desc; cap at 3 named
    sorted_auths = auth_counts.most_common()
    leads_named = [a for a, c in sorted_auths if c >= LEAD_THRESHOLD][:LEAD_DISPLAY_CAP]
    others_count = len([a for a, c in sorted_auths if c < LEAD_THRESHOLD]) \
                   + max(0, len([a for a, c in sorted_auths if c >= LEAD_THRESHOLD]) - LEAD_DISPLAY_CAP)
    leads_short = [short_authority(a) for a in leads_named]

    # Recent — top RECENT_CAP by date
    pillar_news.sort(key=lambda r: r.get("fields", {}).get("Date Published") or "", reverse=True)
    recent = []
    for n in pillar_news[:RECENT_CAP]:
        f = n.get("fields", {})
        recent.append({
            "headline": f.get("Name") or "",
            "slug": None,  # filled by build_news_json's slug map elsewhere
            "date_published": f.get("Date Published"),
            "authority_short": short_authority((f.get("Name (from Authorities)") or [""])[0]),
            "story_type": f.get("Story Type"),
        })

    # Top instruments — legislation rows tagged with this pillar Topic, In force preferred
    pillar_leg = []
    for r in leg_for_juris:
        topics = r.get("fields", {}).get("Topic") or []
        if pillar in topics:
            pillar_leg.append(r)
    # Prefer In-force, then most recently enacted
    pillar_leg.sort(key=lambda r: (
        0 if r.get("fields", {}).get("Status") == "In force" else 1,
        -(int((r.get("fields", {}).get("Date Enacted") or "0000-00-00")[:4] or 0)),
    ))
    top_inst = []
    for r in pillar_leg[:INSTRUMENT_CAP]:
        f = r.get("fields", {})
        top_inst.append({
            "name": f.get("Name") or f.get("Short Title") or "",
            "status": f.get("Status") or "",
            "date_enacted": f.get("Date Enacted"),
        })

    return {
        "leads": leads_short,
        "leads_full": leads_named,
        "others_count": others_count,
        "news_total_in_pillar": sum(c for _, c in sorted_auths),
        "recent": recent,
        "top_instruments": top_inst,
    }


def main():
    print("Fetching AT2 ...", file=sys.stderr)
    juris = fetch_all(JURIS_TBL)
    juris_by_id = {r["id"]: r.get("fields", {}).get("Name") for r in juris}
    juris_id_by_name = {v: k for k, v in juris_by_id.items() if v}

    news = fetch_all(NEWS_TBL)
    leg = fetch_all(LEG_TBL)

    # Group news + leg by jurisdiction (by name for news — uses lookup; by rec_id for leg)
    news_by_juris = collections.defaultdict(list)
    for n in news:
        for jname in (n.get("fields", {}).get("Name (from Jurisdiction)") or []):
            news_by_juris[jname].append(n)

    leg_by_juris = collections.defaultdict(list)
    for r in leg:
        for jid in (r.get("fields", {}).get("Jurisdiction") or []):
            jname = juris_by_id.get(jid)
            if jname:
                leg_by_juris[jname].append(r)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jurisdictions": {},
    }

    for jname, juris_news in news_by_juris.items():
        if len(juris_news) < 3:
            continue  # don't render Domain-First for jurisdictions with <3 news rows total
        block = {}
        for pillar in PILLARS:
            block[pillar] = build_pillar_block(jname, pillar, juris_news, leg_by_juris.get(jname, []))
        out["jurisdictions"][jname] = block

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} ({len(out['jurisdictions'])} jurisdictions covered)", file=sys.stderr)
    # Quick UK summary for verification
    uk = out["jurisdictions"].get("United Kingdom")
    if uk:
        print(f"\nUK quickcheck:", file=sys.stderr)
        for p in PILLARS:
            b = uk[p]
            leads = " · ".join(b["leads"]) or "—"
            extra = f" · +{b['others_count']} other{'s' if b['others_count']!=1 else ''}" if b["others_count"] else ""
            print(f"  {p}: {leads}{extra}  (recent={len(b['recent'])}, instruments={len(b['top_instruments'])})", file=sys.stderr)


if __name__ == "__main__":
    main()
