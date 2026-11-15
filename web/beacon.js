// ZeroOrigine beacon: one anonymous page_view per page load. No cookies, no personal data, no query strings.
(function () {
  try {
    const c = window.NOTCH_CONFIG; if (!c || navigator.webdriver) return;
    fetch(c.supabaseUrl + '/rest/v1/zo_product_metrics', {
      method: 'POST', keepalive: true,
      headers: { apikey: c.publishableKey, 'content-type': 'application/json', prefer: 'return=minimal' },
      body: JSON.stringify({ product_slug: c.slug, event: 'page_view', path: location.pathname.slice(0, 120), is_probe: false, source: 'browser' })
    }).catch(() => {});
  } catch (_) {}
})();
