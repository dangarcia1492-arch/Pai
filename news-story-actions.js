/* Community channel chip — injected into .story-related on every news story.
 * Maps story type + jurisdiction → the best community channel.
 * One file change covers all 940+ story pages.
 */
(function () {
  var EU_COUNTRIES = ['austria','belgium','bulgaria','croatia','cyprus','czechia','czech republic','denmark',
    'estonia','finland','france','germany','greece','hungary','ireland','italy','latvia','lithuania',
    'luxembourg','malta','netherlands','poland','portugal','romania','slovakia','slovenia','spain','sweden',
    'european union','eu','norway','iceland','liechtenstein'];
  var APAC_COUNTRIES = ['australia','china','hong kong','india','indonesia','japan','malaysia',
    'new zealand','philippines','singapore','south korea','taiwan','thailand','vietnam'];
  var US_STATES = ['california','colorado','texas','virginia','connecticut','utah','iowa','oregon',
    'indiana','tennessee','florida','new york state','new jersey','illinois','washington'];

  var CHANNEL_META = {
    'enforcement-watch': 'Enforcement actions and regulatory decisions across all jurisdictions',
    'eu-ai-act':         'EU AI Act implementation — obligations, timelines, guidance',
    'eu':                'European Union regulatory updates — GDPR, AI Act, NIS2 and more',
    'uk':                'United Kingdom — ICO, FCA, CMA regulatory developments',
    'us-federal':        'US federal regulatory developments — FTC, DOJ, NIST, OSTP',
    'us-states':         'US state-level privacy and AI legislation',
    'ccpa-cpra':         'California privacy law — CCPA, CPRA, CPPA rulemaking',
    'apac':              'Asia-Pacific regulatory updates across all jurisdictions',
    'dpia':              'Data Protection Impact Assessments — methodology and practice',
    'incident-response': 'Breach and incident response — notification, containment, post-incident',
    'sccs-transfers':    'Standard Contractual Clauses and international data transfers',
    'vendor-risk':       'Third-party and supplier risk management',
    'model-cards':       'AI model documentation and transparency requirements',
    'gc-roundtable':     'General Counsel discussion — strategy, board reporting, legal risk',
    'privacy-ops':       'Privacy operations and programme management',
  };

  function mapChannel(type, juris, title) {
    var t = (type  || '').toLowerCase();
    var j = (juris || '').toLowerCase();
    var h = (title || '').toLowerCase();

    // Title-based topic signals take priority
    if (/\bai act\b/.test(h))                            return 'eu-ai-act';
    if (/\bsccs?\b|standard contractual\b/.test(h))      return 'sccs-transfers';
    if (/\bdpia\b|impact assessment/.test(h))            return 'dpia';
    if (/\bincident\b|\bbreach\b|\bnotif/.test(h))       return 'incident-response';
    if (/\bvendor\b|\bsupplier\b|\bthird.party/.test(h)) return 'vendor-risk';
    if (/\bmodel card\b|\btransparency.*ai\b/.test(h))   return 'model-cards';

    // Enforcement type → always enforcement-watch regardless of jurisdiction
    if (t === 'enforcement' || t === 'enf')              return 'enforcement-watch';

    // California first (before generic US)
    if (j === 'california' || /california|ccpa|cpra|cppa/.test(h)) return 'ccpa-cpra';

    // Jurisdiction mapping
    if (j === 'united kingdom' || j === 'uk')            return 'uk';
    if (j === 'united states' || j === 'us' || j === 'us federal') return 'us-federal';
    if (US_STATES.indexOf(j) !== -1)                     return 'us-states';
    if (EU_COUNTRIES.indexOf(j) !== -1)                  return 'eu';
    if (APAC_COUNTRIES.indexOf(j) !== -1)                return 'apac';

    // Fallback for unmatched: enforcement-watch is most active
    return 'enforcement-watch';
  }

  function initCommunityChip() {
    var typeEl  = document.querySelector('.eb-type');
    var jurisEl = document.querySelector('.eb-juris');
    var titleEl = document.querySelector('h1.story-title') || document.querySelector('h1');
    var type    = typeEl  ? typeEl.textContent.trim()  : '';
    var juris   = jurisEl ? jurisEl.textContent.trim() : '';
    var title   = titleEl ? titleEl.textContent.trim() : '';

    var slug = mapChannel(type, juris, title);
    var desc = CHANNEL_META[slug] || '';

    var relSection = document.querySelector('.story-related');
    if (!relSection) return;
    if (relSection.querySelector('.pai-community-chip')) return; // idempotent

    var chip = document.createElement('a');
    chip.href = 'pai-app-chat.html#' + slug;
    chip.target = '_blank';
    chip.rel = 'noopener';
    chip.className = 'pai-community-chip';
    chip.style.cssText = [
      'display:flex;align-items:center;gap:14px',
      'padding:14px 18px',
      'margin:0 0 20px 0',
      'background:#f0faf8',
      'border:1px solid #c3e8e3',
      'border-left:3px solid #0e8a7d',
      'border-radius:6px',
      'text-decoration:none',
      'color:inherit',
      'transition:background .12s,border-color .12s',
      'cursor:pointer',
    ].join(';');

    chip.innerHTML =
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0e8a7d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">'
      + '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
      + '</svg>'
      + '<div style="flex:1;min-width:0">'
      + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">'
      + '<span style="font-size:13px;font-weight:700;color:#0a4f46">Discuss in community</span>'
      + '<span style="font-size:12px;font-weight:700;color:#0e8a7d;background:#d4f0ec;padding:2px 8px;border-radius:3px">#' + slug + '</span>'
      + '</div>'
      + '<div style="font-size:12.5px;color:#4a6670;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + desc + '</div>'
      + '</div>'
      + '<span style="font-size:12px;font-weight:600;color:#0e8a7d;white-space:nowrap;display:flex;align-items:center;gap:4px">'
      + 'Open'
      + '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
      + '</span>';

    chip.addEventListener('mouseenter', function () {
      chip.style.background = '#e3f5f2';
      chip.style.borderColor = '#0e8a7d';
    });
    chip.addEventListener('mouseleave', function () {
      chip.style.background = '#f0faf8';
      chip.style.borderColor = '#c3e8e3';
    });

    var relGrid = relSection.querySelector('.rel-grid');
    if (relGrid) {
      relSection.insertBefore(chip, relGrid);
    } else {
      var relTitle = relSection.querySelector('.rel-title');
      if (relTitle) relTitle.after(chip);
      else relSection.insertBefore(chip, relSection.firstChild);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommunityChip);
  } else {
    initCommunityChip();
  }
})();


