"""Render IP+AI cross-jurisdictional matrix from PG frameworks.claim.

Reads frameworks.dimension + frameworks.claim WHERE superseded_at IS NULL.
Outputs the <tbody> content for pai-app-frameworks-ip.html (matrix only,
header/footer untouched).

Usage:
  python3 render_ipai.py                  # write rendered to OUT_HTML
  python3 render_ipai.py --print-tbody    # print just <tbody>...</tbody>
  python3 render_ipai.py --diff           # diff vs current page tbody
  python3 render_ipai.py --apply          # swap rendered tbody into the page
"""
import argparse
import html as html_lib
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

PAGE = Path("/Users/claude-sandbox/Pai-edit-ipai-render/pai-app-frameworks-ip.html")
OUT_HTML = Path("/Users/claude-sandbox/workboard/research/ipai-rendered-tbody.html")

# Answer -> (color, background) for the pill styling.
# Derived from inspecting the live page's inline styles.
ANSWER_STYLE = {
    "Yes": ("#2e844a", "#d6f1dc"),
    "No": ("#5e6878", "#ebeff5"),
    "No framework": ("#5e6878", "#ebeff5"),
    "Untested": ("#905200", "#fef0c7"),
    "Maybe": ("#905200", "#fef0c7"),
    "Editorial (revised)": ("#905200", "#fef0c7"),
    "Limited": ("#0a1729", "#e3effc"),
    "Unsettled": ("#0a1729", "#e3effc"),
    "Evolving": ("#0a1729", "#e3effc"),
    "Fair use": ("#0a1729", "#e3effc"),
    "N/A": ("#8a93a3", "#f4f6fa"),
}
DEFAULT_STYLE = ("#5e6878", "#ebeff5")  # fallback gray

# Jurisdictions present in PG but not yet ready for the live page (e.g. missing tags).
# Brazil's bootstrap data lacks tag-pill values; show on page after a tag backfill.
JURIS_HIDE = {"Brazil"}

# Jurisdiction display order on the live page (matches what's currently rendered).
# Brazil (added by us) goes at the bottom.
JURIS_ORDER = [
    "United Kingdom",
    "United States",
    "Japan",
    "European Union",
    "China",
    "Singapore",
    "South Korea",
    "India",
    "Australia",
    "Brazil",
]

# slug for the per-juris IP+AI note page link
JURIS_SLUG = {
    "United Kingdom": "united-kingdom",
    "United States": "united-states",
    "Japan": "japan",
    "European Union": "european-union",
    "China": "china",
    "Singapore": "singapore",
    "South Korea": "south-korea",
    "India": "india",
    "Australia": "australia",
    "Brazil": "brazil",
}


def tag_class(tag: str) -> str:
    """Derive `tag-pill X` class from tag text."""
    if not tag:
        return "tag-pill "
    t = tag.lower()
    if t.startswith("source-confirmed"):
        return "tag-pill confirmed"
    if t.startswith("editorial"):
        return "tag-pill editorial"
    if t == "n/a":
        return "tag-pill "
    return "tag-pill "


def answer_pill(answer: str) -> str:
    fg, bg = ANSWER_STYLE.get(answer or "", DEFAULT_STYLE)
    text = html_escape(answer or "—")
    return (
        f'<span style="display:inline-block;font-family:\'Inter\',sans-serif;font-size:10.5px;'
        f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{fg};'
        f'background:{bg};padding:2px 7px;border-radius:3px">{text}</span>'
    )


def html_escape(s: str) -> str:
    """Match the live page's encoding: decimal &#39; for apostrophe, not hex &#x27;."""
    return html_lib.escape(s, quote=True).replace("&#x27;", "&#39;")


def render_cell(answer: str, citation: str, tag: str) -> str:
    cite_html = html_escape(citation) if citation else ""
    tag_text = html_escape(tag) if tag else ""
    cls = tag_class(tag)
    return (
        f"<td>{answer_pill(answer)}"
        f'<div class="src-cite">{cite_html}</div>'
        f'<div class="{cls}">{tag_text}</div></td>'
    )


