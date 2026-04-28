"""
Demo story generator for PAI platform (Apr 29 demo: Ikea Sweden + India lawyer).
Creates 4 story HTML pages, updates news.json, refreshes news wire.
  Build:   python3 gen_demo_stories.py
  Restore: python3 gen_demo_stories.py --restore
"""
import json, re, sys, shutil
from pathlib import Path

RESTORE = '--restore' in sys.argv

# ─── Story definitions ───────────────────────────────────────────────────────

STORIES = [
    {
        "slug":       "imy-sportadmin-2026",
        "at_id":      "rect1dEDtLDZkbC3c",
        "title":      "IMY imposes SEK 6 million fine on Sportadmin after data breach exposes 2.1 million individuals",
        "breadcrumb": "IMY fines Sportadmin SEK 6 M",
        "scope_chip": "Sweden · Enforcement",
        "reviewed":   "Editor-reviewed · 28 Jan 2026",
        "juris":      "Sweden",
        "auth_slug":  "#",
        "auth_name":  "IMY",
        "eb_type":    "enf",
        "eb_type_lbl":"Enforcement",
        "date":       "28 January 2026",
        "deck": (
            "Sweden's data protection authority has imposed an administrative fine of SEK 6 million "
            "(approximately EUR 520,000) on sports administration platform Sportadmin after a cyber attack "
            "in January 2025 exposed personal data of more than 2.1 million individuals, including "
            "children, personal identity numbers and data on persons with protected identity."
        ),
        "body": [
            (
                "The Integritetsskyddsmyndigheten (IMY) issued its decision on 28 January 2026 following a "
                "supervision investigation opened after a threat actor gained access to Sportadmin's systems "
                "and subsequently published the extracted data on the Darknet. IMY imposed an administrative "
                "fine of SEK 6 million (approximately EUR 520,000), the authority's largest enforcement "
                "action so far in 2026."
            ),
            (
                "The leaked data covered more than 2.1 million individuals and included names, contact "
                "details, personal identity numbers and information about which sport and sports club each "
                "individual was associated with. The data also included sensitive health data and, in some "
                "cases, information relating to persons with protected identity, meaning that their personal "
                "data is subject to statutory confidentiality restrictions under Swedish law."
            ),
            (
                "IMY identified both technical and organisational deficiencies in Sportadmin's security "
                "programme. The authority found that Sportadmin was aware of known weaknesses in its systems "
                "and elevated attack risks for a significant period prior to the attack but did not take "
                "adequate remedial steps. Specifically, the company lacked routines to detect deficiencies "
                "in existing security measures and did not operate an intrusion-detection system capable of "
                "identifying intrusions or attempted intrusions in real time."
            ),
            (
                "IMY found a violation of Article 32 of the General Data Protection Regulation, which "
                "requires controllers to implement appropriate technical and organisational measures to ensure "
                "a level of security appropriate to the risk. Director General Eric Leijonram stated that "
                "cyber attacks can never be entirely ruled out but that there is an obligation to maintain "
                "a level of security appropriate to the personal data being processed, and that Sportadmin "
                "had demonstrated a degree of passivity in addressing known risks."
            ),
        ],
        "ops": [
            "Art. 32 GDPR security obligations extend to operationally verified controls, not merely documented policies.",
            "Known vulnerabilities with no adequate remediation plan are treated as aggravating factors by IMY.",
            "Real-time intrusion detection is regarded by IMY as a baseline requirement when processing personal identity numbers and children's health data at scale.",
            "Data categories in scope: children's data, special-category health data, personal identity numbers, protected-identity records.",
            "SEK 6 million (approx. EUR 520,000) reflects volume and sensitivity of exposure; maximum GDPR penalty is the higher of EUR 10 million or 2% of global annual turnover (Art. 83(4)).",
        ],
        "sources": [
            {
                "label": "Supervisory decision, IMY (28 Jan 2026)",
                "url":   "https://www.imy.se/en/news/administrative-fine-against-sportadmin/",
                "meta":  "imy.se"
            },
            {
                "label": "GDPR Article 32",
                "url":   "https://gdpr-info.eu/art-32-gdpr/",
                "meta":  "gdpr-info.eu"
            },
        ],
        "src_note": "All claims derived from the published IMY supervisory decision of 28 January 2026.",
        "related": [
            {"kick":"Authority","h":"Integritetsskyddsmyndigheten","p":"Swedish DPA · GDPR supervisor for Sweden","href":"#"},
            {"kick":"Instrument","h":"GDPR Article 32","p":"Security of processing: appropriate technical and organisational measures","href":"#"},
            {"kick":"Topic","h":"Enforcement: Data Security","p":"DPA enforcement actions for security failures across Europe","href":"#"},
        ],
        "claim_id": "pai-20260128-imy-sportadmin-art32",
        "summary": (
            "Sweden's Integritetsskyddsmyndigheten (IMY) imposed an administrative fine of SEK 6 million "
            "(approx. EUR 520,000) on Sportadmin on 28 January 2026 after a cyber attack exposed personal "
            "data of more than 2.1 million individuals including children's names, personal identity numbers, "
            "health data and protected-identity records. IMY found violations of Article 32 GDPR, citing "
            "known but unaddressed security weaknesses and absence of real-time intrusion detection."
        ),
    },
    {
        "slug":       "imy-tee-2026",
        "at_id":      "rec71eprLP5kMi8f0",
        "title":      "IMY concludes trusted execution environments strengthen GDPR compliance for connected-vehicle data",
        "breadcrumb": "IMY: TEE guidance for connected vehicles",
        "scope_chip": "Sweden · Guidance",
        "reviewed":   "Editor-reviewed · 17 Apr 2026",
        "juris":      "Sweden",
        "auth_slug":  "#",
        "auth_name":  "IMY",
        "eb_type":    "guid",
        "eb_type_lbl":"Guidance",
        "date":       "17 April 2026",
        "deck": (
            "The Swedish Authority for Privacy Protection has concluded that trusted execution environments "
            "offer technically verifiable data-in-use controls that exceed the guarantees available from "
            "conventional cloud solutions, a finding with direct implications for automotive, logistics and "
            "any sector processing personal data outside a device's local environment."
        ),
        "body": [
            (
                "The Integritetsskyddsmyndigheten (IMY) published its conclusions on 17 April 2026 "
                "(reference IMY-2026-5444) following a regulatory sandbox project conducted in partnership "
                "with Volvo Group, Ericsson and CanaryBit. The project examined whether and how personal "
                "data collected by cameras and sensors on Volvo trucks, including video footage in which "
                "road users appear, can lawfully be transferred to and processed in a trusted execution "
                "environment hosted by a mobile network operator within its telecommunications "
                "infrastructure."
            ),
            (
                "IMY finds that trusted execution environments reduce risks associated with external "
                "processing of personal data, particularly the risk of unauthorised or unintended access. "
                "Through built-in protection mechanisms, both access to data and which code is permitted "
                "to execute are controlled, strengthening trust in the technology provider. IMY emphasises "
                "that key management and the verifier function, which performs attestations of the "
                "environment to confirm it is secure and running correct programme code, must remain within "
                "the data controller's sphere of control for this assessment to hold in practice."
            ),
            (
                "On GDPR applicability, IMY concludes that the processing constitutes processing by Volvo "
                "as controller within the meaning of Article 4(2) of the GDPR. The authority notes that "
                "data are processed automatically and that video material in which road users appear "
                "constitutes personal data. On the role of the mobile network operator, IMY finds "
                "circumstances that argue against sole or joint controller status and also against processor "
                "status under Article 28, given the operator's very limited ability to fulfil processor "
                "obligations, including protecting data subjects' rights."
            ),
            (
                "IMY notes that organisations wishing to rely on a trusted execution environment as a GDPR "
                "safeguard must retain meaningful technical control over the environment: placing the "
                "verifier function with the infrastructure provider undermines the legal classification. "
                "IMY's guidance provides a framework applicable beyond automotive to any connected-device "
                "deployment involving external data processing."
            ),
        ],
        "ops": [
            "Trusted execution environments can constitute a valid Art. 32 GDPR security measure where the controller retains control over key management and the verifier function.",
            "Video footage capturing road users qualifies as personal data; Art. 4(2) GDPR processing by the controller applies from collection through transfer and external processing.",
            "Mobile network operators providing TEE infrastructure do not automatically qualify as processor under Art. 28 GDPR if their ability to fulfil processor obligations is too limited.",
            "Controller accountability under Art. 5(2) GDPR requires demonstrable technical evidence that the operator cannot access processed data content, not merely contractual assurances.",
            "IMY's sandbox conclusions are persuasive guidance, not binding law, but represent the authority's supervisory position for enforcement purposes.",
        ],
        "sources": [
            {
                "label": "IMY: Use of Trusted Execution Environment (17 Apr 2026, ref IMY-2026-5444)",
                "url":   "https://www.imy.se/en/publications/betrodda-exekveringsmiljoer-for-uppkopplade-fordon/",
                "meta":  "imy.se"
            },
            {
                "label": "GDPR Article 4(2): Definition of processing",
                "url":   "https://gdpr-info.eu/art-4-gdpr/",
                "meta":  "gdpr-info.eu"
            },
            {
                "label": "GDPR Article 28: Processor obligations",
                "url":   "https://gdpr-info.eu/art-28-gdpr/",
                "meta":  "gdpr-info.eu"
            },
        ],
        "src_note": "All claims derived from the published IMY sandbox report of 17 April 2026 (IMY-2026-5444).",
        "related": [
            {"kick":"Authority","h":"Integritetsskyddsmyndigheten","p":"Swedish DPA · GDPR supervisor for Sweden","href":"#"},
            {"kick":"Instrument","h":"GDPR Article 32: Security","p":"Technical and organisational measures for data in use","href":"#"},
            {"kick":"Topic","h":"AI and Connected Vehicles","p":"GDPR compliance for automated data collection and processing","href":"#"},
        ],
        "claim_id": "pai-20260417-imy-tee-sandbox",
        "summary": (
            "Sweden's IMY published sandbox conclusions on 17 April 2026 finding that trusted "
            "execution environments (TEEs) can constitute a valid GDPR Article 32 security measure for "
            "connected-vehicle data, provided the data controller retains control over key management "
            "and the verifier function. The guidance arose from a project with Volvo Group, Ericsson "
            "and CanaryBit and applies to any sector processing personal data outside a device's local "
            "environment."
        ),
    },
    {
        "slug":       "imy-priorities-2026",
        "at_id":      "recDVBrXMzVHDTvAz",
        "title":      "IMY targets AI in the public sector, children's data and crime prevention tools in 2026 supervision plan",
        "breadcrumb": "IMY: 2026 supervision priorities",
        "scope_chip": "Sweden · Guidance",
        "reviewed":   "Editor-reviewed · 23 Feb 2026",
        "juris":      "Sweden",
        "auth_slug":  "#",
        "auth_name":  "IMY",
        "eb_type":    "guid",
        "eb_type_lbl":"Guidance",
        "date":       "23 February 2026",
        "deck": (
            "Sweden's data protection authority has announced that its supervision and guidance work "
            "in 2026 will concentrate on artificial intelligence in the public sector, the protection of "
            "children and young people's personal data, and data-intensive law enforcement tools "
            "including biometric data collection."
        ),
        "body": [
            (
                "The Integritetsskyddsmyndigheten (IMY) published its 2026 supervision priorities on "
                "23 February 2026. Each year the authority selects priority areas based on its assessment "
                "of where privacy risks are most significant or where additional guidance will most improve "
                "compliance. Director General Eric Leijonram stated that IMY focuses on areas where its "
                "efforts can make the most difference."
            ),
            (
                "The first priority is the use of AI by the public sector. IMY notes that AI is "
                "increasingly being introduced into public services and that citizens in contact with "
                "those services often have no alternative and cannot avoid the processing. Where AI "
                "systems also handle sensitive personal data, IMY states that high demands are placed "
                "on privacy protection. During 2026, IMY will follow up on how the public sector uses "
                "AI to support public services and assess whether deployments meet GDPR requirements."
            ),
            (
                "The second priority covers data protection for children and young people. IMY observes "
                "that children and young people use the internet, social media and applications daily "
                "without always understanding the risks, and that their personal data merits specific "
                "protection. The authority will work to increase awareness of data protection risks "
                "among young people themselves and among adults who handle their data, including "
                "guardians and schools."
            ),
            (
                "The third priority is law enforcement tools from a data protection perspective. "
                "IMY will examine tools available to law enforcement agencies, including newer coercive "
                "measures and the collection of biometric data. The authority acknowledges that law "
                "enforcement agencies need effective tools to prevent and solve crimes but notes that "
                "some of these tools involve significant restrictions on individuals' right to privacy."
            ),
        ],
        "ops": [
            "Companies supplying AI systems to Swedish public authorities are within IMY's declared 2026 supervision scope, particularly for sensitive-data use cases.",
            "Children's personal data processed by schools, apps and platforms is an active 2026 priority area for IMY guidance and supervision.",
            "Law enforcement technology suppliers operating in Sweden, including biometric and covert surveillance tools, are within the 2026 supervision scope.",
            "IMY supervises private sector processors as well as public controllers: supplying a non-compliant system to a Swedish authority carries direct exposure.",
            "IMY can issue corrective measures, administrative fines and binding orders; the 2026 priority list signals the areas where resources are directed.",
        ],
        "sources": [
            {
                "label": "IMY: Priorities for 2026 (23 Feb 2026)",
                "url":   "https://www.imy.se/en/news/imys-prioriteringar-2026--ai-barn-och-brottsbekampning/",
                "meta":  "imy.se"
            },
        ],
        "src_note": "All claims derived from the IMY published priorities statement of 23 February 2026.",
        "related": [
            {"kick":"Authority","h":"Integritetsskyddsmyndigheten","p":"Swedish DPA · GDPR supervisor for Sweden","href":"#"},
            {"kick":"Topic","h":"AI in the Public Sector","p":"GDPR compliance for government AI deployments across Europe","href":"#"},
            {"kick":"Topic","h":"Children's Data Protection","p":"Age-appropriate design and special protections for minors","href":"#"},
        ],
        "claim_id": "pai-20260223-imy-priorities-2026",
        "summary": (
            "Sweden's IMY announced its three supervision priorities for 2026 on 23 February 2026: "
            "AI use by the public sector, protection of children and young people's data, and "
            "law enforcement tools including biometric data collection. Companies supplying AI systems "
            "to Swedish public bodies or processing children's data are within the declared supervision "
            "scope for 2026."
        ),
    },
    {
        "slug":       "irdai-cyber-2026",
        "at_id":      "recacVs7Yu5RHCm0g",
        "title":      "IRDAI issues revised information and cyber security guidelines for India's insurance sector",
        "breadcrumb": "IRDAI: Cyber Security Guidelines 2026",
        "scope_chip": "India · Regulatory Guidance",
        "reviewed":   "Editor-reviewed · 6 Apr 2026",
        "juris":      "India",
        "auth_slug":  "#",
        "auth_name":  "IRDAI",
        "eb_type":    "guid",
        "eb_type_lbl":"Guidance",
        "date":       "6 April 2026",
        "deck": (
            "India's insurance sector regulator has issued revised information and cyber security "
            "guidelines requiring all insurers, insurance intermediaries and the Insurance Information "
            "Bureau of India to implement updated minimum standards and governance mechanisms with "
            "effect from the current financial year."
        ),
        "body": [
            (
                "The Insurance Regulatory and Development Authority of India (IRDAI) issued Circular "
                "reference IRDAI/GA&HR/CIR/MISC/51/4/2026 on 6 April 2026. The revised guidelines "
                "supersede the IRDAI Guidelines on Information and Cyber Security issued under "
                "Circular IRDAI/GA&HR/GDL/MISC/88/04/2023 dated 24 April 2023. The revision reflects "
                "the evolving cyber threat landscape, feedback received from the industry, and "
                "recommendations of IRDAI committees."
            ),
            (
                "The 2026 guidelines are intended to enable the insurance sector to further strengthen "
                "its defences and related governance mechanisms. The guidelines set out the minimum "
                "standards and governance mechanisms to be adopted by all regulated entities. IRDAI "
                "states that the update addresses emerging cyber threats not adequately covered by "
                "the 2023 framework."
            ),
            (
                "The circular applies with immediate effect to all insurers including foreign reinsurance "
                "branches, and to all insurance intermediaries: brokers, corporate agents, web aggregators, "
                "third-party administrators, insurance marketing firms, insurance repositories, insurance "
                "self-network platforms, corporate surveyors, motor insurance service providers and "
                "common service centres. The Insurance Information Bureau of India (IIB) is also within "
                "scope."
            ),
            (
                "All regulated entities must comply with the guidelines from the current financial year "
                "(2026-27). IRDAI's Executive Director A. R. Nithiyanantham signed the circular. Full "
                "revised guidelines are attached as Annexure B to the circular, with a summary of major "
                "changes from the 2023 framework set out in Annexure A."
            ),
        ],
        "ops": [
            "Compliance is mandatory from financial year 2026-27; no grace period is stated in the circular.",
            "Scope is broad: all insurers, all intermediary categories and the IIB are within scope, including foreign reinsurance branches.",
            "The 2026 guidelines supersede the 2023 circular entirely; entities operating under 2023 controls must review against the new minimum standards.",
            "A summary of major changes from 2023 to 2026 is provided in Annexure A of the circular.",
            "IRDAI circular reference: IRDAI/GA&HR/CIR/MISC/51/4/2026 dated 6 April 2026.",
        ],
        "sources": [
            {
                "label": "IRDAI Circular IRDAI/GA&HR/CIR/MISC/51/4/2026 (6 Apr 2026)",
                "url":   "https://irdai.gov.in/",
                "meta":  "irdai.gov.in"
            },
        ],
        "src_note": "All claims derived from IRDAI Circular IRDAI/GA&HR/CIR/MISC/51/4/2026 dated 6 April 2026.",
        "related": [
            {"kick":"Authority","h":"Insurance Regulatory and Development Authority of India","p":"Sector regulator for all insurance entities in India","href":"#"},
            {"kick":"Topic","h":"Cyber Security Regulation","p":"Mandatory cyber standards across financial services globally","href":"#"},
            {"kick":"Topic","h":"India: AI and Data Governance","p":"Regulatory developments across India's data and technology landscape","href":"#"},
        ],
        "claim_id": "pai-20260406-irdai-cyber-guidelines-2026",
        "summary": (
            "India's IRDAI issued Circular IRDAI/GA&HR/CIR/MISC/51/4/2026 on 6 April 2026 "
            "requiring all insurers, intermediaries and the IIB to comply with revised information "
            "and cyber security guidelines from financial year 2026-27. The 2026 guidelines "
            "supersede the 2023 circular and address the evolving cyber threat landscape. No "
            "grace period is stated."
        ),
    },
]


