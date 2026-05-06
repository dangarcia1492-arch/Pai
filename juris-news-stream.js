/* PAI juris-page news stream renderer — reads news-by-juris/<iso>.json,
 * applies the hero-card selection rule (memory: feedback_juris_hero_lead_rule.md),
 * renders into <div class="nr-stream-grid" data-pai-news-stream></div>.
 *
 * Replaces hardcoded pai-app-news-story-* refs that violated the rule
 * "Never hardcode news-story refs in juris pages" (memory: 2026-05-06).
 *
 * Pages must set window.PAI_JURIS (canonical name, e.g. "Philippines") and
 * include this script after the markup that contains [data-pai-news-stream].
 */
function paiJurisNewsStreamRender() {
  if (!window.PAI_JURIS) return;

  // Canonical name → 2-letter ISO used by news-by-juris/*.json filenames
  var ISO_MAP = {
    'Philippines': 'ph', 'Nigeria': 'ng', 'India': 'in',
    'United Kingdom': 'gb', 'United States': 'us', 'United States of America': 'us', 'USA': 'us',
    'France': 'fr', 'Germany': 'de', 'Italy': 'it', 'Spain': 'es', 'Sweden': 'se',
    'Belgium': 'be', 'Netherlands': 'nl', 'Portugal': 'pt', 'Greece': 'gr',
    'Japan': 'jp', 'China': 'cn', 'India': 'in', 'South Korea': 'kr', 'Singapore': 'sg',
    'Australia': 'au', 'Canada': 'ca', 'Brazil': 'br', 'Argentina': 'ar', 'Mexico': 'mx',
    'European Union': 'eu', 'OECD': 'oecd', 'International': 'int',
    'Hamburg': 'hh', 'Hawaii': 'hi', 'New Hampshire': 'nh', 'New York': 'ny', 'California': 'ca',
    'Egypt': 'eg', 'Israel': 'il', 'Saudi Arabia': 'sa', 'Turkey': 'tr',
    'Indonesia': 'id', 'Malaysia': 'my', 'Philippines': 'ph', 'Thailand': 'th', 'Vietnam': 'vn',
    'Czech Republic': 'cz', 'Estonia': 'ee', 'Albania': 'al', 'Belarus': 'by'
  };

  var grid = document.querySelector('[data-pai-news-stream]');
  if (!grid) return;

  var iso = ISO_MAP[window.PAI_JURIS];
  if (!iso) return;

  // Type-priority for tie-breaking on same date
  var PRIORITY = { 'Enforcement': 4, 'Case law': 3, 'Legislation': 2, 'Guidance': 1, 'Update': 0, 'Blog': 0, 'Analysis': 0 };

  function escHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }
  function fmtDate(s) {
    if (!s) return '';
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
    if (!m) return s;
    var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return parseInt(m[3], 10) + ' ' + months[parseInt(m[2], 10) - 1] + ' ' + m[1];
  }

  fetch('news-by-juris/' + iso + '.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (data) {
      var rows = (data.rows || []).slice();
      rows.sort(function (a, b) {
        var da = a.date_published || '', db = b.date_published || '';
        if (da !== db) return db.localeCompare(da);            // newest first
        var pa = PRIORITY[a.story_type] || 0, pb = PRIORITY[b.story_type] || 0;
        if (pa !== pb) return pb - pa;                          // higher-priority type first
        return (a.title || '').localeCompare(b.title || '');    // alpha
      });
      var top5 = rows.slice(0, 5);

      // Hero rule: 0 leads → latest; 1 lead → it; 2+ leads → latest lead
      var leads = top5.filter(function (r) { return !!r.is_lead; });
      var hero = top5[0] || null;
      if (leads.length === 1) hero = leads[0];
      else if (leads.length >= 2) hero = leads[0]; // already-sorted leads keep date order

      var others = top5.filter(function (r) { return r !== hero; });
      var ordered = hero ? [hero].concat(others) : top5;

      // Update meta + see-all count
      var meta = document.querySelector('.nr-stream-head .meta');
      if (meta) {
        var d = new Date();
        var monthsShort = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var label = d.getDate() + ' ' + monthsShort[d.getMonth()];
        meta.textContent = 'Updated ' + label + ' · ' + (data.total || 0) + ' items';
      }
      var seeAll = document.querySelector('[data-pai-news-stream-seeall]');
      if (seeAll) seeAll.textContent = 'See all ' + (data.total || 0) + ' ' + window.PAI_JURIS + ' items →';

      // Render
      grid.innerHTML = ordered.map(function (r, i) {
        var isHero = (r === hero);
        var cls = 'nr-card' + (isHero ? ' hero-card' : '');
        var tag = r.is_lead ? 'Lead' : (r.story_type || 'Update');
        var slug = r.at2_id || r.id || '';
        var href = slug ? ('pai-app-news-story-' + slug) : '#';
        var summary = (r.summary || '');
        if (summary.length > 220) summary = summary.slice(0, 220) + '…';
        return '<a class="' + cls + '" href="' + escHtml(href) + '">'
          + '<div class="nr-meta"><span>' + escHtml(fmtDate(r.date_published)) + '</span>'
          +   '<span class="pill pill-source">' + escHtml(tag) + '</span></div>'
          + '<h3>' + escHtml(r.title || '') + '</h3>'
          + (summary ? '<p>' + escHtml(summary) + '</p>' : '')
          + '</a>';
      }).join('');
    })
    .catch(function () {
      // Silent: leave empty if fetch fails. Don't show stale placeholder.
      grid.innerHTML = '<div style="grid-column:1/-1;color:var(--text-mute);font-size:13px;padding:20px;text-align:center;">News will appear here as items are tracked.</div>';
    });
}
// Defer until DOMContentLoaded — juris pages set window.PAI_JURIS via an inline
// <script> tag that may appear AFTER this file's <script src=…> in the document.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', paiJurisNewsStreamRender);
} else {
  paiJurisNewsStreamRender();
}