/* "Report broken link" button on every news story page.
 *
 * Posts a JSON report to /api/report-broken-link (Cloudflare Pages Function
 * that forwards via Resend to david@principlesai.org). No mailto, no client
 * mail app required.
 *
 * Page-shape contract (from build_news_story_pages.py / IMY chrome):
 *   <section class="story-sources"><div class="src-title">Sources</div>
 *     <ul><li><a href="…">…</a></li>…</ul><p class="src-note">…</p>
 *   </section>
 */
(function () {
  function init() {
    var sourcesSection = document.querySelector('.story-sources');
    if (!sourcesSection) return;
    if (sourcesSection.querySelector('.pai-report-broken-link-wrap')) return;  // idempotent

    var firstSourceLink = sourcesSection.querySelector('ul li a[href]');
    var sourceUrl = firstSourceLink ? firstSourceLink.href : '';
    var titleEl = document.querySelector('h1.story-title') || document.querySelector('h1');
    var title = (titleEl ? titleEl.textContent : document.title || '').trim();
    var pageUrl = window.location.href;

    var wrap = document.createElement('div');
    wrap.className = 'pai-report-broken-link-wrap';
    wrap.style.cssText = 'margin-top:18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pai-report-broken-link';
    btn.setAttribute('title', 'Send a report to PAI — no mail client needed.');
    btn.style.cssText =
      'display:inline-flex;align-items:center;gap:8px;'
      + 'padding:9px 16px;'
      + 'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;'
      + 'font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;'
      + 'color:#a4660b;background:#fff4e1;'
      + 'border:1.5px solid #f0c97a;border-radius:5px;'
      + 'text-decoration:none;cursor:pointer;'
      + 'transition:background .12s,border-color .12s,color .12s;';
    btn.innerHTML =
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">'
      + '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
      + '<line x1="12" y1="9" x2="12" y2="13"/>'
      + '<line x1="12" y1="17" x2="12.01" y2="17"/>'
      + '</svg>'
      + '<span>Report broken link</span>';

    btn.addEventListener('mouseenter', function () {
      btn.style.background = '#fde8c0'; btn.style.borderColor = '#e0b35e';
    });
    btn.addEventListener('mouseleave', function () {
      btn.style.background = '#fff4e1'; btn.style.borderColor = '#f0c97a';
    });

    var status = document.createElement('span');
    status.className = 'pai-report-broken-link-status';
    status.style.cssText = 'font-size:12px;color:#5e6878;font-style:italic;';

    btn.addEventListener('click', function () {
      if (btn.dataset.busy === '1') return;
      btn.dataset.busy = '1';
      var origLabel = btn.querySelector('span').textContent;
      btn.querySelector('span').textContent = 'Sending…';
      btn.style.opacity = '0.65';
      status.textContent = '';
      status.style.color = '#5e6878';

      fetch('/api/report-broken-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_title: title,
          story_url:   pageUrl,
          source_url:  sourceUrl
        })
      })
      .then(function (r) {
        return r.json().catch(function () { return { ok: r.ok }; }).then(function (j) { return { ok: r.ok, status: r.status, body: j }; });
      })
      .then(function (res) {
        if (res.ok) {
          btn.querySelector('span').textContent = 'Reported';
          btn.style.opacity = '1';
          btn.style.color = '#2e844a';
          btn.style.background = '#e8f5ee';
          btn.style.borderColor = '#9bcfaf';
          status.textContent = 'Thanks — the team will fix it.';
          status.style.color = '#2e844a';
          btn.disabled = true;
        } else {
          btn.querySelector('span').textContent = origLabel;
          btn.style.opacity = '1';
          btn.dataset.busy = '';
          status.textContent = 'Could not send (status ' + res.status + '). Try again, or email david@principlesai.org.';
          status.style.color = '#a4660b';
        }
      })
      .catch(function (e) {
        btn.querySelector('span').textContent = origLabel;
        btn.style.opacity = '1';
        btn.dataset.busy = '';
        status.textContent = 'Network error. Try again, or email david@principlesai.org.';
        status.style.color = '#a4660b';
      });
    });

    wrap.appendChild(btn);
    wrap.appendChild(status);
    sourcesSection.appendChild(wrap);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