# ─── HTML generation ──────────────────────────────────────────────────────────

TEMPLATE = Path("pai-app-news-story-ico-nhs.html").read_text()

cut_start = re.search(r'<div class="page-statusbar">', TEMPLATE)
cut_end   = re.search(r'<!-- ==BEGIN_JUR_HTML==', TEMPLATE)

assert cut_start and cut_end, "Could not locate content bounds in template"

SHELL_HEAD  = TEMPLATE[:cut_start.start()]
SHELL_TAIL  = TEMPLATE[cut_end.start():]


def story_html(s):
    body_paras = "\n    ".join(f"<p>{p}</p>" for p in s["body"])
    ops_items  = "\n      ".join(f"<li>{o}</li>" for o in s["ops"])
    src_items  = "\n    ".join(
        f'<li><a href="{src["url"]}" target="_blank" rel="noopener">{src["label"]}</a>'
        f'<span class="src-meta">{src["meta"]}</span></li>'
        for src in s["sources"]
    )
    rel_cards = "\n      ".join(
        f'<a class="rel-card" href="{r["href"]}">'
        f'<div class="rel-kick">{r["kick"]}</div>'
        f'<div class="rel-h">{r["h"]}</div>'
        f'<div class="rel-p">{r["p"]}</div>'
        f'</a>'
        for r in s["related"]
    )

    return f"""  <div class="page-statusbar">
    <div class="ps-left">
      <span class="ps-breadcrumb">
        <a href="pai-app-news">News</a>
        <span class="ps-sep">&#8250;</span>
        <span class="ps-current">{s['breadcrumb']}</span>
      </span>
      <span class="ps-sep">&#183;</span>
      <span class="ps-scope-chip">{s['scope_chip']}</span>
      <span class="ps-sep">&#183;</span>
      <span class="ps-ok">{s['reviewed']}</span>
    </div>
  </div>

  <div class="story-eyebrow">
    <span class="eb-juris">{s['juris']}</span>
    <span class="eb-auth"><a href="{s['auth_slug']}">{s['auth_name']}</a></span>
    <span class="eb-dot">&#183;</span>
    <span class="eb-type {s['eb_type']}">{s['eb_type_lbl']}</span>
    <span class="eb-dot">&#183;</span>
    <span class="eb-date">{s['date']}</span>
  </div>

  <h1 class="story-title">{s['title']}</h1>

  <p class="story-deck">{s['deck']}</p>

  <section class="story-body">
    {body_paras}
  </section>

  <section class="story-ops">
    <div class="ops-title">Operational notes</div>
    <ul>
      {ops_items}
    </ul>
  </section>

  <section class="story-sources">
    <div class="src-title">Sources</div>
    <ul>
    {src_items}
    </ul>
    <p class="src-note">{s['src_note']} The PAI Research Team reviews each story against source before publication. Claim ID: <code>{s['claim_id']}</code>.</p>
  </section>

  <section class="story-related">
    <div class="rel-title">Related</div>
    <div class="rel-grid">
      {rel_cards}
    </div>
  </section>

  <div class="story-footer">
    <button class="btn-primary" onclick="this.textContent = this.textContent.indexOf('Saved') > -1 ? '&#9679; Save to watchlist' : '&#9679; Saved to watchlist';">&#9679; Save to watchlist</button>
    <span class="story-footer-note">Editor-reviewed &middot; published {s['date']} &middot; claim id: {s['claim_id']}</span>
  </div>

</div>
</div>

"""


