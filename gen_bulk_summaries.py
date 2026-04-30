"""
Bulk story summary writer for PAI demo (Apr 29).
Reads news.json, fetches source_text from PG, calls claude-haiku-4-5
to generate house-style Body Full for each story lacking a summary.

Tags each generated row with summary_draft=True in news.json.
Saves all raw drafts to demo_summaries_apr29.json for later refinement.

Usage:
  python3 gen_bulk_summaries.py          # write all missing summaries
  python3 gen_bulk_summaries.py --clear  # remove demo summaries from news.json
                                          # (keeps demo_summaries_apr29.json)
"""
import json, os, sys, time, psycopg2
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic

# ─── Config ──────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PG_URL           = "postgresql://pai:BjypxrDDsN8QImnjNzUQIo7YI8EyRH7@127.0.0.1:15432/pai"
NEWS_JSON        = Path("news.json")
DRAFTS_FILE      = Path("demo_summaries_apr29.json")
MODEL            = "claude-sonnet-4-6"
MAX_CONCURRENT   = 6
MIN_SOURCE_LEN   = 250   # chars

# ─── House style system prompt ────────────────────────────────────────────────

SYSTEM = """You write regulatory news stories for PAI, a platform for senior legal, privacy and compliance professionals.

RULES — follow exactly:
- British English throughout (organisational, authorise, recognise, programme, etc.)
- Body Full: 250-400 words. No more, no less.
- Structure: (1) Lead sentence — standalone one-sentence summary with authority, entity, outcome, legal basis. (2) Date paragraph starting "On [date], [full authority name]..." (3) Two to three body paragraphs with factual detail from the source. (4) No closing forward-looking sentence.
- Every factual finding, legal conclusion or determination MUST be attributed to the authority: "IMY finds...", "The CNIL determined...", "IRDAI states...". Never state regulatory findings as standalone facts.
- Never use "should". Use "must" only when quoting a legal obligation. Prefer "is required to", "the authority finds", "the decision notes".
- No em dashes. Use commas or colons instead.
- No advice. No "organisations should review...", "practitioners must consider..." etc.
- No characterising adjectives: never "landmark", "significant", "robust", "major", "sweeping".
- Cite article numbers inline where they support the point: "(Art. 32 GDPR)", "(s.13 DPDPA)", etc.
- Fine amounts: always state local currency AND EUR/USD equivalent in the lead and date paragraph.
- Output ONLY a JSON object: {"title": "...", "summary": "..."} — no other text, no markdown fences.
- title: a clear, factual headline. No verbs like "signals" or "marks". State what happened.
- summary: the full Body Full text (250-400 words), plain text, no markdown."""

# ─── PG fetch ────────────────────────────────────────────────────────────────

def fetch_source_texts(at_ids):
    conn = psycopg2.connect(PG_URL)
    cur  = conn.cursor()
    ph   = ",".join(["%s"] * len(at_ids))
    cur.execute(
        f"SELECT airtable_id, headline, source_url, source_text, date_published "
        f"FROM intake.content WHERE airtable_id IN ({ph}) "
        f"AND workflow_status IN ('Approved', 'Lead')",
        at_ids
    )
    rows = {r[0]: {"headline": r[1], "url": r[2], "text": r[3], "date": str(r[4])} for r in cur.fetchall()}
    conn.close()
    return rows

