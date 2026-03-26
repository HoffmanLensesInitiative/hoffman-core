// Hoffman Lenses - Overlay Renderer v0.2.2
// Annotates flagged text blocks on any page.
// Session bar with flag navigator at bottom of screen.

(function() {

  // Registry of all annotation boxes in page order
  var annotations = [];
  var currentIndex = -1;

  // -- Escape HTML ------------------------------------------
  function esc(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // -- Session bar ------------------------------------------
  function createBar() {
    if (document.getElementById('hl-bar')) return;
    var bar = document.createElement('div');
    bar.id = 'hl-bar';
    bar.innerHTML =
      '<div class="hl-bar-inner">' +
        '<span class="hl-bar-logo">o HOFFMAN LENSES</span>' +
        '<div class="hl-bar-stats">' +
          '<span class="hl-bar-stat"><span class="hl-bar-label">Scanned</span><span class="hl-bar-val" id="hl-scanned">0</span></span>' +
          '<span class="hl-bar-sep"></span>' +
          '<span class="hl-bar-stat"><span class="hl-bar-label">Flagged blocks</span><span class="hl-bar-val hl-danger hl-clickable" id="hl-flagged" title="Click to navigate flags">0</span></span>' +
          '<span class="hl-bar-sep"></span>' +
          '<span class="hl-bar-stat"><span class="hl-bar-label">Escalation</span><span class="hl-bar-val" id="hl-escalation">--</span></span>' +
          '<span class="hl-bar-sep"></span>' +
          '<span class="hl-bar-stat"><span class="hl-bar-label">Site</span><span class="hl-bar-val hl-muted" id="hl-site">' + location.hostname + '</span></span>' +
        '</div>' +
        '<button class="hl-bar-btn" id="hl-toggle">ON</button>' +
      '</div>';
    document.body.appendChild(bar);

    // Toggle button
    document.getElementById('hl-toggle').addEventListener('click', function() {
      var btn = document.getElementById('hl-toggle');
      var isOn = btn.textContent === 'ON';
      btn.textContent = isOn ? 'OFF' : 'ON';
      btn.classList.toggle('hl-off', isOn);
      document.querySelectorAll('.hl-annotation').forEach(function(el) {
        el.style.display = isOn ? 'none' : '';
      });
      try { chrome.runtime.sendMessage({ type: 'TOGGLE', data: { active: !isOn } }); } catch(e) {}
    });

    // Flagged count -- click to open navigator
    document.getElementById('hl-flagged').addEventListener('click', function() {
      toggleNavigator();
    });
  }

  // -- Flag navigator ---------------------------------------
  function toggleNavigator() {
    var existing = document.getElementById('hl-navigator');
    if (existing) {
      existing.remove();
      currentIndex = -1;
      return;
    }
    if (annotations.length === 0) return;
    createNavigator();
    navigateTo(0);
  }

  function createNavigator() {
    var nav = document.createElement('div');
    nav.id = 'hl-navigator';
    nav.innerHTML =
      '<div class="hl-nav-inner">' +
        '<span class="hl-nav-label">FLAG NAVIGATOR</span>' +
        '<span class="hl-nav-counter"><span id="hl-nav-current">1</span> of <span id="hl-nav-total">' + annotations.length + '</span></span>' +
        '<div class="hl-nav-controls">' +
          '<button class="hl-nav-btn" id="hl-nav-prev" title="Previous flag">&#8593;</button>' +
          '<button class="hl-nav-btn" id="hl-nav-next" title="Next flag">&#8595;</button>' +
          '<button class="hl-nav-close" id="hl-nav-close" title="Close navigator">&#10005;</button>' +
        '</div>' +
        '<div class="hl-nav-preview" id="hl-nav-preview"></div>' +
      '</div>';
    document.body.appendChild(nav);

    document.getElementById('hl-nav-prev').addEventListener('click', function() {
      navigateTo(currentIndex - 1);
    });
    document.getElementById('hl-nav-next').addEventListener('click', function() {
      navigateTo(currentIndex + 1);
    });
    document.getElementById('hl-nav-close').addEventListener('click', function() {
      nav.remove();
      clearHighlight();
      currentIndex = -1;
    });
  }

  function navigateTo(index) {
    if (annotations.length === 0) return;

    // Wrap around
    if (index < 0) index = annotations.length - 1;
    if (index >= annotations.length) index = 0;
    currentIndex = index;

    var target = annotations[currentIndex];
    if (!target) return;

    // Clear previous highlight
    clearHighlight();

    // Highlight current annotation
    target.classList.add('hl-annotation-active');

    // Scroll to it -- offset to account for bottom bar
    var rect = target.getBoundingClientRect();
    var scrollTop = window.pageYOffset + rect.top - (window.innerHeight / 2) + (rect.height / 2);
    window.scrollTo({ top: scrollTop, behavior: 'smooth' });

    // Update counter
    var counter = document.getElementById('hl-nav-current');
    if (counter) counter.textContent = currentIndex + 1;

    // Update preview -- show first flag label and snippet
    var preview = document.getElementById('hl-nav-preview');
    if (preview) {
      var label = target.querySelector('.hl-flag-label');
      var flagCount = target.querySelectorAll('.hl-flag').length;
      var labelText = label ? label.textContent : 'Flag detected';
      preview.innerHTML =
        '<span class="hl-nav-flag-label">' + esc(labelText) + '</span>' +
        (flagCount > 1 ? '<span class="hl-nav-more"> +' + (flagCount - 1) + ' more</span>' : '');
    }
  }

  function clearHighlight() {
    document.querySelectorAll('.hl-annotation-active').forEach(function(el) {
      el.classList.remove('hl-annotation-active');
    });
  }

  // -- Update bar stats -------------------------------------
  function updateBar(response) {
    if (!response || !response.session) return;
    var s = response.session;
    var scanned = document.getElementById('hl-scanned');
    var flagged = document.getElementById('hl-flagged');
    var esc_el  = document.getElementById('hl-escalation');
    if (scanned) scanned.textContent = s.blocksScanned || 0;
    if (flagged) {
      var count = s.blocksFlagged || 0;
      flagged.textContent = count;
      flagged.className = 'hl-bar-val hl-clickable ' + (count > 0 ? 'hl-danger' : 'hl-good');
      // Update navigator total if open
      var navTotal = document.getElementById('hl-nav-total');
      if (navTotal) navTotal.textContent = annotations.length;
    }
    if (esc_el) {
      var level = response.escalationLevel || 'low';
      esc_el.textContent = level.toUpperCase() + ' (' + (s.escalationScore || 0) + ')';
      esc_el.className = 'hl-bar-val hl-' + (level === 'low' ? 'good' : level === 'medium' ? 'warn' : 'danger');
    }
  }

  // -- Annotate a flagged block -----------------------------
  function annotate(el, result) {
    if (el.querySelector('.hl-annotation')) return;

    var hasDanger = result.patterns.some(function(p) { return p.severity === 'danger'; });
    var hasWarn   = result.patterns.some(function(p) { return p.severity === 'warn'; });
    var sev = hasDanger ? 'danger' : hasWarn ? 'warn' : 'info';

    var flagsHtml = result.patterns.map(function(p) {
      var conf = p.confidence < 0.9
        ? ' <span class="hl-conf">(' + Math.round(p.confidence * 100) + '%)</span>'
        : '';
      return '<div class="hl-flag hl-flag-' + p.severity + '">' +
        '<div class="hl-dot hl-dot-' + p.severity + '"></div>' +
        '<div class="hl-flag-text">' +
          '<div class="hl-flag-label">' + esc(p.label) + conf + '</div>' +
          '<div class="hl-flag-explanation">' + esc(p.explanation) + '</div>' +
        '</div>' +
      '</div>';
    }).join('');

    var box = document.createElement('div');
    box.className = 'hl-annotation hl-annotation-' + sev;
    box.innerHTML =
      '<div class="hl-annotation-header">' +
        '<span class="hl-annotation-logo">o HOFFMAN LENSES</span>' +
        '<span class="hl-annotation-count">' +
          result.patternCount + ' flag' + (result.patternCount > 1 ? 's' : '') + ' on this block' +
        '</span>' +
      '</div>' +
      '<div class="hl-flags">' + flagsHtml + '</div>';

    if (el.parentNode) {
      el.parentNode.insertBefore(box, el.nextSibling);
    }

    el.classList.add('hl-flagged', 'hl-flagged-' + sev);

    // Register in navigator list
    annotations.push(box);

    // Update navigator total if open
    var navTotal = document.getElementById('hl-nav-total');
    if (navTotal) navTotal.textContent = annotations.length;
  }

  // -- Init -------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createBar);
  } else {
    createBar();
  }

  window.HLOverlay = { annotate: annotate, updateBar: updateBar };
  console.log('[Hoffman Lenses] overlay.js ready');

})();
