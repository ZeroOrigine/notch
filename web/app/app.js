
const $ = (id) => document.getElementById(id);
const S = {
  mode: 'idle', chatting: false, banner: null,
  voice: localStorage.getItem('voice') !== 'off',
  turns: JSON.parse(localStorage.getItem('turns') || '[]'),
  memory: JSON.parse(localStorage.getItem('memory') || '[]'),
  timerEnd: Number(localStorage.getItem('timerEnd')) || null
};
const save = () => { localStorage.setItem('turns', JSON.stringify(S.turns.slice(-200))); localStorage.setItem('memory', JSON.stringify(S.memory.slice(-60))); };

// ---------- drawing ----------
const fmt = (ms) => { const s = Math.max(0, Math.round(ms / 1000)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
let skyT = 0;
function loop(now) {
  const t = now / 1000, busy = S.mode === 'thinking' || S.mode === 'speaking';
  NovaArt.star($('big'), t, busy);
  NovaArt.star($('mini'), t, busy);
  if (now - skyT > 33) { NovaArt.stars($('sky'), t); skyT = now; }
  const live = S.timerEnd && S.timerEnd > Date.now();
  if (S.timerEnd && !live) { S.timerEnd = null; localStorage.removeItem('timerEnd'); ding(); say('Your timer is done.'); }
  const r = $('right');
  const want = S.mode === 'listening' ? 'L' : S.mode === 'speaking' ? 'S' : S.mode === 'thinking' ? 'T' : live ? 'C' : '';
  if (want === 'L' && r.dataset.k !== 'L') r.innerHTML = '<span class="eq red"><i></i><i></i><i></i><i></i></span>';
  if (want === 'S' && r.dataset.k !== 'S') r.innerHTML = '<span class="eq"><i></i><i></i><i></i><i></i></span>';
  if (want === 'T') r.textContent = 'Thinking';
  if (want === 'C') r.textContent = '⏱ ' + fmt(S.timerEnd - Date.now());
  if (want === '') r.textContent = '';
  r.dataset.k = want;
  $('tbig').style.display = live ? 'block' : 'none'; if (live) $('tbig').textContent = fmt(S.timerEnd - Date.now());
  const isl = $('isl');
  isl.classList.toggle('wide', !S.banner && (S.mode !== 'idle' || live));
  isl.classList.toggle('glow2', busy);
  $('title').textContent = { listening: 'Listening…', thinking: 'Thinking…', speaking: 'Nova' }[S.mode] || "Hi, I'm Nova";
  requestAnimationFrame(loop);
}
let bannerT;
function banner(text, sec = 4) {
  S.banner = text; $('btext').textContent = text; $('isl').classList.add('big');
  clearTimeout(bannerT); bannerT = setTimeout(() => { S.banner = null; $('isl').classList.remove('big'); }, sec * 1000);
}
$('isl').onclick = () => { const last = [...S.turns].reverse().find(x => x[0] === 'nova'); if (S.banner) { S.banner = null; $('isl').classList.remove('big'); } else if (last) banner(last[1], 6); };

// ---------- chat list ----------
function render() {
  const c = $('chat'); c.innerHTML = '';
  if (!S.turns.length) { c.innerHTML = '<div class="empty">Ask me anything.<br>Try “set a 5 minute timer” or “open youtube”.</div>'; return; }
  for (const [who, text] of S.turns.slice(-80)) { const d = document.createElement('div'); d.className = 'msg ' + (who === 'you' ? 'you' : 'nova'); d.textContent = text; c.appendChild(d); }
  c.scrollTop = c.scrollHeight;
}
function add(who, text) { S.turns.push([who, text]); save(); render(); }

// ---------- sound and speech ----------
let actx;
function ding() { try { actx = actx || new (window.AudioContext || window.webkitAudioContext)(); const o = actx.createOscillator(), g = actx.createGain(); o.frequency.value = 880; g.gain.setValueAtTime(.2, actx.currentTime); g.gain.exponentialRampToValueAtTime(.001, actx.currentTime + .8); o.connect(g).connect(actx.destination); o.start(); o.stop(actx.currentTime + .8); } catch {} }
function setMode(m) { S.mode = m; $('stop').style.display = (m !== 'idle' || S.chatting) ? 'flex' : 'none'; }
function speak(text) {
  if (!S.voice || text.startsWith('⚠︎') || !('speechSynthesis' in window)) { setMode('idle'); afterSpeech(); return; }
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  const vs = speechSynthesis.getVoices();
  const v = vs.find(v => /en-GB/.test(v.lang) && /Serena|Kate|Martha|Female|Stephanie/i.test(v.name)) || vs.find(v => /en-GB/.test(v.lang));
  if (v) u.voice = v;
  u.onstart = () => setMode('speaking');
  u.onend = u.onerror = () => { setMode('idle'); afterSpeech(); };
  setMode('speaking');
  speechSynthesis.speak(u);
}
function afterSpeech() { if (S.chatting) setTimeout(() => { if (S.chatting && S.mode === 'idle') listen(); }, 400); }
function say(text) { add('nova', text); banner(text); speak(text); }

// ---------- Nova brain (ZeroOrigine notch-api, shared core in /nova-core.js) ----------
const N = window.NovaCore;
const TOOLS = ['open_url', 'search_web', 'youtube', 'timer', 'remember', 'forget'];
let device = localStorage.getItem('notchDevice');
if (!N.validDevice(device)) { device = N.newDeviceId(); localStorage.setItem('notchDevice', device); }
const go = (u) => { const safe = N.safeUrl(u); if (safe) window.open(safe, '_blank', 'noopener'); };
function startTimer(min) { S.timerEnd = Date.now() + Math.min(1440, Math.max(.1, Number(min) || 1)) * 60000; localStorage.setItem('timerEnd', S.timerEnd); }
function run(action) {
  const url = N.urlFor(action); if (url) { go(url); return; }
  const a = action.args || {};
  if (action.tool === 'timer') startTimer(a.minutes);
  if (action.tool === 'stop_timer') { S.timerEnd = null; localStorage.removeItem('timerEnd'); }
  if (action.tool === 'remember' && a.fact) { S.memory.push(String(a.fact).slice(0, 200)); save(); }
  if (action.tool === 'forget' && a.text) { const t = String(a.text).toLowerCase(); S.memory = S.memory.filter((x) => !x.toLowerCase().includes(t)); save(); }
}
let ctrl;
async function ask(text) {
  text = text.trim(); if (!text || S.mode === 'thinking') return;
  $('q').value = '';
  if (S.chatting && /^(stop|bye|goodbye|thanks|thank you|that's all)\b/i.test(text)) { S.chatting = false; $('chattag').style.display = 'none'; say("Okay. I'm here when you need me."); return; }
  const before = S.turns.slice();
  add('you', text);
  let r = N.local(text);
  if (!r) {
    setMode('thinking');
    ctrl = new AbortController();
    r = await N.ask({ client: 'web', device, turns: before, text, memory: S.memory, tools: TOOLS, jwt: await Auth.token(), signal: ctrl.signal });
    if (r.aborted || S.mode !== 'thinking') return;
  }
  (r.actions || []).forEach(run);
  if (r.refused) { S.turns.pop(); save(); render(); setMode('idle'); banner(r.reply, 6); tip(r.reply.replace('⚠︎ ', '')); return; }
  say(r.reply || 'Done.');
}

// ---------- optional sign-in (shared ZeroOrigine accounts, magic link, PKCE) ----------
const Auth = (() => {
  const c = window.NOTCH_CONFIG;
  let sb = null;
  try { sb = window.supabase.createClient(c.supabaseUrl, c.publishableKey, { auth: { flowType: 'pkce', detectSessionInUrl: true, persistSession: true } }); } catch (_) {}
  async function token() { try { const { data } = await sb.auth.getSession(); return data.session?.access_token || null; } catch { return null; } }
  async function refreshChip() {
    const chip = $('signchip'); if (!chip) return;
    let email = null; try { const { data } = await sb.auth.getSession(); email = data.session?.user?.email || null; } catch {}
    chip.textContent = email ? '✓ ' + email.split('@')[0] : '✉︎ Sign in';
    chip.dataset.signed = email ? '1' : '';
  }
  async function signInOrOut() {
    if (!sb) { tip('Sign-in is not available right now.'); return; }
    if ($('signchip').dataset.signed) { await sb.auth.signOut(); refreshChip(); tip('Signed out.'); return; }
    const email = (prompt('Your email. We will send you a sign-in link. No password.') || '').trim();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { if (email) tip('That email does not look right.'); return; }
    const { error } = await sb.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + '/app/' } });
    tip(error ? 'Could not send the link: ' + error.message : 'Check your email and tap the link to sign in.');
  }
  if (sb) sb.auth.onAuthStateChange(() => refreshChip());
  return { token, refreshChip, signInOrOut };
})();

// ---------- voice in ----------
let rec = null;
function listen() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { tip('Voice typing is not supported in this browser. Use Safari or Chrome.'); return; }
  if (rec) { rec.stop(); return; }
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  S.chatting = true; $('chattag').style.display = 'inline';
  rec = new SR(); rec.lang = 'en-IN'; rec.interimResults = true; rec.continuous = false;
  let fin = '';
  rec.onstart = () => { setMode('listening'); $('mic').classList.add('on'); $('q').placeholder = 'Listening…'; };
  rec.onresult = (e) => { let t = ''; for (const r of e.results) t += r[0].transcript; $('q').value = t; if (e.results[e.results.length - 1].isFinal) fin = t; };
  rec.onerror = (e) => { if (e.error === 'not-allowed' || e.error === 'service-not-allowed') tip('Please allow the microphone and speech recognition for this site.'); };
  rec.onend = () => {
    rec = null; $('mic').classList.remove('on'); $('q').placeholder = 'Ask Nova…';
    const t = (fin || $('q').value).trim(); setMode('idle');
    if (t) ask(t); else { S.chatting = false; $('chattag').style.display = 'none'; setMode('idle'); }
  };
  try { rec.start(); } catch { rec = null; setMode('idle'); }
}
function stopAll() {
  S.chatting = false; $('chattag').style.display = 'none';
  if (rec) { rec.onend = null; rec.stop(); rec = null; $('mic').classList.remove('on'); $('q').placeholder = 'Ask Nova…'; }
  if (ctrl) ctrl.abort();
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  setMode('idle'); banner('Stopped', 1.5);
}
let tipT; function tip(t) { $('tip').textContent = t; $('tip').style.display = 'block'; clearTimeout(tipT); tipT = setTimeout(() => $('tip').style.display = 'none', 6000); }

