(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- The live Mushaf page ---------- */
  var host = document.getElementById('live-page');
  var reveal = document.getElementById('reveal');
  var restart = document.getElementById('restart');
  var status = document.getElementById('reveal-status');
  var hifz = document.getElementById('hifz-toggle');
  var tajweed = document.getElementById('tajweed-toggle');

  function say(page) {
    if (!hifz.checked) { status.textContent = ''; return; }
    var n = page.revealed;
    status.textContent = n === page.words
      ? 'All ' + page.words + ' words recited. The page is whole again.'
      : n + ' of ' + page.words + ' words recited.';
    reveal.disabled = n === page.words;
  }

  if (host && window.QariMushaf) {
    window.QariMushaf.load('data/pages.json').then(function (pages) {
      var page = window.QariMushaf.mount(host, pages['1']);

      document.querySelectorAll('input[name="paper"]').forEach(function (input) {
        input.addEventListener('change', function () { page.set({ theme: input.value }); });
      });
      hifz.addEventListener('change', function () {
        page.set({ hifz: hifz.checked });
        reveal.disabled = false;
        say(page);
      });
      tajweed.addEventListener('change', function () { page.set({ tajweed: tajweed.checked }); });
      reveal.addEventListener('click', function () {
        // Revealing only makes sense on a hidden page: turn Hifz on first.
        if (!hifz.checked) { hifz.checked = true; page.set({ hifz: true }); }
        page.reveal();
        say(page);
      });
      restart.addEventListener('click', function () {
        page.reset();
        reveal.disabled = false;
        say(page);
      });
    }).catch(function () {
      host.textContent = 'The page could not be loaded.';
    });
  }

  /* ---------- Motion ---------- */
  if (reduce || !window.gsap) return;
  var gsap = window.gsap;
  if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);

  // Smooth scrolling, driven by GSAP's ticker so ScrollTrigger stays in step.
  if (window.Lenis && window.ScrollTrigger) {
    var lenis;
    // Find-in-page, the keyboard and scripts move the page natively. Before
    // Lenis handles a wheel turn, bring its target to where the page really
    // is, so the turn never jumps back to an old position.
    function resync() {
      if (lenis && !lenis.isScrolling && Math.abs(lenis.targetScroll - window.scrollY) > 1) {
        lenis.scrollTo(window.scrollY, { immediate: true, force: true });
      }
    }
    window.addEventListener('wheel', resync, { capture: true, passive: true });
    window.addEventListener('scroll', resync, { passive: true });
    lenis = new window.Lenis({ lerp: 0.12, smoothWheel: true });
    lenis.on('scroll', window.ScrollTrigger.update);
    gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
    gsap.ticker.lagSmoothing(0);
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var id = a.getAttribute('href');
        var target = id === '#top' ? 0 : document.querySelector(id);
        if (target === null) return;
        e.preventDefault();
        lenis.scrollTo(target, { offset: 0 });
        if (id !== '#top') {
          // Keep keyboard focus with the reader.
          if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
          target.focus({ preventScroll: true });
        }
      });
    });
  }

  // The signature move: the masthead page opens from the left edge like a
  // shutter while the picture settles; the name and the two statements follow.
  var shutter = document.querySelector('.tile-photo-a');
  var masthead = gsap.timeline({ defaults: { ease: 'expo.out' } });
  if (shutter) {
    var img = shutter.querySelector('img');
    masthead
      .fromTo(shutter, { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 1.1 }, 0.1)
      .fromTo(img, { scale: 1.12 }, { scale: 1.06, duration: 1.4 }, 0.1);
  }
  masthead
    .from('.tile-name h1', { yPercent: 40, opacity: 0, duration: 0.9 }, 0.25)
    .from('.tile-dark, .tile-gold', { y: 24, opacity: 0, duration: 0.8, stagger: 0.08 }, 0.45)
    .from('.tile-photo-b img', { opacity: 0, duration: 0.9, ease: 'power2.out' }, 0.5);

  if (!window.ScrollTrigger) return;

  // Section headings rise out of a mask, once, as each section arrives.
  document.querySelectorAll('main h2:not(.sr)').forEach(function (h) {
    var inner = document.createElement('span');
    inner.className = 'mask-line';
    while (h.firstChild) inner.appendChild(h.firstChild);
    var outer = document.createElement('span');
    outer.className = 'mask';
    outer.appendChild(inner);
    h.appendChild(outer);
    gsap.from(inner, {
      yPercent: 105, duration: 0.9, ease: 'expo.out',
      scrollTrigger: { trigger: h, start: 'top 88%', once: true }
    });
  });

  // Then the parts of each section, in reading order: text, then pictures.
  function enter(trigger, targets, opts) {
    var list = gsap.utils.toArray(targets);
    if (!list.length) return;
    gsap.from(list, Object.assign({
      y: 24, opacity: 0, duration: 0.8, ease: 'expo.out', stagger: 0.07,
      scrollTrigger: { trigger: trigger, start: 'top 82%', once: true }
    }, opts || {}));
  }
  enter('.band', '.panel', { y: 32, stagger: 0.08 });
  enter('.band-caption', '.band-caption');
  gsap.utils.toArray('.block').forEach(function (block) {
    enter(block, block.children);
  });
  enter('.library .axis-body', '.library .axis-body');
  enter('.grades', '.grades tr', { y: 16, stagger: 0.06 });
  enter('.hadith', '.hadith, .table-note');
  enter('.about-text', '.about-lead, .about-more, .facts li');
  enter('.strip', '.strip img', { y: 32 });
  enter('.cta-band', '.cta-line, .cta-small');
  enter('.footer-big', '.footer-big', { y: 32 });

  // One moving picture: the masthead page drifts as the board scrolls away.
  gsap.fromTo('.tile-photo-a img', { yPercent: -2.5 }, {
    yPercent: 2.5, ease: 'none', immediateRender: false,
    scrollTrigger: { trigger: '.board', start: 'top top', end: 'bottom top', scrub: true }
  });
})();