def build_story_file(s):
    head = SHELL_HEAD.replace(
        "<title>PrinciplesAI — ICO fines NHS Trust · News</title>",
        f"<title>PrinciplesAI — {s['title'][:60]} · News</title>"
    )
    html = head + story_html(s) + SHELL_TAIL
    outpath = Path(f"pai-app-news-story-{s['slug']}.html")
    outpath.write_text(html)
    print(f"  Wrote {outpath} ({len(html):,} chars)")


# ─── news.json update ─────────────────────────────────────────────────────────

def update_news_json():
    nj = Path("news.json")
    backup = Path("news.json.backup-apr28")
    if not backup.exists():
        shutil.copy(nj, backup)
        print(f"  Backed up news.json -> {backup}")

    data = json.loads(nj.read_text())
    rows = data["rows"]

    updates = {s["at_id"]: s for s in STORIES}
    changed = 0
    for row in rows:
        if row.get("id") in updates:
            s = updates[row["id"]]
            row["title"]   = s["title"]
            row["summary"] = s["summary"]
            changed += 1

    nj.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"  Updated {changed} rows in news.json")


# ─── news wire update ─────────────────────────────────────────────────────────

NEW_LEAD = '''  <!-- LEAD -->
  <div class="news-lead">
    <div class="nl-kick">TODAY\'S LEAD &middot; SWEDEN &middot; &mdash; &middot; <span class="status-pill-sm enf">Enforcement</span></div>
    <h2><a href="pai-app-news-story-imy-sportadmin-2026">IMY imposes SEK 6 million fine on Sportadmin after data breach exposes 2.1 million individuals</a></h2>
    <p class="nl-deck">Sweden\'s data protection authority found violations of Article 32 GDPR, exposing names, personal identity numbers, health data and protected-identity records for over 2.1 million individuals including children, following a January 2025 cyber attack.</p>
    <div class="nl-footer">
      <span><strong>Type</strong> Enforcement</span>
      <span><strong>Authority</strong> IMY</span>
      <span><strong>Source</strong> <a href="https://www.imy.se" target="_blank" rel="noopener">imy.se &#8599;</a></span>
    </div>
    <button class="nl-save on" title="Saved" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
  </div>
'''

