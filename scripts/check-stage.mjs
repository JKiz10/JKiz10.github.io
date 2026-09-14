#!/usr/bin/env node
// Runtime checks for the homepage stage (the rotating hero) in real headless Chrome.
//
//   node scripts/check-stage.mjs                            serves this repo locally
//   node scripts/check-stage.mjs https://jkiz10.github.io   checks a live host
//   node scripts/check-stage.mjs --shots ./shots            also saves a screenshot per scenario
//
// Needs Google Chrome (override the path with CHROME=...) and Node 22+ for the
// global WebSocket. No npm packages. Waits follow the load event and the stage's
// own rotation clock, so keep HOLD_MS and START_DELAY_MS in step with site.js.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const HOLD_MS = 7000;
const START_DELAY_MS = 600;
const CROSSFADE_MARGIN_MS = 2200;
const CHROME_START_TIMEOUT_MS = 20000;
const FRAMES = [
  'vue-point-bedroom-canopy-hero', 'gateway-condo-primary-bedroom-hero', 'rockpoint-primary-bathroom-hero',
  'knoll-kitchen-plaster-hood-hero', 'evergreen-bedroom-navy-grid-wall-hero', 'starfish-covered-porch-hero',
];
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.jpg': 'image/jpeg',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.xml': 'application/xml',
};

const args = process.argv.slice(2);
const shotsDir = args.includes('--shots') ? path.resolve(args[args.indexOf('--shots') + 1]) : null;
const remoteOrigin = args.find((arg) => /^https?:\/\//.test(arg));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const frameOf = (url) => FRAMES.findIndex((frame) => url.includes(`/${frame}`));

// Serves the repo the way GitHub Pages does: a folder URL without its trailing
// slash gets a 301, and the slashed form serves index.html.
function serveRepo() {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://local');
    let file = path.normalize(path.join(REPO, decodeURIComponent(url.pathname)));
    if (file !== REPO && !file.startsWith(REPO + path.sep)) { res.writeHead(403); res.end(); return; }
    try {
      if (fs.statSync(file).isDirectory()) {
        if (!url.pathname.endsWith('/')) {
          res.writeHead(301, { Location: `${url.pathname}/${url.search}` });
          res.end();
          return;
        }
        file = path.join(file, 'index.html');
      }
      const body = fs.readFileSync(file);
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(body);
    } catch {
      res.writeHead(404);
      res.end('not found');
    }
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function launchChrome() {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'jkd-stage-'));
  const proc = spawn(CHROME, [
    '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((resolve, reject) => {
    let stderr = '';
    const timer = setTimeout(() => reject(new Error(`Chrome did not start:\n${stderr}`)), CHROME_START_TIMEOUT_MS);
    proc.stderr.on('data', (chunk) => {
      stderr += chunk;
      const match = stderr.match(/DevTools listening on (ws:\/\/\S+)/);
      if (match) { clearTimeout(timer); resolve(match[1]); }
    });
    proc.on('exit', (code) => { clearTimeout(timer); reject(new Error(`Chrome exited with ${code}:\n${stderr}`)); });
  });

  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let nextId = 0;
  const pending = new Map();
  const handlers = new Set();
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id === undefined) { handlers.forEach((handler) => handler(msg)); return; }
    const waiter = pending.get(msg.id);
    if (!waiter) return;
    pending.delete(msg.id);
    if (msg.error) waiter.reject(new Error(`${waiter.method}: ${msg.error.message}`));
    else waiter.resolve(msg.result);
  };
  const send = (method, params = {}, sessionId) => {
    const id = ++nextId;
    ws.send(JSON.stringify(sessionId ? { id, method, params, sessionId } : { id, method, params }));
    return new Promise((resolve, reject) => pending.set(id, { resolve, reject, method }));
  };

  return {
    // A fresh tab in its own browser context, so no cache or state leaks between scenarios.
    async newPage() {
      const { browserContextId } = await send('Target.createBrowserContext');
      const { targetId } = await send('Target.createTarget', { url: 'about:blank', browserContextId });
      const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
      const pageSend = (method, params) => send(method, params, sessionId);
      const on = (fn) => {
        const handler = (msg) => { if (msg.sessionId === sessionId) fn(msg); };
        handlers.add(handler);
        return () => handlers.delete(handler);
      };
      return {
        send: pageSend,
        on,
        goto: async (url) => {
          const loaded = new Promise((resolve) => {
            const off = on((msg) => { if (msg.method === 'Page.loadEventFired') { off(); resolve(Date.now()); } });
          });
          const result = await pageSend('Page.navigate', { url });
          if (result.errorText) throw new Error(`navigate ${url}: ${result.errorText}`);
          return loaded;
        },
        eval: async (expression) => {
          const result = await pageSend('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
          if (result.exceptionDetails) {
            throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
          }
          return result.result.value;
        },
        close: () => send('Target.disposeBrowserContext', { browserContextId }),
      };
    },
    async close() {
      ws.close();
      proc.kill();
      await sleep(300);
      fs.rmSync(profile, { recursive: true, force: true });
    },
  };
}

const READ_STATE = `(() => {
  const stage = document.querySelector('.stage');
  const slides = [...stage.querySelectorAll('.stage__slide')];
  return {
    armed: stage.getAttribute('data-armed'),
    active: slides.findIndex((s) => s.getAttribute('data-active') === 'true'),
    tick: [...stage.querySelectorAll('.stage__tick')].findIndex((t) => t.getAttribute('aria-current') === 'true'),
    credit: stage.querySelector('.stage__credit').textContent,
    frames: slides.map((s) => {
      const img = s.querySelector('img');
      const css = getComputedStyle(s);
      return { display: css.display, opacity: css.opacity, loaded: img.complete && img.naturalWidth > 0,
        file: (img.currentSrc || '').split('/').pop() };
    }),
  };
})()`;

