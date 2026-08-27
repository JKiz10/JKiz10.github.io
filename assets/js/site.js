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
