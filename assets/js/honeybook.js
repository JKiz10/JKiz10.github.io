/* Jennifer's enquiry form is a HoneyBook placement, the same one her old site ran, so
   enquiries keep landing in the pipeline she already works from. HoneyBook's controller
   injects an iframe into a container it finds by class name, then resizes it.

   This file exists instead of an inline <script> so the Content-Security-Policy can stay
   on 'self' plus named hosts, with no 'unsafe-inline'.

   The form is someone else's code on someone else's server. Until its iframe is actually
   on the page, the visitor keeps a real way to reach the studio, and if it never arrives
   that way stays put. Nothing here ever reports success it has not seen. */
(function () {
  var mount = document.querySelector('[data-honeybook]');
  if (!mount) return;

  var pid = mount.getAttribute('data-honeybook');
  var fallback = document.querySelector('[data-honeybook-fallback]');
  if (!pid) return;

  window._HB_ = window._HB_ || {};
  window._HB_.pid = pid;

  var controller = document.createElement('script');
  controller.type = 'text/javascript';
  controller.async = true;
  controller.src = 'https://widget.honeybook.com/assets_users_production/websiteplacements/placement-controller.min.js';

  var settled = false;
  function settle(loaded) {
    if (settled) return;
    settled = true;
    mount.removeAttribute('data-loading');
    if (!fallback) return;
    if (loaded) fallback.hidden = true;             // the form is here, the fallback steps aside
    else fallback.setAttribute('data-only-way', 'true');  // it is not coming, so say so plainly
  }

  controller.addEventListener('error', function () { settle(false); });
  document.head.appendChild(controller);

  mount.setAttribute('data-loading', 'true');
  var giveUpAt = Date.now() + 9000;
  var poll = setInterval(function () {
    if (mount.querySelector('iframe')) {
      clearInterval(poll);
      settle(true);
    } else if (Date.now() > giveUpAt) {
      clearInterval(poll);
      settle(false);
    }
  }, 250);
})();
