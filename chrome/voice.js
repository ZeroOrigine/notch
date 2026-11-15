// Voice capture inside the extension origin. The website never gets microphone access.
// Only what the person actually said is sent back. Status and error text never are.
const SR = self.SpeechRecognition || self.webkitSpeechRecognition;
const $ = (id) => document.getElementById(id);
let sent = false, said = '', fin = '';
const done = (text) => { if (sent) return; sent = true; chrome.runtime.sendMessage({ type: 'heard', text: (text || '').trim() }); };
if (!SR) { $('t').textContent = 'Voice is not supported here.'; setTimeout(() => done(''), 1500); }
else {
  const rec = new SR(); rec.lang = 'en-IN'; rec.interimResults = true; rec.continuous = false;
  rec.onresult = (e) => {
    said = ''; for (const r of e.results) said += r[0].transcript;
    $('t').textContent = said;
    if (e.results[e.results.length - 1].isFinal) fin = said;
  };
  rec.onerror = (e) => {
    said = ''; fin = '';
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') { $('t').textContent = 'Please allow the microphone for Notch.'; $('s').textContent = 'Click the mic icon in the address bar, then try again.'; }
    else $('t').textContent = 'I could not hear you.';
    setTimeout(() => done(''), 2500);
  };
  rec.onend = () => { if (fin || said) done(fin || said); else setTimeout(() => done(''), 2600); };
  rec.start();
}