def render_juris_row(juris: str, cells_by_dim: dict, dim_keys: list) -> str:
    slug = JURIS_SLUG.get(juris)
    if not slug:
        slug = juris.lower().replace(" ", "-")
    juris_a = (
        f'<td class="juris-cell"><a href="pai-app-ipai-note-{slug}" '
        'style="color:#014486;text-decoration:none;font-weight:700;'
        f'border-bottom:1px solid #cfe1f6">{html_lib.escape(juris)} →</a></td>'
    )
    cells_html = []
    for dk in dim_keys:
        cell = cells_by_dim.get(dk, {"answer_label": None, "citation": None, "tag": None})
        cells_html.append(render_cell(cell["answer_label"], cell["citation"], cell["tag"]))
    return "<tr>" + juris_a + "".join(cells_html) + "</tr>"


def fetch_grid():
    conn = psycopg2.connect(os.environ["PAI_PG_URL"])
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT key FROM frameworks.dimension WHERE framework_slug='ip-and-ai' ORDER BY col_order"
        )
        dim_keys = [r["key"] for r in cur.fetchall()]

        cur.execute(
            """SELECT jurisdiction, dimension_key, answer_label, citation, tag
               FROM frameworks.claim
               WHERE framework_slug='ip-and-ai' AND superseded_at IS NULL"""
        )
        by_juris: dict[str, dict] = {}
        for r in cur.fetchall():
            by_juris.setdefault(r["jurisdiction"], {})[r["dimension_key"]] = {
                "answer_label": r["answer_label"],
                "citation": r["citation"],
                "tag": r["tag"],
            }
    conn.close()
    return dim_keys, by_juris


def render_tbody() -> str:
    dim_keys, by_juris = fetch_grid()
    rows = []
    seen = set()
    for j in JURIS_ORDER:
        if j in JURIS_HIDE:
            continue
        if j in by_juris:
            rows.append(render_juris_row(j, by_juris[j], dim_keys))
            seen.add(j)
    # Any jurisdiction in PG but not in JURIS_ORDER → append at end (also honor JURIS_HIDE)
    for j in sorted(by_juris.keys() - seen - JURIS_HIDE):
        rows.append(render_juris_row(j, by_juris[j], dim_keys))
    return "<tbody>" + "\n".join(rows) + "</tbody>"


def extract_current_tbody() -> str:
    html = PAGE.read_text()
    m = re.search(r"<tbody>.*?</tbody>", html, re.DOTALL)
    if not m:
        sys.exit("could not find <tbody> in page")
    # Return first match — the matrix tbody is the first one (line 545).
    return m.group(0)


def apply_to_page(rendered_tbody: str) -> bool:
    """Replace the first <tbody>...</tbody> in PAGE with rendered_tbody. Returns True if changed."""
    html = PAGE.read_text()
    new_html, n = re.subn(r"<tbody>.*?</tbody>", lambda m: rendered_tbody, html, count=1, flags=re.DOTALL)
    if n == 0:
        sys.exit("could not find <tbody> in page to swap")
    if new_html == html:
        return False
    PAGE.write_text(new_html)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print-tbody", action="store_true")
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--apply", action="store_true", help="swap rendered tbody into the page file")
    args = ap.parse_args()

    rendered = render_tbody()

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(rendered + "\n")
    print(f"Wrote rendered tbody: {OUT_HTML} ({len(rendered)} bytes)")

    if args.print_tbody:
        print(rendered)

    if args.diff:
        current = extract_current_tbody()
        cur_path = OUT_HTML.with_name("ipai-current-tbody.html")
        cur_path.write_text(current + "\n")
        print(f"Wrote current page tbody:  {cur_path} ({len(current)} bytes)")
        proc = subprocess.run(
            ["diff", "-u", str(cur_path), str(OUT_HTML)],
            capture_output=True, text=True
        )
        print(proc.stdout)
        if not proc.stdout.strip():
            print("(NO DIFF — rendered output matches current page byte-for-byte)")

    if args.apply:
        changed = apply_to_page(rendered)
        print(f"page apply: {'CHANGED' if changed else 'no-op (already current)'}")


if __name__ == "__main__":
    main()
