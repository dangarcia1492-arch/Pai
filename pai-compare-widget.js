/* PaiCompareWidget — shared comparison primitive
   Extracted from pai-app-tables-eu-regulation-tracker.html (commit b58e76af on mobile/burger-and-buttons).
   Owns: selection state, create-bar, custom-actions, frozen collapsed-summary banner, saved-searches panel,
         pin/chip click delegation, base64 share-link encode/decode, print trigger.
   Caller (page) owns: rendering of list items + 1-2-selected inline frozen rows (page-specific layout).
   API (window.PaiCompareWidget.init returns instance):
     getSelected() / has(slug) / add(slug) / remove(slug) / clear() / size()
     refreshUI()                          re-renders frozen bar + create bar + custom-actions + saved-searches
     getSavedSearches()
*/
(function(){
  'use strict';

  function PaiCompareWidget(config){
    var cfg = config || {};
    var storagePrefix = cfg.storagePrefix || 'paiCompare:default';
    var shareParam = cfg.shareParam || 'compare';
    var maxSavedSearches = cfg.maxSavedSearches || 2;

    // Element lookup with sensible defaults matching existing tracker markup
    var ids = Object.assign({
      createBar: 'createTrackerBar',
      count: 'ctbCount',
      name: 'ctbName',
      create: 'ctbCreate',
      save: 'ctbSave',
      clear: 'ctbClear',
      customActions: 'customActions',
      caName: 'caName',
      caPrint: 'caPrint',
      caShare: 'caShare',
      caRemove: 'caRemove',
      frozenBar: 'frozenBar',
      savedSearches: 'savedSearches',
      ssList: 'ssList',
      ssCap: 'ssCap'
    }, cfg.elements || {});

    var el = {};
    Object.keys(ids).forEach(function(k){ el[k] = document.getElementById(ids[k]); });

    var itemContainerId = cfg.itemContainer || 'matrix';
    var itemContainer = document.getElementById(itemContainerId);

    // Required hooks (no-op safe defaults)
    var getItemName = cfg.getItemName || function(slug){ return slug; };
    var getItemIso = cfg.getItemIso || function(slug){ return slug.slice(0,3).toUpperCase(); };
    var isCustomViewActive = cfg.isCustomViewActive || function(){ return false; };
    var activeCustomViewLabel = cfg.activeCustomViewLabel || function(){ return ''; };
    var sourceTabLabel = cfg.sourceTabLabel || function(){ return 'default'; };
    var onCreateView = cfg.onCreateView || function(){};
    var onRemoveActiveView = cfg.onRemoveActiveView || function(){};
    var onShareView = cfg.onShareView || function(){ return null; };
    var onLoadSharedView = cfg.onLoadSharedView || function(){};
    var onSelectionChange = cfg.onSelectionChange || function(){};

    // State
    var selected = new Set();
    var savedSearches = [];

    // Storage keys
    var LS_CUSTOM = storagePrefix + ':customViews';  // optional — page may handle its own
    var LS_SAVED  = storagePrefix + ':savedSearches';

    // ── Selection API ───────────────────────────────────────────────────
    function getSelected(){ return Array.from(selected); }
    function has(slug){ return selected.has(slug); }
    function size(){ return selected.size; }
    function add(slug){ selected.add(slug); refreshUI(); onSelectionChange(); }
    function remove(slug){ selected.delete(slug); refreshUI(); onSelectionChange(); }
    function clear(){ selected.clear(); refreshUI(); onSelectionChange(); }

    // ── Create-bar visibility ──────────────────────────────────────────
    function updateCreateBar(){
      if (!el.createBar) return;
      if (el.count) el.count.textContent = String(selected.size);
      el.createBar.hidden = (selected.size === 0);
    }

    // ── Custom-actions visibility ──────────────────────────────────────
    function updateCustomActions(){
      if (!el.customActions) return;
      if (isCustomViewActive()){
        el.customActions.hidden = false;
        if (el.caName) el.caName.textContent = activeCustomViewLabel();
      } else {
        el.customActions.hidden = true;
      }
    }

    // ── Frozen collapsed-summary banner (3+ selected, not in custom view) ─
    function renderFrozenBar(){
      if (!el.frozenBar) return;
      var inCustom = isCustomViewActive();
      if (inCustom || selected.size < 3){
        el.frozenBar.hidden = true;
        el.frozenBar.innerHTML = '';
        return;
      }
      el.frozenBar.hidden = false;
      var list = Array.from(selected).map(function(slug){
        return { slug: slug, name: getItemName(slug), iso: getItemIso(slug) };
      }).sort(function(a,b){ return a.name.localeCompare(b.name); });
      var initials = list.map(function(s){
        return '<button type="button" class="initial-chip" data-unpin="'+s.slug+
               '" title="Unpin '+s.name+'">'+s.iso+'<span class="chip-x">×</span></button>';
      }).join('');
      el.frozenBar.innerHTML =
        '<div class="frozen-summary">' +
          '<span class="fs-label"><span class="pin-glyph">📌</span> Pinned</span>' +
          '<span class="fs-count">'+list.length+' selected</span>' +
          '<span class="initials">'+initials+'</span>' +
          '<button class="fs-clear" id="fsClear">Clear all</button>' +
        '</div>';
      var fsClear = el.frozenBar.querySelector('#fsClear');
      if (fsClear) fsClear.addEventListener('click', function(){ clear(); });
      el.frozenBar.querySelectorAll('.initial-chip[data-unpin]').forEach(function(chip){
        chip.addEventListener('click', function(e){
          e.preventDefault();
          remove(chip.dataset.unpin);
        });
      });
    }

    // ── Saved-searches panel ───────────────────────────────────────────
    function loadSavedSearches(){
      try {
        var raw = localStorage.getItem(LS_SAVED);
        if (raw) savedSearches = JSON.parse(raw).slice(0, maxSavedSearches);
      } catch(e){ savedSearches = []; }
    }
    function persistSavedSearches(){
      try { localStorage.setItem(LS_SAVED, JSON.stringify(savedSearches)); } catch(e){}
    }
    function renderSavedSearches(){
      if (!el.savedSearches || !el.ssList) return;
      if (el.ssCap) el.ssCap.textContent = savedSearches.length + ' / ' + maxSavedSearches;
      if (savedSearches.length === 0){
        el.ssList.innerHTML = '<div class="ss-empty">Tick items + click <b>Save search</b> to pin a draft selection here.</div>';
        return;
      }
      el.ssList.innerHTML = savedSearches.map(function(s, i){
        return '<div class="ss-item">' +
          '<div class="ss-meta">' +
            '<div class="ss-name" title="'+s.name+'">'+s.name+'</div>' +
            '<div class="ss-count">'+s.states.length+' item'+(s.states.length===1?'':'s')+' · '+(s.sourceTab||'mixed')+'</div>' +
          '</div>' +
          '<button class="ss-load" data-load="'+i+'">Load</button>' +
          '<button class="ss-remove" data-remove="'+i+'" title="Remove">×</button>' +
        '</div>';
      }).join('');
    }
    function saveCurrentSearch(){
      if (selected.size === 0) return;
      var name = (el.name && el.name.value || '').trim() || ('Search ' + (savedSearches.length + 1));
      var entry = {
        name: name,
        states: Array.from(selected),
        sourceTab: sourceTabLabel(),
        ts: Date.now()
      };
      if (savedSearches.length >= maxSavedSearches){
        var ok = confirm('You have ' + maxSavedSearches + ' saved searches (max). Replace the oldest ("' + savedSearches[0].name + '")?');
        if (!ok) return;
        savedSearches.shift();
      }
      savedSearches.push(entry);
      persistSavedSearches();
      renderSavedSearches();
      if (el.name) el.name.value = '';
    }
    function loadSavedSearch(idx){
      var s = savedSearches[idx];
      if (!s) return;
      selected.clear();
      s.states.forEach(function(slug){ selected.add(slug); });
      if (s.name && el.name && !el.name.value) el.name.value = s.name;
      refreshUI();
      onSelectionChange();
    }
    function removeSavedSearch(idx){
      savedSearches.splice(idx, 1);
      persistSavedSearches();
      renderSavedSearches();
    }
    function getSavedSearches(){ return savedSearches.slice(); }

    // ── Share-URL encode/decode (base64 of {n, s, src}) ────────────────
    function buildShareUrl(){
      var payload = onShareView();
      if (!payload) return null;
      var enc = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
      var u = new URL(location.href);
      u.searchParams.set(shareParam, enc);
      return u.toString();
    }
    function parseShareUrl(){
      var enc = new URLSearchParams(location.search).get(shareParam);
      if (!enc) return;
      try {
        var payload = JSON.parse(decodeURIComponent(escape(atob(enc))));
        onLoadSharedView(payload);
      } catch(e){ /* ignore malformed share-URL */ }
    }

    // ── Click delegation on the item container ────────────────────────
    function wireItemContainer(){
      if (!itemContainer) return;
      itemContainer.addEventListener('click', function(e){
        var pinBtn = e.target.closest('.pin-btn[data-unpin]');
        if (pinBtn){
          e.preventDefault();
          e.stopPropagation();
          remove(pinBtn.dataset.unpin);
        }
      });
    }

    // ── Wire create-bar buttons ────────────────────────────────────────
    function wireCreateBar(){
      if (el.create){
        el.create.addEventListener('click', function(){
          var name = (el.name && el.name.value || '').trim() ||
                     ('Custom view ' + Date.now().toString(36).slice(-4));
          if (selected.size === 0) return;
          var slugs = Array.from(selected);
          var src = sourceTabLabel();
          onCreateView(name, slugs, src);
          selected.clear();
          if (el.name) el.name.value = '';
          refreshUI();
          onSelectionChange();
        });
      }
      if (el.save){
        el.save.addEventListener('click', saveCurrentSearch);
      }
      if (el.clear){
        el.clear.addEventListener('click', function(){
          selected.clear();
          if (el.name) el.name.value = '';
          refreshUI();
          onSelectionChange();
        });
      }
    }

    // ── Wire custom-actions buttons ────────────────────────────────────
    function wireCustomActions(){
      if (el.caPrint){
        el.caPrint.addEventListener('click', function(){ window.print(); });
      }
      if (el.caShare){
        el.caShare.addEventListener('click', async function(){
          var url = buildShareUrl();
          if (!url) return;
          var orig = el.caShare.textContent;
          try {
            await navigator.clipboard.writeText(url);
            el.caShare.textContent = 'Copied ✓';
            setTimeout(function(){ el.caShare.textContent = orig; }, 1500);
          } catch(e){
            prompt('Share URL:', url);
          }
        });
      }
      if (el.caRemove){
        el.caRemove.addEventListener('click', function(){
          if (!isCustomViewActive()) return;
          var lbl = activeCustomViewLabel();
          if (confirm('Remove "' + lbl + '"?')) onRemoveActiveView();
        });
      }
    }

    // ── Wire saved-searches list (load/remove delegation) ──────────────
    function wireSavedSearches(){
      if (!el.ssList) return;
      el.ssList.addEventListener('click', function(e){
        var t = e.target;
        if (t.dataset.load !== undefined) loadSavedSearch(+t.dataset.load);
        else if (t.dataset.remove !== undefined) removeSavedSearch(+t.dataset.remove);
      });
    }

    function refreshUI(){
      updateCreateBar();
      updateCustomActions();
      renderFrozenBar();
    }

    // ── Init sequence ──────────────────────────────────────────────────
    loadSavedSearches();
    wireItemContainer();
    wireCreateBar();
    wireCustomActions();
    wireSavedSearches();
    parseShareUrl();
    renderSavedSearches();
    refreshUI();

    // Expose instance API
    return {
      getSelected: getSelected,
      has: has,
      size: size,
      add: add,
      remove: remove,
      clear: clear,
      refreshUI: refreshUI,
      renderSavedSearches: renderSavedSearches,
      getSavedSearches: getSavedSearches,
      // For pages that want to feed a slug-set in without UI events
      setSelected: function(slugs){
        selected.clear();
        slugs.forEach(function(s){ selected.add(s); });
        refreshUI();
        onSelectionChange();
      }
    };
  }

  window.PaiCompareWidget = { init: PaiCompareWidget };
})();