NEW_SECONDS = '''  <!-- SECONDS -->
  <div class="news-seconds">
    <div class="news-second">
      <div class="ns-kick">SECOND LEAD &middot; SWEDEN &middot; &mdash;</div>
      <h3><a href="pai-app-news-story-imy-tee-2026">IMY concludes trusted execution environments strengthen GDPR compliance for connected-vehicle data</a></h3>
      <div class="ns-meta"><span class="status-pill-sm guid">Guidance</span> &middot; Integritetsskyddsmyndigheten</div>
      <button class="ns-save" title="Save" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
    <div class="news-second">
      <div class="ns-kick">SECOND LEAD &middot; INDIA &middot; &mdash;</div>
      <h3><a href="pai-app-news-story-irdai-cyber-2026">IRDAI issues revised information and cyber security guidelines for India&#39;s insurance sector</a></h3>
      <div class="ns-meta"><span class="status-pill-sm guid">Guidance</span> &middot; Insurance Regulatory and Development Authority of India</div>
      <button class="ns-save" title="Save" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
  </div>
'''

NEW_WIRE_ROWS = '''    <!-- demo rows: Sweden + India -->
    <div class="wire-row">
      <div class="wr-ts">28 Jan</div>
      <div class="wr-jur">SE</div>
      <div class="wr-info">
        <h4><a href="pai-app-news-story-imy-sportadmin-2026">IMY imposes SEK 6 million fine on Sportadmin after data breach exposes 2.1 million individuals</a></h4>
        <div class="wr-src"><strong>Integritetsskyddsmyndigheten</strong> &middot; imy.se</div>
      </div>
      <div class="wr-tag enf">Enforcement</div>
      <button class="wr-star on" title="Saved" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
    <div class="wire-row">
      <div class="wr-ts">17 Apr</div>
      <div class="wr-jur">SE</div>
      <div class="wr-info">
        <h4><a href="pai-app-news-story-imy-tee-2026">IMY concludes trusted execution environments strengthen GDPR compliance for connected-vehicle data</a></h4>
        <div class="wr-src"><strong>Integritetsskyddsmyndigheten</strong> &middot; imy.se</div>
      </div>
      <div class="wr-tag guid">Guidance</div>
      <button class="wr-star" title="Save" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
    <div class="wire-row">
      <div class="wr-ts">23 Feb</div>
      <div class="wr-jur">SE</div>
      <div class="wr-info">
        <h4><a href="pai-app-news-story-imy-priorities-2026">IMY targets AI in the public sector, children&#39;s data and crime prevention tools in 2026 supervision plan</a></h4>
        <div class="wr-src"><strong>Integritetsskyddsmyndigheten</strong> &middot; imy.se</div>
      </div>
      <div class="wr-tag guid">Guidance</div>
      <button class="wr-star" title="Save" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
    <div class="wire-row">
      <div class="wr-ts">6 Apr</div>
      <div class="wr-jur">IN</div>
      <div class="wr-info">
        <h4><a href="pai-app-news-story-irdai-cyber-2026">IRDAI issues revised information and cyber security guidelines for India&#39;s insurance sector</a></h4>
        <div class="wr-src"><strong>Insurance Regulatory and Development Authority of India</strong> &middot; irdai.gov.in</div>
      </div>
      <div class="wr-tag guid">Guidance</div>
      <button class="wr-star" title="Save" onclick="saveToggle(event,this)"><svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button>
    </div>
'''


