// nova-core.js — one brain client for the Chrome extension and the web app.
// Pure where it can be (tested in tests/nova-core.test.js). Works in a page, a service worker and Node.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.NovaCore = api;
})(typeof self !== 'undefined' ? self : this, function () {
  const API = 'https://opgitcuqwicuiplaptkm.supabase.co/functions/v1/notch-api';

  // ── safety ──
  /** Only http/https links. Returns a clean URL string or null. */
  function safeUrl(raw) {
    let s = String(raw || '').trim();
    if (!s || /\s/.test(s)) return null;
    if (!s.includes('://') && /^[a-z][a-z0-9+.-]*:(?![0-9])/i.test(s)) return null; // javascript:, mailto:, data:...
    if (!s.includes('://')) s = 'https://' + s;
    try {
      const u = new URL(s);
      if (u.protocol !== 'https:' && u.protocol !== 'http:') return null;
      if (!u.hostname) return null;
      return u.href;
    } catch { return null; }
  }
  /** The em dash law. */
  const noDashes = (s) => String(s || '').replace(/\s*[—–]\s*/g, ', ');
  const validDevice = (d) => /^[A-Za-z0-9-]{16,64}$/.test(String(d || ''));
  function newDeviceId() {
    const b = new Uint8Array(16);
    (globalThis.crypto || require('crypto').webcrypto).getRandomValues(b);
    return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
  }

  // ── commands answered on the device, no network ──
  const SITES = { youtube: 'youtube.com', gmail: 'mail.google.com', google: 'google.com', maps: 'maps.google.com', drive: 'drive.google.com',
    github: 'github.com', chatgpt: 'chatgpt.com', claude: 'claude.ai', netflix: 'netflix.com', amazon: 'amazon.ca', instagram: 'instagram.com',
    facebook: 'facebook.com', twitter: 'x.com', x: 'x.com', linkedin: 'linkedin.com', reddit: 'reddit.com', wikipedia: 'wikipedia.org',
    spotify: 'open.spotify.com', whatsapp: 'web.whatsapp.com', nova: 'nova.zeroorigine.com', calendar: 'calendar.google.com' };
  const tidy = (x) => x.replace(/\b(please|for me|now|nova)\b/g, '').replace(/\s+/g, ' ').trim();

  /** Returns {reply, actions:[{tool,args}]} or null when the brain is needed. Never runs anything itself. */
  function local(text, nowDate) {
    const low = String(text || '').toLowerCase().trim().replace(/[.!?]+$/, '');
    let m;
    if ((m = low.match(/(\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes)\b/)) && /timer|remind|countdown/.test(low)) {
      const n = Number(m[1]); return { reply: `Timer set for ${n} minute${n === 1 ? '' : 's'}.`, actions: [{ tool: 'timer', args: { minutes: n } }] };
    }
    if (/^(stop|cancel) (the )?timer$/.test(low)) return { reply: 'Timer stopped.', actions: [{ tool: 'stop_timer', args: {} }] };
    if (/^(what time is it|what's the time|time)$/.test(low)) {
      const d = nowDate || new Date();
      return { reply: 'It is ' + d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) + '.', actions: [] };
    }
    if ((m = low.match(/^(?:hey nova,?\s*)?(?:open|go to|launch|show me)\s+(.+)$/))) {
      const w = tidy(m[1]).replace(/^the\s+/, '').replace(/\s+(website|site|app)$/, '');
      const dom = /\./.test(w) && !/\s/.test(w) ? w : SITES[w] || (/^[a-z0-9-]+$/.test(w) ? w + '.com' : null);
      const url = dom && safeUrl(dom);
      if (url) return { reply: `Opening ${w}.`, actions: [{ tool: 'open_url', args: { url } }] };
    }
    if ((m = low.match(/^(?:play|watch)\s+(.+?)(?:\s+on youtube)?$/)) || (m = low.match(/^youtube\s+(.+)$/))) {
      const q = tidy(m[1]); return { reply: `Here's ${q} on YouTube.`, actions: [{ tool: 'youtube', args: { query: q } }] };
    }
    if ((m = low.match(/^(?:search(?: for| google for)?|google|look up)\s+(.+)$/))) {
      const q = tidy(m[1]); return { reply: `Searching for ${q}.`, actions: [{ tool: 'search_web', args: { query: q } }] };
    }
    if ((m = String(text || '').trim().match(/^remember(?: that)?\s+(.+)$/i))) {
      return { reply: "Got it. I'll remember.", actions: [{ tool: 'remember', args: { fact: m[1].replace(/[.!]+$/, '') } }] };
    }
    return null;
  }

  /** Turns an action into a URL to open (or null). Used by Chrome and the web app alike. */
  function urlFor(action) {
    const a = action.args || {};
    if (action.tool === 'open_url') return safeUrl(a.url);
    if (action.tool === 'search_web') return 'https://www.google.com/search?q=' + encodeURIComponent(String(a.query || ''));
    if (action.tool === 'youtube') return 'https://www.youtube.com/results?search_query=' + encodeURIComponent(String(a.query || ''));
    return null;
  }

  /** Chat turns [[who,text]] → API messages, alternating, starting with the user, last 14. */
  function toMessages(turns, text) {
    const msgs = [];
    for (const [who, said] of (turns || []).slice(-14)) {
      const role = who === 'you' ? 'user' : 'assistant';
      if (!msgs.length && role !== 'user') continue;
      if (msgs.length && msgs[msgs.length - 1].role === role) msgs[msgs.length - 1].content += '\n' + said;
      else msgs.push({ role, content: String(said).slice(0, 4000) });
    }
    if (text) {
      if (msgs.length && msgs[msgs.length - 1].role === 'user') msgs[msgs.length - 1].content += '\n' + text;
      else msgs.push({ role: 'user', content: String(text).slice(0, 4000) });
    }
    return msgs.slice(-14);
  }

  /** Ask Nova through notch-api. Always resolves to {reply, actions, refused?}. */
  async function ask({ client, device, turns, text, memory, tools, page, jwt, signal, fetchFn }) {
    const f = fetchFn || fetch;
    const headers = { 'content-type': 'application/json', 'x-notch-device': device };
    if (jwt) headers.authorization = 'Bearer ' + jwt;
    let r;
    try {
      r = await f(API + '/ask', { method: 'POST', signal, headers,
        body: JSON.stringify({ client, messages: toMessages(turns, text), memory: (memory || []).slice(-30), tools: tools || [], page: page || null, now: new Date().toString() }) });
    } catch (e) {
      if (e && e.name === 'AbortError') return { reply: '', actions: [], aborted: true };
      return { reply: '⚠︎ No internet. Try again.', actions: [], refused: true };
    }
    let j = {};
    try { j = await r.json(); } catch {}
    if (!r.ok) return { reply: '⚠︎ ' + (j.error || `Nova is busy right now (${r.status}). Try again.`), actions: [], refused: true, status: r.status };
    const actions = Array.isArray(j.actions) ? j.actions.filter((a) => a && typeof a.tool === 'string') : [];
    return { reply: noDashes(j.reply || '').trim() || (actions.length ? 'Done.' : ''), actions, signedIn: !!j.signed_in };
  }

  return { API, safeUrl, noDashes, validDevice, newDeviceId, local, urlFor, toMessages, ask, SITES };
});
