// Notch background: talks to Nova through ZeroOrigine's notch-api, runs the actions, keeps the timer.
importScripts('nova-core.js');
const N = self.NovaCore;
const TOOLS = ['open_url', 'search_web', 'youtube', 'timer', 'remember', 'forget', 'close_tab'];

const get = (k, d) => chrome.storage.local.get(k).then((r) => r[k] ?? d);
const set = (o) => chrome.storage.local.set(o);
async function device() {
  let d = await get('device', '');
  if (!N.validDevice(d)) { d = N.newDeviceId(); await set({ device: d }); }
  return d;
}

chrome.runtime.onInstalled.addListener(async (d) => {
  await set({ enabled: true });
  await device();
  if (d.reason === 'install') {
    const tabs = await chrome.tabs.query({ url: ['http://*/*', 'https://*/*'] });
    for (const t of tabs) chrome.scripting.executeScript({ target: { tabId: t.id }, files: ['notch.js'] }).catch(() => {});
  }
});
chrome.action.onClicked.addListener(async () => { await set({ enabled: !(await get('enabled', true)) }); });
chrome.commands.onCommand.addListener(async (c) => {
  if (c !== 'open-nova') return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) chrome.tabs.sendMessage(tab.id, { type: 'open' }).catch(() => {});
});

// ── timer ──
async function startTimer(min, label = 'Timer') {
  const m = Math.min(24 * 60, Math.max(0.1, Number(min) || 1));
  await set({ timerEnd: Date.now() + m * 60000, timerLabel: label });
  chrome.alarms.create('notch-timer', { delayInMinutes: m });
}
chrome.alarms.onAlarm.addListener(async (a) => {
  if (a.name !== 'notch-timer') return;
  const label = await get('timerLabel', 'Timer');
  await set({ timerEnd: null, timerLabel: '' });
  chrome.notifications.create({ type: 'basic', iconUrl: 'icons/128.png', title: 'Nova', message: `${label} is done.` });
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (tab) chrome.tabs.sendMessage(tab.id, { type: 'say', text: `Your ${String(label).toLowerCase()} is done.` }).catch(() => {});
});

// ── actions (the only place the extension acts) ──
async function run(action, tab) {
  const url = N.urlFor(action);
  if (url) { await chrome.tabs.create({ url }); return action.tool; }
  const a = action.args || {};
  switch (action.tool) {
    case 'timer': await startTimer(a.minutes, a.label || 'Timer'); return 'timer';
    case 'stop_timer': chrome.alarms.clear('notch-timer'); await set({ timerEnd: null }); return 'timer stopped';
    case 'remember': { const m = await get('memory', []); if (a.fact) { m.push(String(a.fact).slice(0, 200)); await set({ memory: m.slice(-60) }); } return 'remembered'; }
    case 'forget': { const m = await get('memory', []); const t = String(a.text || '').toLowerCase(); await set({ memory: m.filter((x) => !x.toLowerCase().includes(t)) }); return 'forgot'; }
    case 'close_tab': if (tab?.id) setTimeout(() => chrome.tabs.remove(tab.id).catch(() => {}), 1500); return 'closing tab';
  }
  return '';
}

async function ask(text, tab) {
  const turns = await get('turns', []);
  let r = N.local(text);
  if (!r) {
    r = await N.ask({ client: 'chrome', device: await device(), turns, text, memory: await get('memory', []), tools: TOOLS,
      page: tab ? { title: tab.title || '', url: tab.url || '' } : null });
  }
  const steps = [];
  for (const a of r.actions || []) { const s = await run(a, tab); if (s) steps.push(s); }
  if (!r.refused) { turns.push(['you', text], ['nova', r.reply]); await set({ turns: turns.slice(-200) }); }
  return { reply: r.reply, steps };
}

// ── voice: runs in the extension's own window, so the microphone belongs to Notch, never to the website ──
let voiceTab = null;
async function openVoice(tabId) {
  await set({ voiceFor: tabId });
  const w = await chrome.windows.create({ url: 'voice.html', type: 'popup', width: 380, height: 220, focused: true });
  voiceTab = w.tabs?.[0]?.id ?? null;
}

chrome.runtime.onMessage.addListener((msg, sender, send) => {
  (async () => {
    if (msg.type === 'ask') send(await ask(String(msg.text || '').slice(0, 4000), sender.tab));
    else if (msg.type === 'newchat') { await set({ turns: [] }); send({}); }
    else if (msg.type === 'timer') { await startTimer(msg.minutes); send({}); }
    else if (msg.type === 'voice') { await openVoice(sender.tab?.id); send({}); }
    else if (msg.type === 'heard') {            // from voice.html
      const tabId = await get('voiceFor', null);
      if (tabId) chrome.tabs.sendMessage(tabId, { type: 'heard', text: String(msg.text || '') }).catch(() => {});
      if (sender.tab?.windowId) chrome.windows.remove(sender.tab.windowId).catch(() => {});
      send({});
    }
    else send({});
  })();
  return true;
});