async function scenario(chrome, base, name, opt) {
  const page = await chrome.newPage();
  const dpr = opt.dpr || 1;
  await page.send('Page.enable');
  await page.send('Network.enable');
  await page.send('Network.setCacheDisabled', { cacheDisabled: true });
  await page.send('Emulation.setDeviceMetricsOverride', { width: opt.width, height: opt.height, deviceScaleFactor: dpr, mobile: Boolean(opt.mobile) });
  if (opt.reducedMotion) await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  if (opt.noJs) await page.send('Emulation.setScriptExecutionDisabled', { value: true });
  if (opt.block) await page.send('Network.setBlockedURLs', { urls: opt.block });

  const t0 = Date.now();
  const requests = [];
  page.on((msg) => {
    if (msg.method !== 'Network.requestWillBeSent') return;
    const frame = frameOf(msg.params.request.url);
    if (frame >= 0) requests.push({ frame, at: Date.now() - t0 });
  });

  const loadAt = (await page.goto(`${base}/?stage-check=${t0}`)) - t0;
  if (opt.clickTick !== undefined) {
    await sleep(1500);
    await page.eval(`document.querySelectorAll('.stage__tick')[${opt.clickTick}].click()`);
  }
  await sleep(Math.max(0, loadAt + START_DELAY_MS + HOLD_MS + CROSSFADE_MARGIN_MS - (Date.now() - t0)));

  let state;
  try { state = await page.eval(READ_STATE); } catch (err) { state = { error: String(err.message || err) }; }
  if (shotsDir) {
    const shot = await page.send('Page.captureScreenshot', {
      format: 'jpeg', quality: 72, clip: { x: 0, y: 0, width: opt.width, height: opt.height, scale: 1 / dpr },
    });
    fs.mkdirSync(shotsDir, { recursive: true });
    fs.writeFileSync(path.join(shotsDir, `stage-${name}.jpg`), Buffer.from(shot.data, 'base64'));
  }
  await page.close();
  return { loadAt, requests, state };
}

const server = remoteOrigin ? null : await serveRepo();
const base = remoteOrigin ? remoteOrigin.replace(/\/$/, '') : `http://127.0.0.1:${server.address().port}`;
const chrome = await launchChrome();
const run = {};
try {
  run.desktop = await scenario(chrome, base, 'desktop', { width: 1440, height: 900 });
  run.mobile = await scenario(chrome, base, 'mobile', { width: 390, height: 844, dpr: 3, mobile: true });
  run.noJs = await scenario(chrome, base, 'no-js', { width: 1440, height: 900, noJs: true });
  run.calm = await scenario(chrome, base, 'reduced-motion', { width: 1440, height: 900, reducedMotion: true });
  run.calmClick = await scenario(chrome, base, 'reduced-motion-click', { width: 1440, height: 900, reducedMotion: true, clickTick: 2 });
  run.broken = await scenario(chrome, base, 'frame-2-blocked', { width: 1440, height: 900, block: ['*gateway-condo-primary-bedroom-hero*'] });
} finally {
  await chrome.close();
  if (server) server.close();
}

const deferred = (r) => r.requests.filter((q) => q.frame > 0);
const checks = [
  ['desktop: frame 1 requested before load', run.desktop.requests.some((q) => q.frame === 0 && q.at <= run.desktop.loadAt)],
  ['desktop: frames 2-6 not requested until after load', deferred(run.desktop).length >= 5 && deferred(run.desktop).every((q) => q.at > run.desktop.loadAt)],
  ['desktop: rotated to frame 2 after one hold', run.desktop.state.active === 1 && run.desktop.state.tick === 1],
  ['desktop: all six frames loaded', Boolean(run.desktop.state.frames?.every((f) => f.loaded))],
  ['desktop: credit follows the frame', Boolean(run.desktop.state.credit?.startsWith('Gateway Condo'))],
  ['mobile: rotated and loaded', run.mobile.state.active === 1 && Boolean(run.mobile.state.frames?.every((f) => f.loaded))],
  ['mobile: frames 2-6 not requested until after load', deferred(run.mobile).every((q) => q.at > run.mobile.loadAt)],
  ['no JS: first frame visible', run.noJs.state.frames?.[0]?.opacity === '1'],
  ['no JS: other frames out of layout', Boolean(run.noJs.state.frames?.slice(1).every((f) => f.display === 'none'))],
  ['no JS: credit present in the HTML', Boolean(run.noJs.state.credit?.startsWith('Vue Point'))],
  ['reduced motion: never fetches frames 2-6', deferred(run.calm).length === 0],
  ['reduced motion: holds frame 1', run.calm.state.active === 0 && run.calm.state.armed === null],
  ['reduced motion + click: shows the chosen frame', run.calmClick.state.active === 2 && Boolean(run.calmClick.state.frames?.[2]?.loaded)],
  ['a broken frame is skipped, never faded to blank', run.broken.state.active === 2],
];

let failed = 0;
for (const [label, ok] of checks) {
  if (!ok) failed += 1;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
}
console.log(`${checks.length - failed}/${checks.length} passed against ${base}`);
process.exitCode = failed ? 1 : 0;