// ---------- buttons ----------
$('q').addEventListener('keydown', (e) => { if (e.key === 'Enter') ask($('q').value); });
$('mic').onclick = listen;
$('stop').onclick = stopAll;
const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
let installEvt = null;
addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installEvt = e; });
if (standalone) $('installchip').style.display = 'none';
document.querySelectorAll('.chip').forEach(c => c.onclick = async () => {
  const a = c.dataset.a;
  if (a === 't5' || a === 't1') { startTimer(a === 't5' ? 5 : 1); say(`Timer set for ${a === 't5' ? 5 : 1} minute${a === 't5' ? 's' : ''}.`); }
  if (a === 'voice') { S.voice = !S.voice; localStorage.setItem('voice', S.voice ? 'on' : 'off'); c.textContent = S.voice ? '🔊 Voice on' : '🔇 Voice off'; }
  if (a === 'new') { S.turns = []; save(); render(); }
  if (a === 'sign') Auth.signInOrOut();
  if (a === 'install') {
    if (installEvt) { installEvt.prompt(); installEvt = null; }
    else if (/iPad|iPhone|iPod|Macintosh/.test(navigator.userAgent) && 'ontouchend' in document) tip('Tap the Share button ( ⬆︎ ) then “Add to Home Screen”.');
    else tip('In Chrome: click the install icon in the address bar, or menu ⋮ → “Install Notch”.');
  }
});
$('voicechip').textContent = S.voice ? '🔊 Voice on' : '🔇 Voice off';
if ('speechSynthesis' in window) speechSynthesis.getVoices();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
render();
Auth.refreshChip();
requestAnimationFrame(loop);
