"""
Fix PAI house style issues in demo_summaries_apr29.json.
Pass 1: British spelling substitutions (no LLM)
Pass 2: Haiku fixes for over-length, missing On-date opener, "should", attribution
"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"
DRAFTS_FILE = "demo_summaries_apr29.json"

# ─── British spelling map ─────────────────────────────────────────────────────

SPELLING = [
    (r'\borganization\b', 'organisation'),
    (r'\borganizations\b', 'organisations'),
    (r'\borganizational\b', 'organisational'),
    (r'\bauthorize\b', 'authorise'),
    (r'\bauthorized\b', 'authorised'),
    (r'\bauthorizes\b', 'authorises'),
    (r'\bauthorization\b', 'authorisation'),
    (r'\bauthorizations\b', 'authorisations'),
    (r'\brecognize\b', 'recognise'),
    (r'\brecognized\b', 'recognised'),
    (r'\brecognizes\b', 'recognises'),
    (r'\banalyze\b', 'analyse'),
    (r'\banalyzed\b', 'analysed'),
    (r'\banalyzes\b', 'analyses'),
    (r'\bbehavior\b', 'behaviour'),
    (r'\bbehaviors\b', 'behaviours'),
    (r'\bbehavioral\b', 'behavioural'),
    (r'\bdefense\b', 'defence'),
    (r'\bdefenses\b', 'defences'),
    (r'\boffense\b', 'offence'),
    (r'\boffenses\b', 'offences'),
    (r'\bfavor\b', 'favour'),
    (r'\bfavors\b', 'favours'),
    (r'\bfavorable\b', 'favourable'),
    (r'\bfavorably\b', 'favourably'),
    (r'\blabor\b', 'labour'),
    (r'\blabors\b', 'labours'),
    (r'\bcolor\b', 'colour'),
    (r'\bcolors\b', 'colours'),
    (r'\bhonor\b', 'honour'),
    (r'\bhonors\b', 'honours'),
    (r'\bsummarize\b', 'summarise'),
    (r'\bsummarized\b', 'summarised'),
    (r'\bprioritize\b', 'prioritise'),
    (r'\bprioritized\b', 'prioritised'),
    (r'\butilize\b', 'utilise'),
    (r'\butilized\b', 'utilised'),
    (r'\bminimize\b', 'minimise'),
    (r'\bminimized\b', 'minimised'),
    (r'\bmaximize\b', 'maximise'),
    (r'\bmaximized\b', 'maximised'),
    (r'\bstandardize\b', 'standardise'),
    (r'\bstandardized\b', 'standardised'),
    (r'\bharmonize\b', 'harmonise'),
    (r'\bharmonized\b', 'harmonised'),
    (r'\bpenalize\b', 'penalise'),
    (r'\bpenalized\b', 'penalised'),
    (r'\bfinalize\b', 'finalise'),
    (r'\bfinalized\b', 'finalised'),
    (r'\bformalize\b', 'formalise'),
    (r'\bformalized\b', 'formalised'),
    (r'\bemphasize\b', 'emphasise'),
    (r'\bemphasized\b', 'emphasised'),
    (r'\bcategorize\b', 'categorise'),
    (r'\bcategorized\b', 'categorised'),
    (r'\bcharacterize\b', 'characterise'),
    (r'\bcharacterized\b', 'characterised'),
    (r'\bcenter\b', 'centre'),
    (r'\bcenters\b', 'centres'),
    (r'\bcentralize\b', 'centralise'),
    (r'\bcentralized\b', 'centralised'),
    (r'\bcustomize\b', 'customise'),
    (r'\bcustomized\b', 'customised'),
    (r'\bmodernize\b', 'modernise'),
    (r'\bmodernized\b', 'modernised'),
    (r'\bmobilize\b', 'mobilise'),
    (r'\bmobilized\b', 'mobilised'),
    (r'\bspecialize\b', 'specialise'),
    (r'\bspecialized\b', 'specialised'),
    (r'\bstabilize\b', 'stabilise'),
    (r'\bstabilized\b', 'stabilised'),
    (r'\bneutralize\b', 'neutralise'),
    (r'\bneutralized\b', 'neutralised'),
    (r'\bnormalize\b', 'normalise'),
    (r'\bnormalized\b', 'normalised'),
    (r'\bpersonalize\b', 'personalise'),
    (r'\bpersonalized\b', 'personalised'),
    (r'\brealise\b', 'realise'),  # already correct but just in case
    (r'\brealize\b', 'realise'),
    (r'\brealized\b', 'realised'),
]

def british_spelling(text):
    for pattern, replacement in SPELLING:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE,
                      count=0)
        # Fix case: if pattern matched a capitalised word, capitalise replacement
        text = re.sub(pattern[2:-2].capitalize() + r'\b',
                      replacement.capitalize(), text)
    return text


# ─── Detect issues ────────────────────────────────────────────────────────────

def second_para_starts_on(s):
    paras = [p.strip() for p in s.split('\n\n') if p.strip()]
    return len(paras) >= 2 and paras[1].startswith('On ')

def needs_llm_fix(s):
    issues = []
    if len(s.split()) > 400:
        issues.append('overlength')
    if ' should ' in s.lower():
        issues.append('should')
    if not second_para_starts_on(s):
        issues.append('no_on_date')
    return issues


# ─── LLM fix prompt ──────────────────────────────────────────────────────────

FIX_SYSTEM = """You are a sub-editor for PAI, a regulatory intelligence platform. Fix the story to meet these rules exactly:

