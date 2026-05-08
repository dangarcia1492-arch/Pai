"""Roll the Domain-first widget swap into every juris page that has data.

For each jurisdiction in domain-first.json, find its pai-app-juris-{slug}.html
file and replace the static "is being sourced" placeholder inside `#view-D`
with the widget HTML+JS block, hardcoding the JURIS_DF constant per page.

Idempotent: if the widget is already present, skips the file.
Page-level structure (tabs, sections, page head, country map) untouched
per memory feedback_dont_touch_juris_page_structure.

Usage:
  python3 scripts/roll_domain_first_widget.py --dry-run     # report only, no writes
  python3 scripts/roll_domain_first_widget.py --apply       # write changes
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "domain-first.json"

# Jurisdiction-name → page-slug overrides (where simple lower+hyphen doesn't match)
SLUG_OVERRIDES = {
    "USA": "us-federal",
    "Australia": "australia-federal",
    "Canada": "canada-federal",
    "Germany": "germany-federal",
    "International": None,            # no juris page; skip
    "Türkiye": "turkiye",
    "European Union": "european-union",
    "South Korea": "south-korea",
    "Czech Republic": "czech-republic",
    "Saudi Arabia": "saudi-arabia",
    # Sub-national — try the natural slug; many won't have files
    "US - California": "us-california",
    "US - Hawaii": "us-hawaii",
    "Hamburg": "hamburg",
    "Andalusia": "andalusia",
    "California": "california",
}


def juris_to_slug(name: str):
    if name in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[name]
    return name.lower().replace(" ", "-").replace("'", "")


WIDGET_BLOCK = """    <style>
      .df-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
      .df-card{background:#fff;border:1px solid #ebeff5;border-radius:10px;padding:24px 26px;box-shadow:0 1px 2px rgba(10,23,41,.04);display:flex;flex-direction:column;gap:18px}
      .df-card.ai{border-top:4px solid #5b21b6}
      .df-card.privacy{border-top:4px solid #0176d3}
      .df-card.cyber{border-top:4px solid #ba0517}
      .df-pill-name{font-family:'Inter',sans-serif;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
      .df-pill-name.ai{color:#5b21b6}
      .df-pill-name.privacy{color:#014486}
      .df-pill-name.cyber{color:#ba0517}
      .df-surface{padding:16px 18px;background:#f8fafc;border-radius:8px;border:1px solid #ebeff5}
      .df-surface-h{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#5e6878;margin-bottom:8px}
      .df-leads{display:flex;flex-wrap:wrap;gap:6px}
      .df-lead{display:inline-block;font-family:'Source Serif 4','Inter',sans-serif;font-size:16px;font-weight:700;color:#06101e;padding:5px 10px;border-radius:5px;background:#fff;border:1px solid #ebeff5}
      .df-lead.others{background:#f8fafc;color:#5e6878;font-weight:500;font-size:13px}
      .df-section-h{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#5e6878;margin-bottom:8px}
      .df-list{list-style:none;margin:0;padding:0}
      .df-list li{font-size:13px;padding:8px 0;border-top:1px solid #ebeff5;color:#0a1729;line-height:1.4}
      .df-list li:first-child{border-top:none}
      .df-list li .meta{font-size:11px;color:#8a93a3;display:block;margin-top:2px;font-weight:500;letter-spacing:.04em;text-transform:uppercase}
      .df-list li .meta .auth{color:#2a3548;font-weight:600;letter-spacing:.04em;text-transform:none;margin-right:6px;font-size:11.5px}
      .df-empty{padding:60px 32px;text-align:center;background:#fff;border:1px solid #ebeff5;border-radius:14px;color:#5e6878;font-size:13px}
      @media (max-width:900px){.df-grid{grid-template-columns:1fr}}
    </style>
    <div id="df-root"><div class="df-empty">Loading…</div></div>
    <script>
    (async function loadDomainFirst(){
      const JURIS_DF = "__JURIS_NAME__";
      const root = document.getElementById('df-root');
      const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
      const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const fmtDate = iso => { const m=(iso||'').match(/^(\\d{4})-(\\d{2})-(\\d{2})/); return m ? (parseInt(m[3],10)+' '+MONTHS[parseInt(m[2],10)-1]+' '+m[1]) : ''; };
      try {
        const r = await fetch('./domain-first.json',{cache:'no-cache'});
        if (!r.ok) throw new Error('HTTP '+r.status);
        const d = await r.json();
        const block = (d.jurisdictions||{})[JURIS_DF];
        if (!block) {
          root.innerHTML = '<div class="df-empty">Domain-first view for ' + esc(JURIS_DF) + ' is being sourced. Switch back to <strong>Newsroom</strong> for the latest activity stream.</div>';
          return;
        }
        function renderLeadsRow(p){
          const items = (p.leads||[]).map(n => '<span class="df-lead">' + esc(n) + '</span>').join('');
          const others = p.others_count > 0 ? '<span class="df-lead others">+' + p.others_count + ' other' + (p.others_count===1?'':'s') + '</span>' : '';
          return items + others;
        }
        function renderRecent(p){
          if (!p.recent || !p.recent.length) return '<li style="color:#8a93a3;font-style:italic">No recent activity in this pillar</li>';
          return p.recent.map(r =>
            '<li>' + esc(r.headline) + '<span class="meta"><span class="auth">' + esc(r.authority_short || '') + '</span>' + esc(fmtDate(r.date_published)) + (r.story_type ? ' · ' + esc(r.story_type) : '') + '</span></li>'
          ).join('');
        }
        function renderInstruments(p){
          if (!p.top_instruments || !p.top_instruments.length) return '<li style="color:#8a93a3;font-style:italic">No instruments tagged in this pillar</li>';
          return p.top_instruments.map(i =>
            '<li>' + esc(i.name) + '<span class="meta">' + esc(i.status || '') + (i.date_enacted ? ' · ' + esc(i.date_enacted.slice(0,4)) : '') + '</span></li>'
          ).join('');
        }
        function card(pillarKey, label, cls){
          const p = block[pillarKey] || {leads:[],others_count:0,recent:[],top_instruments:[]};
          const leadsLabel = (p.leads||[]).length === 1 ? 'Lead regulator' : 'Lead regulators';
          return ''
            + '<div class="df-card ' + cls + '">'
            +   '<div class="df-pill-name ' + cls + '">' + esc(label) + '</div>'
            +   '<div class="df-surface"><div class="df-surface-h">' + leadsLabel + '</div><div class="df-leads">' + renderLeadsRow(p) + '</div></div>'
            +   '<div><div class="df-section-h">Recent</div><ul class="df-list">' + renderRecent(p) + '</ul></div>'
            +   '<div><div class="df-section-h">Top instruments</div><ul class="df-list">' + renderInstruments(p) + '</ul></div>'
            + '</div>';
        }
        root.innerHTML = '<div class="df-grid">' + card('AI','AI','ai') + card('Privacy','Privacy','privacy') + card('Cyber','Cyber','cyber') + '</div>';
      } catch (e) {
        root.innerHTML = '<div class="df-empty">Could not load domain-first data (' + esc(e.message) + '). Switch back to <strong>Newsroom</strong>.</div>';
      }
    })();
    </script>
"""


# Match the placeholder div inside #view-D (the original "is being sourced" content)
PLACEHOLDER_RE = re.compile(
    r'(<div class="view" id="view-D" data-view="D">\s*)'
    r'(<div style="padding:60px 32px;text-align:center;background:#fff;border:1px solid #ebeff5;border-radius:14px">.*?</div>)'
    r'(\s*</div>)',
    re.DOTALL,
)
WIDGET_PRESENT_RE = re.compile(r'<div class="view" id="view-D"[^>]*>\s*<style>\s*\.df-grid', re.DOTALL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        sys.exit("Pick --dry-run or --apply")

    data = json.loads(DATA.read_text())
    jurisdictions = data["jurisdictions"]
    print(f"domain-first.json: {len(jurisdictions)} jurisdictions", file=sys.stderr)

    counts = {"applied": 0, "already_done": 0, "no_page": 0, "no_placeholder": 0, "skipped_subnat": 0}
    for jname in sorted(jurisdictions.keys()):
        slug = juris_to_slug(jname)
        if slug is None:
            counts["skipped_subnat"] += 1
            print(f"  SKIP   {jname} — no juris page (no slug)", file=sys.stderr)
            continue
        page = ROOT / f"pai-app-juris-{slug}.html"
        if not page.exists():
            counts["no_page"] += 1
            print(f"  NO_PAGE  {jname} -> pai-app-juris-{slug}.html (file missing)", file=sys.stderr)
            continue
        html = page.read_text()
        if WIDGET_PRESENT_RE.search(html):
            counts["already_done"] += 1
            print(f"  HAS_WIDGET  {jname}", file=sys.stderr)
            continue
        if not PLACEHOLDER_RE.search(html):
            counts["no_placeholder"] += 1
            print(f"  NO_PLACEHOLDER  {jname} -> {page.name}", file=sys.stderr)
            continue
        widget_with_juris = WIDGET_BLOCK.replace("__JURIS_NAME__", jname.replace('"', '\\"'))
        new_html = PLACEHOLDER_RE.sub(lambda m: m.group(1) + widget_with_juris.lstrip() + m.group(3), html)
        if args.apply:
            page.write_text(new_html)
            counts["applied"] += 1
            print(f"  WROTE  {jname}", file=sys.stderr)
        else:
            counts["applied"] += 1  # would-write
            print(f"  WOULD  {jname}", file=sys.stderr)

    print("\nSummary:", file=sys.stderr)
    for k, v in counts.items():
        print(f"  {k:20s} {v}", file=sys.stderr)


if __name__ == "__main__":
    main()
