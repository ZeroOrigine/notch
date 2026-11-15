// node tests/nova-core.test.js
const assert = require('assert');
const N = require('../nova-core.js');
let pass = 0; const t = (name, fn) => { try { fn(); pass++; } catch (e) { console.log('FAIL', name, e.message); process.exitCode = 1; } };
const at = async (name, fn) => { try { await fn(); pass++; } catch (e) { console.log('FAIL', name, e.message); process.exitCode = 1; } };

t('safeUrl bare domain', () => assert.strictEqual(N.safeUrl('youtube.com'), 'https://youtube.com/'));
t('safeUrl http ok', () => assert.ok(N.safeUrl('http://a.com/x?y=1')));
t('safeUrl port ok', () => assert.strictEqual(N.safeUrl('site.com:8080'), 'https://site.com:8080/'));
t('safeUrl javascript', () => assert.strictEqual(N.safeUrl('javascript:alert(1)'), null));
t('safeUrl data', () => assert.strictEqual(N.safeUrl('data:text/html,hi'), null));
t('safeUrl file', () => assert.strictEqual(N.safeUrl('file:///etc/passwd'), null));
t('safeUrl custom scheme', () => assert.strictEqual(N.safeUrl('chrome://settings'), null));
t('safeUrl spaces', () => assert.strictEqual(N.safeUrl('two words'), null));
t('noDashes', () => assert.strictEqual(N.noDashes('a — b–c'), 'a, b, c'));
t('device id', () => { const d = N.newDeviceId(); assert.ok(N.validDevice(d)); assert.strictEqual(d.length, 32); });
t('device invalid', () => assert.ok(!N.validDevice('x')));

t('local timer', () => { const r = N.local('set a 3 minute timer'); assert.deepStrictEqual(r.actions, [{ tool: 'timer', args: { minutes: 3 } }]); assert.strictEqual(r.reply, 'Timer set for 3 minutes.'); });
t('local timer 1', () => assert.strictEqual(N.local('timer for 1 min').reply, 'Timer set for 1 minute.'));
t('local open youtube please', () => assert.deepStrictEqual(N.local('open youtube please').actions, [{ tool: 'open_url', args: { url: 'https://youtube.com/' } }]));
t('local open domain', () => assert.strictEqual(N.local('go to bbc.co.uk').actions[0].args.url, 'https://bbc.co.uk/'));
t('local open gmail', () => assert.strictEqual(N.local('Open Gmail.').actions[0].args.url, 'https://mail.google.com/'));
t('local open sentence → brain', () => assert.strictEqual(N.local('open the thing my boss sent'), null));
t('local play', () => assert.deepStrictEqual(N.local('play lofi beats on youtube').actions, [{ tool: 'youtube', args: { query: 'lofi beats' } }]));
t('local search', () => assert.deepStrictEqual(N.local('search for pizza near me').actions, [{ tool: 'search_web', args: { query: 'pizza near me' } }]));
t('local remember keeps case', () => assert.strictEqual(N.local('Remember that my manager is Sam.').actions[0].args.fact, 'my manager is Sam'));
t('local stop timer', () => assert.strictEqual(N.local('cancel the timer').actions[0].tool, 'stop_timer'));
t('local question → brain', () => assert.strictEqual(N.local('what is 12 times 12'), null));

t('urlFor open_url unsafe', () => assert.strictEqual(N.urlFor({ tool: 'open_url', args: { url: 'javascript:x' } }), null));
t('urlFor search encodes', () => assert.strictEqual(N.urlFor({ tool: 'search_web', args: { query: 'a&b' } }), 'https://www.google.com/search?q=a%26b'));
t('urlFor timer none', () => assert.strictEqual(N.urlFor({ tool: 'timer', args: {} }), null));

t('toMessages alternates and starts with user', () => {
  const m = N.toMessages([['nova', 'hi'], ['you', 'a'], ['you', 'b'], ['nova', 'c']], 'd');
  assert.deepStrictEqual(m.map((x) => x.role), ['user', 'assistant', 'user']);
  assert.strictEqual(m[0].content, 'a\nb'); assert.strictEqual(m[2].content, 'd');
});
t('toMessages caps 14', () => { const turns = Array.from({ length: 40 }, (_, i) => [i % 2 ? 'nova' : 'you', 'x']); assert.ok(N.toMessages(turns, 'q').length <= 14); });

(async () => {
  const fake = (status, body) => { const fn = async (url, opts) => { fn.last = { url, opts }; return { ok: status === 200, status, json: async () => body }; }; return fn; };
  await at('ask success', async () => {
    const f = fake(200, { reply: 'Opening — now', actions: [{ tool: 'open_url', args: { url: 'https://a.com' } }, { bad: 1 }] });
    const r = await N.ask({ client: 'web', device: 'd'.repeat(20), turns: [], text: 'open a', tools: ['open_url'], fetchFn: f });
    assert.strictEqual(r.reply, 'Opening, now'); assert.strictEqual(r.actions.length, 1);
    assert.strictEqual(f.last.opts.headers['x-notch-device'], 'd'.repeat(20));
    assert.strictEqual(JSON.parse(f.last.opts.body).client, 'web');
    assert.ok(f.last.url.endsWith('/notch-api/ask'));
  });
  await at('ask limit', async () => { const r = await N.ask({ client: 'web', device: 'd'.repeat(20), text: 'x', fetchFn: fake(429, { error: 'limit: 30 questions an hour' }) }); assert.ok(r.refused); assert.ok(r.reply.includes('30 questions')); });
  await at('ask offline', async () => { const r = await N.ask({ client: 'web', device: 'd'.repeat(20), text: 'x', fetchFn: async () => { throw new Error('net'); } }); assert.ok(r.reply.includes('No internet')); });
  await at('ask jwt header', async () => { const f = fake(200, { reply: 'ok', actions: [] }); await N.ask({ client: 'web', device: 'd'.repeat(20), text: 'x', jwt: 'a.b.c', fetchFn: f }); assert.strictEqual(f.last.opts.headers.authorization, 'Bearer a.b.c'); });
  await at('ask tool-only reply says Done', async () => { const r = await N.ask({ client: 'web', device: 'd'.repeat(20), text: 'x', fetchFn: fake(200, { reply: '', actions: [{ tool: 'timer', args: { minutes: 2 } }] }) }); assert.strictEqual(r.reply, 'Done.'); });
  console.log(`TESTS: ${pass} passed${process.exitCode ? ', SOME FAILED' : ', 0 failed'}`);
})();