RULES:
1. British English throughout (organisation, authorise, recognise, behaviour, etc.)
2. Body Full: 250–400 words. If over 400, trim the least important sentences from body paragraphs. Never cut the lead sentence or the "On [date]" paragraph.
3. Structure: (1) Lead sentence — standalone one-sentence summary. (2) Second paragraph MUST start "On [date], [full authority name]...". (3) Two to three factual body paragraphs. (4) No closing forward-looking sentence.
4. Never use "should". Replace with "is required to", "must" (only for legal obligation), or "the authority finds".
5. Every factual finding or regulatory conclusion MUST be attributed: "IMY finds...", "The CNIL determined...", etc. Never state a finding as a standalone fact.
6. No em dashes. Use commas or colons.
7. No advice. No "organisations should review...".
8. No characterising adjectives: never "landmark", "significant", "robust", "major".

Output ONLY a JSON object: {"title": "...", "summary": "..."} — no markdown fences, no other text."""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def llm_fix(at_id, d):
    s = d.get('summary', '')
    issues = needs_llm_fix(s)
    issue_str = ', '.join(issues)
    user_msg = (
        f"Fix the following story. Issues to fix: {issue_str}\n\n"
        f"Current title: {d.get('gen_title','')}\n\n"
        f"Current summary:\n{s}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=FIX_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ─── Attribution check ───────────────────────────────────────────────────────

ATTR_SYSTEM = """You are a sub-editor checking PAI regulatory news for attribution.
Every sentence that states a regulatory finding, legal conclusion, or determination must be attributed to the authority using phrases like "IMY finds...", "The CNIL determined...", "The authority states...", "IRDAI notes...", etc.

Find any sentences that state regulatory facts without attribution and fix them. Do not change anything else.

If no attribution issues are found, return the summary unchanged.

Output ONLY a JSON object: {"title": "...", "summary": "..."} — no markdown fences."""

def attribution_check(at_id, d):
    s = d.get('summary', '')
    user_msg = (
        f"Check and fix attribution in this story.\n\n"
        f"Title: {d.get('gen_title','')}\n\n"
        f"Summary:\n{s}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=ATTR_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    drafts = json.load(open(DRAFTS_FILE))

    # Pass 1: British spelling (all 240, no LLM)
    spelling_fixed = 0
    for at_id, d in drafts.items():
        original = d.get('summary', '')
        fixed = british_spelling(original)
        if fixed != original:
            d['summary'] = fixed
            spelling_fixed += 1
        t_original = d.get('gen_title', '')
        t_fixed = british_spelling(t_original)
        if t_fixed != t_original:
            d['gen_title'] = t_fixed
    print(f"Pass 1 — British spelling fixed in {spelling_fixed} stories")

    # Pass 2: LLM fix for structural/length/should issues
    to_fix = [(at_id, d) for at_id, d in drafts.items() if needs_llm_fix(d.get('summary',''))]
    print(f"Pass 2 — {len(to_fix)} stories need LLM structural fix")

    fixed = 0
    errors = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(llm_fix, at_id, d): at_id for at_id, d in to_fix}
        for i, fut in enumerate(as_completed(futures), 1):
            at_id = futures[fut]
            try:
                result = fut.result()
                drafts[at_id]['summary'] = result.get('summary', drafts[at_id]['summary'])
                if result.get('title'):
                    drafts[at_id]['gen_title'] = result['title']
                fixed += 1
                print(f"  [{i}/{len(to_fix)}] fixed {at_id[:12]}")
            except Exception as e:
                errors.append((at_id, str(e)))
                print(f"  [{i}/{len(to_fix)}] ERROR {at_id[:12]}: {e}")

    print(f"Pass 2 done — {fixed} fixed, {len(errors)} errors")

    # Pass 3: Attribution check (all 240, Haiku)
    print(f"Pass 3 — Attribution check on all {len(drafts)} stories")
    attr_fixed = 0
    attr_errors = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(attribution_check, at_id, d): at_id for at_id, d in drafts.items()}
        for i, fut in enumerate(as_completed(futures), 1):
            at_id = futures[fut]
            try:
                result = fut.result()
                new_summary = result.get('summary', '')
                if new_summary and new_summary != drafts[at_id].get('summary',''):
                    drafts[at_id]['summary'] = new_summary
                    attr_fixed += 1
                if i % 20 == 0:
                    print(f"  {i}/{len(drafts)} checked...")
            except Exception as e:
                attr_errors.append((at_id, str(e)))

    print(f"Pass 3 done — {attr_fixed} attribution fixes, {len(attr_errors)} errors")

    # Save
    json.dump(drafts, open(DRAFTS_FILE, 'w'), ensure_ascii=False, indent=2)
    print(f"\nSaved to {DRAFTS_FILE}")

    # Final compliance check
    items = list(drafts.values())
    under250 = sum(1 for d in items if len(d.get('summary','').split()) < 250)
    over400  = sum(1 for d in items if len(d.get('summary','').split()) > 400)
    starts_on2 = sum(1 for d in items if second_para_starts_on(d.get('summary','')))
    has_should = sum(1 for d in items if ' should ' in d.get('summary','').lower())
    has_em     = sum(1 for d in items if '—' in d.get('summary',''))
    print(f"\nFinal compliance:")
    print(f"  Words 250-400: {len(items)-under250-over400}  under 250: {under250}  over 400: {over400}")
    print(f"  Para 2 starts 'On': {starts_on2}/{len(items)}")
    print(f"  'should': {has_should}  em-dash: {has_em}")

    if errors:
        print(f"\nLLM fix errors: {errors}")
    if attr_errors:
        print(f"Attribution errors: {attr_errors[:5]}")

if __name__ == "__main__":
    main()
