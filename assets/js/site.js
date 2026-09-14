/* Jennifer Kizzee Design - site behavior. Kept deliberately small. */
(function () {
  'use strict';

  // Mobile navigation
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.getAttribute('data-open') === 'true';
      nav.setAttribute('data-open', String(!open));
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.textContent = open ? 'Menu' : 'Close';
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.innerWidth <= 1000) {
        nav.setAttribute('data-open', 'false');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'Menu';
      }
    });
  }


  // --------------------------------------------------------------- stage ---
  // Slow cross-fade hero, built as progressive enhancement. Every frame is a
  // real <img> with a real src, so crawlers, link previews and AI readers see
  // all six photographs. Frame 1 is active in the HTML, so without JS the stage
  // is a still photograph. Frames 2+ are loading="lazy" and held out of layout
  // by CSS until arm(), which only runs once rotation starts after window load.
  // So they never compete with LCP, and anyone who prefers reduced motion never
  // downloads them unless they pick one.
  var stage = document.querySelector('.stage');
  if (stage) {
    var slides = [].slice.call(stage.querySelectorAll('.stage__slide'));
    var ticks  = [].slice.call(stage.querySelectorAll('.stage__tick'));
    var credit = stage.querySelector('.stage__credit');
    var calm   = window.matchMedia('(prefers-reduced-motion: reduce)');
    var HOLD = 7000;          // keep in step with the stage-hold keyframes in site.css
    var START_DELAY = 600;
    var i = 0, timer = null, loaded = false;

    function paint(n) {
      slides.forEach(function (s, k) { s.setAttribute('data-active', String(k === n)); });
      ticks.forEach(function (t, k) {
        if (k === n) t.setAttribute('aria-current', 'true');
        else t.removeAttribute('aria-current');
      });
      if (credit) {
        var name = document.createElement('b');
        name.textContent = slides[n].dataset.project || '';
        credit.textContent = '';
        credit.appendChild(name);
        credit.appendChild(document.createTextNode(slides[n].dataset.note || ''));
      }
      i = n;
    }

    // Puts frames 2+ into layout so the lazy loader fetches them. Idempotent.
    function arm() { stage.setAttribute('data-armed', 'true'); }

    // Moves to the next frame that has loaded. A frame still downloading holds
    // the current one for another beat; a frame that failed is skipped. Either
    // way the stage never fades to an empty box.
    function advance() {
      for (var k = 1; k < slides.length; k++) {
        var n = (i + k) % slides.length;
        var img = slides[n].querySelector('img');
        if (!img || (img.complete && img.naturalWidth > 0)) { paint(n); return; }
        if (!img.complete) return;
      }
    }

    function start() {
      if (!loaded || calm.matches || slides.length < 2) return;
      arm();
      stop();
      timer = setInterval(advance, HOLD);
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }

    ticks.forEach(function (t, k) {
      t.addEventListener('click', function () { arm(); paint(k); start(); });
    });
    stage.addEventListener('mouseenter', stop);
    stage.addEventListener('mouseleave', start);
    stage.addEventListener('focusin', stop);
    stage.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });
    if (calm.addEventListener) calm.addEventListener('change', function () { calm.matches ? stop() : start(); });

    // The HTML marks the opening frame so it shows without JS. Sync the tick and
    // credit to whichever frame that is, so the three can never disagree.
    slides.forEach(function (s, k) { if (s.getAttribute('data-active') === 'true') i = k; });
    paint(i);

    function begin() { loaded = true; setTimeout(start, START_DELAY); }
    if (document.readyState === 'complete') begin();
    else window.addEventListener('load', begin);
  }

  // ------------------------------------------------------- scroll reveal ---
  // Content ships visible. This only runs where IntersectionObserver exists and
  // motion is welcome, so nothing can ever be hidden by a failure here.
  var wants = document.querySelectorAll('[data-reveal]');
  if (wants.length && 'IntersectionObserver' in window
      && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.setAttribute('data-seen', 'true');
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
    [].forEach.call(wants, function (el) { el.classList.add('reveal'); io.observe(el); });
  }

  // Duplicate the marquee track so the loop is seamless
  var track = document.querySelector('.marquee__track');
  if (track && track.children.length === 1) {
    track.appendChild(track.firstElementChild.cloneNode(true));
  }

  // Consultation and phone click tracking hooks (Priority 14).
  // Wire these to your analytics provider once one is installed.
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var event = null;
    if (href.indexOf('tel:') === 0) event = 'phone_click';
    else if (href.indexOf('mailto:') === 0) event = 'email_click';
    else if (a.dataset.cta) event = 'cta_click';
    if (!event) return;
    var payload = { href: href, label: a.dataset.cta || a.textContent.trim() };

    // Custom hook first, if a page defines one.
    if (typeof window.jkdTrack === 'function') window.jkdTrack(event, payload);

    // Then whichever analytics provider is actually installed. Nothing is
    // installed yet, so these are no-ops until a GA4 or GTM snippet is added
    // to the page head. That is deliberate: the capture code should be in
    // place before the tag is, not after.
    if (typeof window.gtag === 'function') {
      window.gtag('event', event, { link_url: payload.href, link_label: payload.label });
    }
    if (Array.isArray(window.dataLayer)) {
      window.dataLayer.push({ event: event, link_url: payload.href, link_label: payload.label });
    }
  });
})();
