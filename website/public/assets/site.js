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
  var idle = status ? status.textContent : '';

  function say(page) {
    if (!hifz.checked) { status.textContent = idle; reveal.disabled = false; return; }
    var n = page.revealed;
    status.textContent = n === page.words
      ? 'All ' + page.words + ' words recited. The page is whole again.'
      : n === 0
        ? 'The words are hidden. Press Reveal next word to recite.'
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
        say(page);
      });
    }).catch(function () {
      host.textContent = 'The page could not be loaded.';
    });
  }

  /* ---------- Motion ---------- */
  if (reduce || !window.gsap) return;
  var gsap = window.gsap;

  // Smooth scrolling, driven by GSAP's ticker so ScrollTrigger stays in step.
  if (window.Lenis && window.ScrollTrigger) {
    gsap.registerPlugin(window.ScrollTrigger);
    var lenis;
    // Find-in-page, the keyboard and scripts move the page natively. Before
    // Lenis handles a wheel turn, bring its target to where the page really
    // is, so the turn never jumps back to an old position.
    var resync = function () {
      if (lenis && !lenis.isScrolling && Math.abs(lenis.targetScroll - window.scrollY) > 1) {
        lenis.scrollTo(window.scrollY, { immediate: true, force: true });
      }
    };
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
        lenis.scrollTo(target, { offset: id === '#top' ? 0 : -72 });
        if (id !== '#top') {
          if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
          target.focus({ preventScroll: true });
        }
      });
    });
  }

  // On load: the words settle in, then the three pages rise into place.
  gsap.timeline({ defaults: { ease: 'expo.out' } })
    .from('.basmala, .hero h1, .hero-sub, .hero-actions, .hero-note', { y: 18, opacity: 0, duration: 0.9, stagger: 0.08 }, 0.05)
    .from('.hp-main', { y: 80, opacity: 0, duration: 1.2 }, 0.35)
    .from('.hp-left', { y: 90, opacity: 0, rotate: 0, duration: 1.2 }, 0.5)
    .from('.hp-right', { y: 90, opacity: 0, rotate: 0, duration: 1.2 }, 0.5);

  if (!window.ScrollTrigger) return;
  gsap.registerPlugin(window.ScrollTrigger);

  // Each section's parts appear once, in reading order.
  function enter(trigger, targets, opts) {
    var list = gsap.utils.toArray(targets);
    if (!list.length) return;
    gsap.from(list, Object.assign({
      y: 22, opacity: 0, duration: 0.8, ease: 'expo.out', stagger: 0.07,
      scrollTrigger: { trigger: trigger, start: 'top 82%', once: true }
    }, opts || {}));
  }
  enter('.features', '.features .ornament, .features h2, .features .section-sub');
  enter('.cards', '.card', { stagger: 0.06 });
  enter('.hifz', '.hifz-text > *, .frame');
  enter('.library', '.library .ornament, .library h2, .library .section-sub');
  enter('.hadith-card', '.hadith-card', { y: 30 });
  enter('.chain', '.chain li', { y: 12, stagger: 0.07 });
  enter('.learn', '.learn-text > *, .tracks li');
  enter('.cta-card', '.cta-card > *');
})();