# ─── Haiku call ──────────────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_summary(row, src):
    user_msg = (
        f"Source headline: {src['headline']}\n"
        f"Authority: {row.get('body_name', 'Unknown')}\n"
        f"Jurisdiction: {row.get('jurisdiction_name', 'Unknown')}\n"
        f"Date published: {row.get('date_published') or src.get('date', 'unknown')}\n"
        f"Topic: {row.get('topic', 'unknown')}\n"
        f"Source URL: {src['url']}\n\n"
        f"SOURCE TEXT:\n{src['text'][:6000]}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    raw = resp.content[0].text.strip()
    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ─── Clear mode ──────────────────────────────────────────────────────────────

def clear_drafts():
    data  = json.loads(NEWS_JSON.read_text())
    count = 0
    for row in data["rows"]:
        if row.pop("summary_draft", False):
            row["summary"] = ""
            row["title"]   = row.get("_orig_title", row["title"])
            row.pop("_orig_title", None)
            count += 1
    NEWS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Cleared {count} draft summaries from news.json")
    print(f"Raw drafts preserved in {DRAFTS_FILE}")

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if "--clear" in sys.argv:
        clear_drafts()
        return

    # Load existing drafts (resume support)
    existing_drafts = {}
    if DRAFTS_FILE.exists():
        existing_drafts = json.loads(DRAFTS_FILE.read_text())
        print(f"Loaded {len(existing_drafts)} existing drafts from {DRAFTS_FILE}")

    data = json.loads(NEWS_JSON.read_text())
    rows = data["rows"]

    # Find rows needing summaries and not yet drafted
    todo = [r for r in rows
            if not r.get("summary") and not r.get("summary_draft")
            and r["id"] not in existing_drafts]
    print(f"Stories needing summaries: {len(todo)}")

    # Fetch source texts from PG
    todo_ids = [r["id"] for r in todo]
    if not todo_ids:
        print("Nothing to do.")
        return

    print("Fetching source texts from PG...")
    src_map = fetch_source_texts(todo_ids)

    # Filter to those with usable source text
    workable = [(r, src_map[r["id"]]) for r in todo
                if r["id"] in src_map and len(src_map[r["id"]].get("text") or "") >= MIN_SOURCE_LEN]
    print(f"Workable (have source text): {len(workable)}")

    # Estimate cost
    avg_input  = 2500  # tokens
    avg_output = 450
    cost = len(workable) * (avg_input * 0.80 + avg_output * 4.0) / 1_000_000
    print(f"Estimated cost: ${cost:.2f}")
    print("Starting in 3s... Ctrl-C to abort.")
    time.sleep(3)

    errors  = []
    drafted = dict(existing_drafts)

    def process(row_src):
        row, src = row_src
        at_id = row["id"]
        try:
            result = generate_summary(row, src)
            drafted[at_id] = {
                "at_id":        at_id,
                "orig_title":   row.get("title", ""),
                "gen_title":    result.get("title", ""),
                "summary":      result.get("summary", ""),
                "jurisdiction": row.get("jurisdiction_name", ""),
                "body":         row.get("body_name", ""),
                "date":         row.get("date_published", ""),
            }
            return at_id, result, None
        except Exception as e:
            return at_id, None, str(e)

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as pool:
        futures = {pool.submit(process, item): item for item in workable}
        for fut in as_completed(futures):
            at_id, result, err = fut.result()
            done += 1
            if err:
                errors.append((at_id, err))
                print(f"  [{done}/{len(workable)}] ERROR {at_id}: {err[:60]}")
            else:
                juris = drafted[at_id]["jurisdiction"]
                print(f"  [{done}/{len(workable)}] OK  {juris[:20]:20s}  {result['title'][:55]}")

            # Save drafts file after every 10 completions
            if done % 10 == 0:
                DRAFTS_FILE.write_text(json.dumps(drafted, ensure_ascii=False, indent=2))

    # Final save of drafts
    DRAFTS_FILE.write_text(json.dumps(drafted, ensure_ascii=False, indent=2))
    print(f"\nDrafts saved to {DRAFTS_FILE} ({len(drafted)} total)")

    # Inject into news.json
    draft_map = {at_id: v for at_id, v in drafted.items()}
    injected = 0
    for row in rows:
        at_id = row["id"]
        if at_id in draft_map and not row.get("summary"):
            d = draft_map[at_id]
            row["_orig_title"]   = row["title"]
            row["title"]         = d["gen_title"] or row["title"]
            row["summary"]       = d["summary"]
            row["summary_draft"] = True
            injected += 1

    NEWS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Injected {injected} summaries into news.json (tagged summary_draft=True)")

    if errors:
        print(f"\n{len(errors)} errors:")
        for at_id, err in errors:
            print(f"  {at_id}: {err}")

if __name__ == "__main__":
    main()
