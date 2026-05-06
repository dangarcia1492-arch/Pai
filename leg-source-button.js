/**
 * Inject a prominent "View official source" button into the Source card on
 * every legislation staging page. The default-template rendering is a small
 * "domain.tld ↗" inline link inside an .auth-kv row — easy to miss. This
 * adds a bold CTA button at the bottom of the same Source .auth-card that
 * opens the regulator/government source URL in a new tab.
 *
 * Page-shape contract (from build_leg_pages.py / templates/leg.html.j2):
 *   <div class="auth-card">
 *     <div class="auth-card-title">Source</div>
 *     <div class="auth-kv"><span class="k">URL</span><span class="v"><a href="...">…</a></span></div>
 *     …
 *   </div>
 */
(function () {
  function init() {
    var cards = document.querySelectorAll('.auth-card');
    var sourceCard = null;
    for (var i = 0; i < cards.length; i++) {
      var t = cards[i].querySelector('.auth-card-title');
      if (t && (t.textContent || '').trim() === 'Source') { sourceCard = cards[i]; break; }
    }
    if (!sourceCard) return;
    if (sourceCard.querySelector('.pai-leg-source-btn')) return;  // idempotent

    // Find the URL anchor inside the URL row
    var anchor = null;
    var rows = sourceCard.querySelectorAll('.auth-kv');
    for (var j = 0; j < rows.length; j++) {
      var k = rows[j].querySelector('.k');
      if (!k || (k.textContent || '').trim() !== 'URL') continue;
      anchor = rows[j].querySelector('.v a[href]');
      break;
    }
    if (!anchor || !anchor.href || anchor.href === window.location.href + '#') return;

    var btn = document.createElement('a');
    btn.href = anchor.href;
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    btn.className = 'pai-leg-source-btn';
    btn.style.cssText =
      'display:inline-flex;align-items:center;gap:7px;'
      + 'margin:14px 0 4px;padding:8px 14px;'
      + 'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;'
      + 'font-size:10px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;'
      + 'color:#fff;background:#0176d3;'
      + 'border:1px solid #014486;border-radius:5px;'
      + 'text-decoration:none;cursor:pointer;'
      + 'box-shadow:0 1px 3px rgba(10,23,41,0.10);'
      + 'transition:background .12s, border-color .12s, transform .08s;';
    btn.innerHTML =
      '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">'
      + '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
      + '<polyline points="15 3 21 3 21 9"/>'
      + '<line x1="10" y1="14" x2="21" y2="3"/>'
      + '</svg>'
      + '<span>View official source</span>';

    btn.addEventListener('mouseenter', function () {
      btn.style.background = '#014486';
      btn.style.borderColor = '#032e61';
    });
    btn.addEventListener('mouseleave', function () {
      btn.style.background = '#0176d3';
      btn.style.borderColor = '#014486';
    });
    btn.addEventListener('mousedown', function () { btn.style.transform = 'translateY(1px)'; });
    btn.addEventListener('mouseup',   function () { btn.style.transform = ''; });
    btn.addEventListener('mouseleave',function () { btn.style.transform = ''; });

    sourceCard.appendChild(btn);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
