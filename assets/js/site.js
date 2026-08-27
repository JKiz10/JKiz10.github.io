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
  // Slow cross-fade hero. Progressive enhancement: slide 1 is real HTML with a
  // real src, so without JS you get a still photograph and nothing is broken.
  // Slides 2+ carry data-src and are only fetched AFTER window load, so the
  // carousel never competes with LCP. Honours prefers-reduced-motion by simply
  // not rotating.
  var stage = document.querySelector('.stage');
  if (stage) {
    var slides = [].slice.call(stage.querySelectorAll('.stage__slide'));
    var ticks  = [].slice.call(stage.querySelectorAll('.stage__tick'));
    var credit = stage.querySelector('.stage__credit');
    var calm   = window.matchMedia('(prefers-reduced-motion: reduce)');
    var HOLD   = 7000;
    var i = 0, timer = null, loaded = false;

    function paint(n) {
      slides.forEach(function (s, k) { s.setAttribute('data-active', String(k === n)); });
      ticks.forEach(function (t, k) {
        if (k === n) t.setAttribute('aria-current', 'true');
        else t.removeAttribute('aria-current');
      });
      if (credit) {
        var s = slides[n];
        credit.innerHTML = '<b>' + (s.dataset.project || '') + '</b>' + (s.dataset.note || '');
      }
      i = n;
    }

    // Pull in the remaining frames only once the page has settled.
    function hydrate() {
      if (loaded) return;
      loaded = true;
      slides.forEach(function (s, k) {
        if (k === 0) return;
        var img = s.querySelector('img');
        if (img && img.dataset.src) {
          if (img.dataset.srcset) img.srcset = img.dataset.srcset;
          img.src = img.dataset.src;
        }
      });
    }

    function advance() { paint((i + 1) % slides.length); }
    function start() { if (!calm.matches && slides.length > 1) { stop(); timer = setInterval(advance, HOLD); } }
    function stop()  { if (timer) { clearInterval(timer); timer = null; } }

    ticks.forEach(function (t, k) {
      t.addEventListener('click', function () { hydrate(); paint(k); start(); });
    });
    stage.addEventListener('mouseenter', stop);
    stage.addEventListener('mouseleave', start);
    stage.addEventListener('focusin', stop);
    stage.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });

    paint(0);
    if (window.requestIdleCallback) requestIdleCallback(hydrate, { timeout: 2500 });
    else setTimeout(hydrate, 1200);
    window.addEventListener('load', function () { hydrate(); setTimeout(start, 600); });
    if (calm.addEventListener) calm.addEventListener('change', function () { calm.matches ? stop() : start(); });
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
