import { chromium } from 'playwright';
import http from 'http'; import fs from 'fs'; import path from 'path';
const [out, spec, shard = '0/1'] = process.argv.slice(2);
const root = process.cwd(), types = { '.html': 'text/html', '.js': 'text/javascript' };
const srv = http.createServer((q, r) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); } }); });
await new Promise(r => srv.listen(0, r)); const port = srv.address().port;
let frames = []; for (const part of spec.split(',')) { if (part.includes('-')) { const [a, b] = part.split('-').map(Number); for (let i = a; i <= b; i++) frames.push(i); } else frames.push(+part); }
const [si, sn] = shard.split('/').map(Number); frames = frames.filter((f, i) => i % sn === si);
fs.mkdirSync(out, { recursive: true });
const br = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox'] });
const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
pg.on('console', m => { if (m.type() === 'error') console.log('ERR', m.text()); }); pg.on('pageerror', e => console.log('PAGEERR', e.message));
await pg.goto(`http://localhost:${port}/web/index.html`); await pg.waitForFunction('window.ready===true', null, { timeout: 60000 });
const t0 = Date.now(); let n = 0;
for (const f of frames) {
  const fn = path.join(out, 'f' + String(f).padStart(4, '0') + '.jpg'); if (process.env.RESUME && fs.existsSync(fn)) continue;
  const d = await pg.evaluate((f) => { window.renderFrame(f); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, f);
  fs.writeFileSync(fn, Buffer.from(d.split(',')[1], 'base64')); n++;
  if (n % 50 === 0) console.log(`shard ${si}: ${n}/${frames.length} ${((Date.now() - t0) / n / 1000).toFixed(2)}s/f`);
}
console.log(`done shard ${si}: ${n} frames, ${((Date.now() - t0) / Math.max(1, n) / 1000).toFixed(2)}s/f`);
await br.close(); srv.close();
