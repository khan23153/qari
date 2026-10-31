/*
 * Draws Madinah Mushaf pages from data/pages.json the way the Qari app does:
 * every word on its printed line, the ayah number as the KFGQPC medallion,
 * surah banners and basmala on the printed empty lines, tajweed colours on
 * the exact letters, and Hifz mode that hides words but keeps every marker.
 */
(function () {
  'use strict';

  // Light tajweed colours, mirrored from mobile/lib/core/constants/app_constants.dart.
  var LIGHT = {
    ham_wasl: '#607D8B', laam_shamsiyah: '#00897B', madda_normal: '#1B5E20',
    madda_permissible: '#2E7D32', madda_obligatory: '#1B5E20', madda_necessary: '#0B3D0B',
    slnt: '#558B2F', ghunnah: '#00838F', ikhafa: '#AD1457', ikhafa_shafawi: '#C2185B',
    qalaqah: '#37474F', idgham_ghunnah: '#7B1FA2', idgham_wo_ghunnah: '#8E24AA',
    idgham_shafawi: '#6A1B9A', idgham_mutajanisayn: '#9C27B0', iqlab: '#EF6C00'
  };

  // Night colours, mirrored from mushaf_reveal_view.dart (_nightTajweedColor).
  function nightColour(rule) {
    switch (rule) {
      case 'ghunnah': case 'qalaqah': return '#28B8D6';
      case 'ikhafa': case 'ikhafa_shafawi': return '#F063BD';
      case 'iqlab': return '#F4A45D';
      case 'idgham_ghunnah': case 'idgham_wo_ghunnah':
      case 'idgham_shafawi': case 'idgham_mutajanisayn': return '#BE7AE6';
      case 'ham_wasl': return '#AEB8B8';
      case 'normal': return null;
      default: return '#40C98C';
    }
  }

  function colourFor(rule, night) {
    if (rule === 'normal') return null;
    return night ? nightColour(rule) : (LIGHT[rule] || null);
  }

  // The bundled KFGQPC face draws U+06DF and U+06ED as large discs; the app
  // swaps in the small forms (same length, so tajweed offsets still line up).
  function display(word) {
    return word.replace(/۟/g, '۠').replace(/ۭ/g, 'ۢ');
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function fillWord(span, item, night) {
    var text = display(item.w);
    span.textContent = '';
    if (!item.s || !item.s.length) { span.textContent = text; return; }
    var ruleAt = new Array(text.length);
    item.s.forEach(function (s) {
      for (var i = Math.max(0, s[0]); i < Math.min(text.length, s[1]); i++) ruleAt[i] = s[2];
    });
    var start = 0;
    for (var i = 1; i <= text.length; i++) {
      if (i < text.length && ruleAt[i] === ruleAt[start]) continue;
      var run = text.slice(start, i);
      var colour = ruleAt[start] ? colourFor(ruleAt[start], night) : null;
      if (colour) {
        var r = el('span', 't', run);
        r.style.setProperty('--t', colour);
        span.appendChild(r);
      } else {
        span.appendChild(document.createTextNode(run));
      }
      start = i;
    }
  }

  /**
   * Builds a page into `root`. Returns a controller:
   *   set({theme, tajweed, hifz}), reveal() → bool, reset(), words (count)
   */
  function mount(root, page) {
    root.classList.add('mushaf');
    root.setAttribute('data-ui', '');
    if (page.opening) root.classList.add('is-opening');
    root.textContent = '';

    var sheet = el('div', 'mushaf-sheet');
    sheet.dir = 'rtl';
    sheet.lang = 'ar';
    sheet.style.setProperty('--lines', page.lineCount);
    var words = [];
    var byLine = {};
    page.lines.forEach(function (line) { byLine[line.n] = line; });

    for (var n = 1; n <= page.lineCount; n++) {
      var line = byLine[n];
      var row = el('div', 'm-line');
      if (!line) {
        row.classList.add('m-empty');
      } else if (line.type === 'header') {
        row.classList.add('m-header');
        row.appendChild(el('span', 'm-banner', 'سورة ' + line.name));
      } else if (line.type === 'basmala') {
        row.classList.add('m-basmala');
        row.appendChild(el('span', 'm-run', line.text));
      } else {
        row.classList.add('m-text');
        var run = el('span', 'm-run');
        line.items.forEach(function (item) {
          if (item.m) {
            var mk = el('span', 'mk', item.m);
            mk.title = 'Ayah ' + item.ref;
            run.appendChild(mk);
          } else {
            var w = el('span', 'w');
            w._item = item;
            words.push(w);
            run.appendChild(w);
          }
        });
        row.appendChild(run);
      }
      sheet.appendChild(row);
    }

    var foot = el('div', 'mushaf-foot', String(page.page));
    root.appendChild(sheet);
    root.appendChild(foot);

    var state = { theme: 'classic', tajweed: false, hifz: false, revealed: 0 };

    function paint() {
      var night = state.theme === 'night';
      root.setAttribute('data-theme', state.theme);
      words.forEach(function (w, i) {
        var hidden = state.hifz && i >= state.revealed;
        w.classList.toggle('is-hidden', hidden);
        // Tajweed never shows through a hidden word, as in the app.
        fillWord(w, state.tajweed && !hidden ? w._item : { w: w._item.w }, night);
      });
    }

    function fit() {
      var width = sheet.clientWidth;
      if (!width) return;
      // Measure every printed line at a reference size, then pick the size
      // at which the widest one fills the measure. Narrow lines are then
      // spread to the full width, the way the printed page justifies them.
      sheet.classList.add('is-measuring');
      sheet.style.setProperty('--fs', '100px');
      var widest = 0;
      sheet.querySelectorAll('.m-text .m-run, .m-basmala .m-run').forEach(function (r) {
        widest = Math.max(widest, r.getBoundingClientRect().width);
      });
      sheet.classList.remove('is-measuring');
      var pitch = sheet.clientHeight / page.lineCount;
      var size = widest ? 100 * width / widest : 0;
      // Opening pages centre a narrower block, as the printed pages do.
      size = page.opening ? Math.min(size * 0.82, pitch * 0.42) : Math.min(size * 0.985, pitch * 0.56);
      sheet.style.setProperty('--fs', size.toFixed(2) + 'px');
    }

    paint();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    if ('ResizeObserver' in window) new ResizeObserver(fit).observe(root);
    fit();

    return {
      words: words.length,
      get revealed() { return state.revealed; },
      set: function (patch) {
        for (var k in patch) state[k] = patch[k];
        paint();
      },
      reveal: function () {
        if (state.revealed >= words.length) return false;
        state.revealed += 1;
        paint();
        return true;
      },
      reset: function () { state.revealed = 0; paint(); },
      fit: fit
    };
  }

  var cache = null;
  function load(url) {
    if (!cache) cache = fetch(url || 'data/pages.json').then(function (r) {
      if (!r.ok) throw new Error('pages.json ' + r.status);
      return r.json();
    }).then(function (d) { return d.pages; });
    return cache;
  }

  window.QariMushaf = { mount: mount, load: load };
})();
