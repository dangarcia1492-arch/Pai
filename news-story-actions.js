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
