/* pai-alerts.js — shared alerts module
 * Included on all logged-in pages. Renders bell counter + dropdown.
 * On news page, also wires the "Set alert for this view" button + modal.
 *
 * Storage keys:
 *   pai-alerts-v1   — array of {id, name, filters, frequency, createdAt}
 *   pai-last-visit  — ISO timestamp; used to compute "new since last visit"
 */
(function(){
  'use strict';

  var ALERTS_KEY = 'pai-alerts-v1';
  var VISIT_KEY  = 'pai-last-visit';

  // ============ Storage ============
  function loadAlerts(){
    try { return JSON.parse(localStorage.getItem(ALERTS_KEY) || '[]'); }
    catch(e){ return []; }
  }
  function saveAlerts(arr){
    try { localStorage.setItem(ALERTS_KEY, JSON.stringify(arr)); }
    catch(e){}
  }
  function getLastVisit(){
    try { return localStorage.getItem(VISIT_KEY) || new Date(0).toISOString(); }
    catch(e){ return new Date(0).toISOString(); }
  }
  function genId(){ return 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); }

  // ============ Filter helpers ============
  function filterStateToJSON(f){
    return {
      search:      f.search || '',
      regions:     Array.from(f.regions || []),
      juris:       Array.from(f.juris || []),
      types:       Array.from(f.types || []),
      authorities: Array.from(f.authorities || []),
      date:        f.date || 'all'
    };
  }
  function rowMatchesAlert(row, f){
    var j = row.jurisdiction_name || '';
    if (typeof newsCanonJur === 'function') j = newsCanonJur(row.jurisdiction_name);
    var d = (typeof jurData !== 'undefined' && jurData) ? jurData[j] : null;
    var region    = d ? d.region : '';
    var isUnattr  = !j;
    var effRegion = isUnattr ? '__unattributed__' : region;
    var effJuris  = isUnattr ? '__none__' : j;
    if ((f.regions.length || f.juris.length) &&
        f.regions.indexOf(effRegion) === -1 && f.juris.indexOf(effJuris) === -1) return false;
    if (f.types.length && f.types.indexOf(row.story_type) === -1) return false;
    if (f.authorities.length && f.authorities.indexOf(row.authority) === -1) return false;
    if (f.search){
      var q = f.search.toLowerCase();
      var hay = [(row.headline||''),(row.summary||''),(row.authority||''),(row.jurisdiction_name||'')].join(' ').toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }
    return true;
  }
  function deriveAlertName(f){
    var parts = [];
    if (f.regions.length)     parts.push(f.regions.join(' / '));
    if (f.juris.length)       parts.push(f.juris.slice(0,2).join(' / '));
    if (f.types.length)       parts.push(f.types.join(' / '));
    if (f.authorities.length) parts.push(f.authorities.slice(0,2).join(' / '));
    if (f.search)             parts.push('"' + f.search + '"');
    return parts.join(' · ') || 'All news';
  }
  function alertSummary(f){
    var bits = [];
    if (f.regions.length)     bits.push(f.regions.length + ' region' + (f.regions.length>1?'s':''));
    if (f.juris.length)       bits.push(f.juris.length + ' juris');
    if (f.types.length)       bits.push(f.types.join(', '));
    if (f.authorities.length) bits.push(f.authorities.length + ' authorit' + (f.authorities.length>1?'ies':'y'));
    if (f.search)             bits.push('search: "' + f.search + '"');
    return bits.join(' · ') || 'all news';
  }

  // ============ news.json (cached fetch) ============
  var _newsCache = null;
  function fetchNews(cb){
    if (_newsCache) { cb(_newsCache); return; }
    if (window.__newsAllRows) { _newsCache = window.__newsAllRows; cb(_newsCache); return; }
    fetch('news.json').then(function(r){ return r.json(); })
      .then(function(d){ _newsCache = d.rows || []; cb(_newsCache); })
      .catch(function(){ cb([]); });
  }
  function countNewForAlert(alert, rows, sinceISO){
    var n = 0;
    for (var i = 0; i < rows.length; i++){
      var r = rows[i];
      if (!r.date_published) continue;
      if (r.date_published <= sinceISO) continue;
      if (rowMatchesAlert(r, alert.filters)) n++;
    }
    return n;
  }

  // ============ Bell counter ============
  function renderBell(){
    var bell = document.querySelector('.pai-bell');
    if (!bell) return;
    var badge = bell.querySelector('.badge-count');
    var alerts = loadAlerts();
    if (!alerts.length){
      if (badge) badge.style.display = 'none';
      window.__paiAlerts = [];
      return;
    }
    fetchNews(function(rows){
      var since = getLastVisit();
      var total = 0;
      alerts.forEach(function(a){
        a._new = countNewForAlert(a, rows, since);
        total += a._new;
      });
      if (badge){
        if (total > 0){
          badge.textContent = total > 99 ? '99+' : String(total);
          badge.style.display = '';
        } else {
          badge.style.display = 'none';
        }
      }
      window.__paiAlerts = alerts;
    });
  }

  // ============ Bell dropdown ============
  function toggleDropdown(){
    var existing = document.getElementById('pai-alerts-dropdown');
    if (existing){ existing.remove(); return; }
    var bell = document.querySelector('.pai-bell');
    if (!bell) return;
    var rect = bell.getBoundingClientRect();
    var alerts = window.__paiAlerts || loadAlerts();

    var d = document.createElement('div');
    d.id = 'pai-alerts-dropdown';
    d.className = 'pai-alerts-dropdown';
    d.style.top = (rect.bottom + 8) + 'px';
    d.style.right = (window.innerWidth - rect.right) + 'px';

    var html = '';
    if (!alerts.length){
      html += '<div class="pad-empty">No alerts yet.<br><span class="hint">Create one from the News page filter panel.</span></div>';
      html += '<a class="pad-see-all" href="pai-app-alerts">Manage alerts →</a>';
    } else {
      var total = 0; alerts.forEach(function(a){ total += a._new || 0; });
      html += '<div class="pad-head">' + (total > 0
        ? (total + ' new item' + (total===1?'':'s') + ' across your alerts')
        : 'No new items since last visit') + '</div>';
      alerts.forEach(function(a){
        var n = a._new || 0;
        html += '<a class="pad-row" href="pai-app-news?alert=' + encodeURIComponent(a.id) + '">' +
                  '<span class="pad-name">' + escapeHtml(a.name) + '</span>' +
                  '<span class="pad-count' + (n > 0 ? ' has-new' : '') + '">' + (n > 0 ? '+' + n : '0') + '</span>' +
                '</a>';
      });
      html += '<a class="pad-see-all" href="pai-app-alerts">Manage alerts →</a>';
    }
    d.innerHTML = html;
    document.body.appendChild(d);

    setTimeout(function(){
      document.addEventListener('click', closeOnOutside, { once: true });
    }, 0);
  }
  function closeOnOutside(e){
    if (e.target.closest('.pai-alerts-dropdown') || e.target.closest('.pai-bell')) {
      document.addEventListener('click', closeOnOutside, { once: true });
      return;
    }
    var d = document.getElementById('pai-alerts-dropdown');
    if (d) d.remove();
  }

  function escapeHtml(s){
    s = String(s || '');
    return s.replace(/[&<>"']/g, function(c){
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
    });
  }

  // ============ Save-alert modal (news page only) ============
  function openSaveAlertModal(){
    var f = window.__newsFilters;
    if (!f){ showToast('Filters not loaded — reload the page.'); return; }
    var filterJSON = filterStateToJSON(f);
    var defaultName = deriveAlertName(filterJSON);

    var overlay = document.createElement('div');
    overlay.className = 'pai-alerts-modal-overlay';
    overlay.innerHTML =
      '<div class="pai-alerts-modal" role="dialog" aria-modal="true">' +
        '<div class="pam-head"><h3>Save this view as an alert</h3><button class="pam-close" type="button" aria-label="Close">&times;</button></div>' +
        '<div class="pam-body">' +
          '<label class="pam-field"><span class="pam-label">Name</span><input type="text" class="pam-input" id="pamName" value="' + escapeHtml(defaultName) + '" maxlength="80"></label>' +
          '<div class="pam-field"><span class="pam-label">What this alert tracks</span><div class="pam-summary">' + escapeHtml(alertSummary(filterJSON)) + '</div></div>' +
          '<div class="pam-field"><span class="pam-label">Notify me</span>' +
            '<label class="pam-radio"><input type="radio" name="pamFreq" value="immediate"><span>Immediately when something matches</span></label>' +
            '<label class="pam-radio"><input type="radio" name="pamFreq" value="daily" checked><span>Daily digest (one summary per day)</span></label>' +
            '<label class="pam-radio"><input type="radio" name="pamFreq" value="weekly"><span>Weekly digest</span></label>' +
          '</div>' +
        '</div>' +
        '<div class="pam-foot">' +
          '<button class="pam-btn pam-cancel" type="button">Cancel</button>' +
          '<button class="pam-btn pam-save" type="button">Save alert</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    setTimeout(function(){ overlay.classList.add('open'); }, 10);

    function close(){ overlay.classList.remove('open'); setTimeout(function(){ overlay.remove(); }, 200); }
    overlay.querySelector('.pam-close').onclick  = close;
    overlay.querySelector('.pam-cancel').onclick = close;
    overlay.addEventListener('click', function(e){ if (e.target === overlay) close(); });

    overlay.querySelector('.pam-save').onclick = function(){
      var name = (document.getElementById('pamName').value || '').trim() || defaultName;
      var freqEl = overlay.querySelector('input[name="pamFreq"]:checked');
      var freq = freqEl ? freqEl.value : 'daily';
      var alerts = loadAlerts();
      alerts.push({
        id: genId(),
        name: name,
        filters: filterJSON,
        frequency: freq,
        createdAt: new Date().toISOString()
      });
      saveAlerts(alerts);
      close();
      showToast('Alert saved · ' + name);
      renderBell();
    };
  }

  function showToast(msg){
    var t = document.createElement('div');
    t.className = 'pai-alerts-toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function(){ t.classList.add('show'); }, 10);
    setTimeout(function(){ t.classList.remove('show'); setTimeout(function(){ t.remove(); }, 300); }, 3000);
  }

  // ============ News-page Set-alerts button ============
  function setupNewsButton(){
    var clearBtn = document.querySelector('.facet-clear-all');
    if (!clearBtn) return;
    if (document.querySelector('.facet-set-alert')) return;
    var btn = document.createElement('button');
    btn.className = 'facet-set-alert';
    btn.type = 'button';
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="1.8" fill="none" style="vertical-align:-2px;margin-right:6px;">' +
        '<path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>' +
        '<path d="M13.73 21a2 2 0 01-3.46 0"/>' +
      '</svg>Set alert for this view';
    btn.onclick = openSaveAlertModal;
    clearBtn.insertAdjacentElement('afterend', btn);
  }

  // ============ ?alert=ID auto-apply ============
  function autoApplyAlertFromUrl(){
    var m = location.search.match(/[?&]alert=([^&]+)/);
    if (!m) return;
    var id = decodeURIComponent(m[1]);
    var alerts = loadAlerts();
    var a; for (var i=0;i<alerts.length;i++){ if (alerts[i].id === id){ a = alerts[i]; break; } }
    if (!a) return;
    var attempt = 0;
    var iv = setInterval(function(){
      attempt++;
      if (window.__newsFilters && typeof nfApply === 'function'){
        clearInterval(iv);
        var f = window.__newsFilters;
        f.search      = a.filters.search || '';
        f.regions     = new Set(a.filters.regions);
        f.juris       = new Set(a.filters.juris);
        f.types       = new Set(a.filters.types);
        f.authorities = new Set(a.filters.authorities);
        f.date        = a.filters.date || 'all';
        nfApply();
        history.replaceState(null, '', location.pathname);
        showToast('Alert applied: ' + a.name);
      } else if (attempt > 30){
        clearInterval(iv);
      }
    }, 100);
  }

  // ============ CSS ============
  function injectCSS(){
    var css =
      '.pai-bell { position: relative; cursor: pointer; }' +
      '.pai-bell .badge-count { display: none; }' +
      '.facet-set-alert { display: inline-flex; align-items: center; justify-content: center; width: 100%; height: 36px; background: rgba(1,118,211,0.08); border: 1px solid rgba(1,118,211,0.25); border-radius: 6px; font-size: 11.5px; font-weight: 600; color: var(--accent-2, #014486); cursor: pointer; margin-top: 6px; letter-spacing: .02em; font-family: inherit; }' +
      '.facet-set-alert:hover { background: rgba(1,118,211,0.14); }' +
      '.pai-alerts-dropdown { position: fixed; z-index: 9000; min-width: 280px; max-width: 360px; background: var(--surface, #fff); border: 1px solid var(--border, #d9dee6); border-radius: 8px; box-shadow: 0 8px 24px rgba(10,23,41,0.16); padding: 8px 0; font-family: "Inter", sans-serif; }' +
      '.pai-alerts-dropdown .pad-head { font-size: 11.5px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted, #6b7a8f); padding: 6px 14px 8px; border-bottom: 1px solid var(--border-soft, #e5e9f0); }' +
      '.pai-alerts-dropdown .pad-empty { padding: 18px 16px; text-align: center; font-size: 13px; color: var(--secondary, #4a556b); }' +
      '.pai-alerts-dropdown .pad-empty .hint { display: block; margin-top: 6px; font-size: 11.5px; color: var(--muted, #8a93a3); }' +
      '.pai-alerts-dropdown .pad-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; text-decoration: none; color: inherit; border-bottom: 1px solid var(--border-soft, #f0f3f7); }' +
      '.pai-alerts-dropdown .pad-row:last-of-type { border-bottom: none; }' +
      '.pai-alerts-dropdown .pad-row:hover { background: var(--surface-3, #f6f8fa); }' +
      '.pai-alerts-dropdown .pad-name { font-size: 13px; color: var(--ink, #07202e); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-right: 10px; }' +
      '.pai-alerts-dropdown .pad-count { font-size: 11px; font-family: var(--mono, ui-monospace); font-weight: 600; padding: 2px 8px; border-radius: 9px; background: var(--surface-3, #f0f3f7); color: var(--muted, #6b7a8f); }' +
      '.pai-alerts-dropdown .pad-count.has-new { background: var(--red-fill, #e23131); color: #fff; }' +
      '.pai-alerts-dropdown .pad-see-all { display: block; padding: 10px 14px; font-size: 12px; font-weight: 600; color: var(--accent-2, #014486); text-decoration: none; border-top: 1px solid var(--border-soft, #e5e9f0); }' +
      '.pai-alerts-dropdown .pad-see-all:hover { background: var(--surface-3, #f6f8fa); }' +
      '.pai-alerts-modal-overlay { position: fixed; inset: 0; z-index: 9500; background: rgba(6,16,30,0.42); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.2s; }' +
      '.pai-alerts-modal-overlay.open { opacity: 1; }' +
      '.pai-alerts-modal { background: var(--surface, #fff); border-radius: 10px; box-shadow: 0 16px 48px rgba(10,23,41,0.24); width: 480px; max-width: calc(100vw - 32px); font-family: "Inter", sans-serif; overflow: hidden; }' +
      '.pai-alerts-modal .pam-head { display: flex; align-items: center; justify-content: space-between; padding: 18px 22px 14px; border-bottom: 1px solid var(--border-soft, #e5e9f0); }' +
      '.pai-alerts-modal .pam-head h3 { margin: 0; font-size: 15px; font-weight: 600; color: var(--ink, #07202e); }' +
      '.pai-alerts-modal .pam-close { background: none; border: none; cursor: pointer; font-size: 22px; color: var(--muted, #6b7a8f); line-height: 1; padding: 0; }' +
      '.pai-alerts-modal .pam-body { padding: 18px 22px; }' +
      '.pai-alerts-modal .pam-field { display: block; margin-bottom: 16px; }' +
      '.pai-alerts-modal .pam-label { display: block; font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted, #6b7a8f); margin-bottom: 6px; }' +
      '.pai-alerts-modal .pam-input { width: 100%; padding: 8px 10px; border: 1px solid var(--border, #d9dee6); border-radius: 5px; font-size: 13.5px; font-family: inherit; box-sizing: border-box; }' +
      '.pai-alerts-modal .pam-input:focus { outline: none; border-color: var(--accent, #0176d3); }' +
      '.pai-alerts-modal .pam-summary { font-size: 13px; color: var(--secondary, #4a556b); padding: 6px 0; }' +
      '.pai-alerts-modal .pam-radio { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 13.5px; color: var(--ink, #07202e); cursor: pointer; }' +
      '.pai-alerts-modal .pam-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 14px 22px; background: var(--surface-2, #f9fafb); border-top: 1px solid var(--border-soft, #e5e9f0); }' +
      '.pai-alerts-modal .pam-btn { padding: 8px 16px; border-radius: 5px; font-size: 13px; font-weight: 600; font-family: inherit; cursor: pointer; border: 1px solid transparent; }' +
      '.pai-alerts-modal .pam-cancel { background: transparent; color: var(--secondary, #4a556b); border-color: var(--border, #d9dee6); }' +
      '.pai-alerts-modal .pam-cancel:hover { background: var(--surface-3, #f0f3f7); }' +
      '.pai-alerts-modal .pam-save { background: var(--accent, #0176d3); color: #fff; }' +
      '.pai-alerts-modal .pam-save:hover { background: var(--accent-2, #014486); }' +
      '.pai-alerts-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(20px); background: var(--ink, #07202e); color: #fff; padding: 10px 18px; border-radius: 6px; font-size: 13px; font-family: "Inter", sans-serif; z-index: 9700; opacity: 0; transition: opacity 0.25s, transform 0.25s; box-shadow: 0 4px 16px rgba(0,0,0,0.24); }' +
      '.pai-alerts-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }';
    var s = document.createElement('style');
    s.textContent = css;
    document.head.appendChild(s);
  }

  // ============ Init ============
  function init(){
    injectCSS();
    setupNewsButton();
    renderBell();
    var bell = document.querySelector('.pai-bell');
    if (bell) bell.addEventListener('click', function(e){ e.preventDefault(); toggleDropdown(); });
    autoApplyAlertFromUrl();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  // Debug surface
  window.paiAlerts = { load: loadAlerts, save: saveAlerts, render: renderBell, open: openSaveAlertModal };
})();
