
const $ = (id) => document.getElementById(id);
const demo = [
  ['idle', '', 2200], ['listening', '', 1800], ['thinking', '', 1500],
  ['banner', 'Opening YouTube for you.', 2600], ['timer', '', 2600], ['speaking', '', 2000], ['banner', 'Your timer is done.', 2400]
];
let step = 0, mode = 'idle', timerStart = 0;
function next() {
  const [m, text, ms] = demo[step % demo.length]; step++;
  mode = m; const isl = $('isl'), r = $('right');
  isl.className = 'isl' + (m === 'banner' ? ' big' : m === 'idle' ? '' : ' wide') + (m === 'thinking' || m === 'speaking' ? ' glowing' : '');
  $('bt').textContent = text;
  r.innerHTML = m === 'listening' ? '<span class="eq red"><i></i><i></i><i></i><i></i></span>' : m === 'speaking' ? '<span class="eq"><i></i><i></i><i></i><i></i></span>' : m === 'thinking' ? 'Thinking' : '';
  if (m === 'timer') timerStart = Date.now();
  setTimeout(next, ms);
}
let skyT = 0;
function loop(now) {
  const t = now / 1000, busy = mode === 'thinking' || mode === 'speaking';
  NovaArt.star($('hstar'), t, busy); NovaArt.star($('mini'), t, busy);
  if (mode === 'timer') $('right').textContent = '⏱ 4:' + String(59 - Math.floor((Date.now() - timerStart) / 1000) % 60).padStart(2, '0');
  if (now - skyT > 33) { NovaArt.stars($('sky'), t); skyT = now; }
  requestAnimationFrame(loop);
}
next(); requestAnimationFrame(loop);
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