def update_news_wire():
    nwp = Path("pai-app-news.html")
    backup = Path("pai-app-news.html.backup-apr28")
    if not backup.exists():
        shutil.copy(nwp, backup)
        print(f"  Backed up pai-app-news.html -> {backup}")

    html = nwp.read_text()

    lead_m = re.search(r'<!-- LEAD -->.*?(?=<!-- SECONDS -->)', html, re.DOTALL)
    if lead_m:
        html = html[:lead_m.start()] + NEW_LEAD + html[lead_m.end():]
        print("  Replaced LEAD block")
    else:
        print("  WARNING: LEAD marker not found")

    sec_m = re.search(r'<!-- SECONDS -->.*?(?=<!-- WIRE \+ RIGHT RAIL)', html, re.DOTALL)
    if sec_m:
        html = html[:sec_m.start()] + NEW_SECONDS + html[sec_m.end():]
        print("  Replaced SECONDS block")
    else:
        print("  WARNING: SECONDS marker not found")

    wire_list_m = re.search(r'<div class="wire-list">', html)
    if wire_list_m:
        ins = wire_list_m.end()
        html = html[:ins] + "\n" + NEW_WIRE_ROWS + html[ins:]
        print("  Inserted 4 demo wire rows")
    else:
        print("  WARNING: wire-list not found")

    nwp.write_text(html)


# ─── Restore ──────────────────────────────────────────────────────────────────

def restore():
    for backup, original in [
        ("news.json.backup-apr28", "news.json"),
        ("pai-app-news.html.backup-apr28", "pai-app-news.html"),
    ]:
        b = Path(backup)
        if b.exists():
            shutil.copy(b, original)
            print(f"  Restored {original} from {backup}")
        else:
            print(f"  WARNING: {backup} not found")

    for s in STORIES:
        p = Path(f"pai-app-news-story-{s['slug']}.html")
        if p.exists():
            p.unlink()
            print(f"  Removed {p}")


# ─── main ─────────────────────────────────────────────────────────────────────

if RESTORE:
    print("=== RESTORING demo content ===")
    restore()
    print("Done. Commit and push to update the live site.")
else:
    print("=== BUILDING demo content ===")
    for s in STORIES:
        build_story_file(s)
    update_news_json()
    update_news_wire()
    print("Done. Commit and push to update the live site.")
