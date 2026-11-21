import { THREE, renderer, world, over, camera, hemi, sun, lamp, clamp, lerp, ss, eout, spring, rnd, M, MB, B, G, canvasTex, texMat, tiles, Actor, U, draw, K, setCam, look, lerpC, tint } from './engine.js';

const FPS = 30;
const sets = {};
function mk(name) { const s = { w: G(world), o: G(over) }; s.w.visible = s.o.visible = false; sets[name] = s; return s; }
const talk = (f, on = true) => on ? ['open', 'smile', 'o', 'open', 'flat', 'open'][Math.floor(f / 3) % 6] : 'smile';
const D = new THREE.Object3D(), BGEO = new THREE.BoxGeometry(1, 1, 1), white = new THREE.MeshToonMaterial({ color: 0xffffff });
const col = new THREE.Color();

// ---------- shared builders ----------
function wave(x, z, t, amp) { return amp * (Math.sin(0.35 * x + 1.3 * t) + 0.6 * Math.sin(0.22 * z + 0.9 * t + 1) + 0.4 * Math.sin(0.5 * (x + z) - 1.7 * t)) / 2; }
function makeSea(parent, nx, nz, cs) {
  const m = new THREE.InstancedMesh(BGEO, new THREE.MeshToonMaterial({ color: 0xffffff }), nx * nz); m.frustumCulled = false; parent.add(m);
  return { m, update(t, amp, ox, oz, deep, light, shadow) {
      const q = Math.max(0.06, amp * 0.28); let i = 0; const cd = new THREE.Color(deep), cl = new THREE.Color(light);
      for (let a = 0; a < nx; a++) for (let b = 0; b < nz; b++, i++) {
        const x = ox + (a + 0.5) * cs, z = oz + (b + 0.5) * cs; const h = wave(x, z, t, amp), y = Math.round(h / q) * q;
        D.position.set(x, y - 3, z); D.scale.set(cs, 6, cs); D.rotation.set(0, 0, 0); D.updateMatrix(); m.setMatrixAt(i, D.matrix);
        const u = clamp(h / (amp + 1e-3) * 0.5 + 0.5); col.copy(cd).lerp(cl, u); if (amp > 0.6 && u > 0.86) col.lerp(new THREE.Color(0xffffff), 0.4);
        if (shadow) col.multiplyScalar(1 - 0.6 * shadow(x, z)); m.setColorAt(i, col);
      }
      m.instanceMatrix.needsUpdate = true; m.instanceColor.needsUpdate = true;
    } };
}
function makeBoat(parent) {
  const g = G(parent), w1 = '#9a6336', w2 = '#7a4a26';
  B(g, 4.6, 0.55, 1.7, w1); B(g, 4.6, 0.3, 0.12, w2, 0, 0.55, 0.8); B(g, 4.6, 0.3, 0.12, w2, 0, 0.55, -0.8);
  B(g, 0.6, 0.75, 1.3, w1, 2.55, 0.1, 0); B(g, 0.4, 0.6, 0.8, w2, 3.0, 0.4, 0); B(g, 0.3, 0.95, 1.7, w2, -2.4, 0, 0);
  B(g, 0.16, 4.3, 0.16, '#6b4423', 0.2, 0.55, -0.2); const sail = B(g, 2.1, 1.7, 0.08, '#ffffff', 0.2, 2.75, -0.1); B(g, 2.3, 0.1, 0.12, '#6b4423', 0.2, 4.45, -0.1); B(g, 0.5, 0.3, 0.05, '#d93a3a', 0.5, 4.6, -0.2);
  return { g, sail };
}
function makeFish(parent) {
  const g = G(parent), dk = '#27408b', lt = '#dcecf5', seg = (w, h, z0, z1, y = 0) => { B(g, w, h * 0.62, z1 - z0, dk, 0, y - h * 0.12, (z0 + z1) / 2); B(g, w * 0.94, h * 0.4, z1 - z0, lt, 0, y - h * 0.5, (z0 + z1) / 2); };
  seg(8, 7.4, -0.5, 6.5, 0.4); seg(7, 6.2, -6, -0.5, 0.3); seg(5, 4.4, -10, -6, 0.2); seg(3, 2.8, -12.6, -10, 0.1);
  const tail = G(g, 0, 0.2, -12.4); B(tail, 0.8, 7.5, 2.2, dk, 0, -3.75, -1.2); B(tail, 0.8, 2, 1.4, dk, 0, 2.6, -2.4); B(tail, 0.8, 2, 1.4, dk, 0, -4.6, -2.4);
  B(g, 0.8, 2.2, 4, dk, 0, 4.4, -1.5); B(g, 0.8, 1.2, 2, dk, 0, 6.2, -2.2);
  const fl = B(g, 3, 0.6, 2.6, dk, 5, -1.8, 2), fr = B(g, 3, 0.6, 2.6, dk, -5, -1.8, 2);
  const up = G(g, 0, 0.5, 6.5), lo = G(g, 0, 0.5, 6.5);
  B(up, 8, 3.9, 7, dk, 0, 0, 3.5); B(up, 7.2, 0.3, 6.4, '#e56b83', 0, -0.2, 3.3);
  for (const s of [-1, 1]) { B(up, 0.25, 1.5, 1.5, '#ffffff', s * 4.05, 1.6, 2.2); B(up, 0.3, 0.8, 0.8, '#1a1a2a', s * 4.12, 1.75, 2.5); }
  for (let i = 0; i < 7; i++) B(up, 0.6, 0.7, 0.5, '#ffffff', -3 + i, -0.7, 6.6); for (const sx of [-1, 1]) { B(up, 1.5, 1.5, 0.25, '#ffffff', sx * 2.5, 1.7, 7.05); B(up, 0.8, 0.8, 0.3, '#1a1a2a', sx * 2.4, 1.85, 7.12); }
  B(lo, 7.6, 2.8, 6.8, lt, 0, -2.8, 3.4); B(lo, 6.8, 0.3, 6.2, '#e56b83', 0, -0.1, 3.3); B(lo, 3.4, 0.35, 4, '#ff9fb2', 0, 0.15, 3.2);
  for (let i = 0; i < 6; i++) B(lo, 0.6, 0.6, 0.5, '#ffffff', -2.5 + i, 0.1, 6.4);
  return { g, up, lo, tail, fl, fr, jaw(a) { up.rotation.x = -a; lo.rotation.x = a * 0.7; }, swim(t) { tail.rotation.y = Math.sin(t * 5) * 0.35; fl.rotation.z = Math.sin(t * 3) * 0.2; fr.rotation.z = -Math.sin(t * 3) * 0.2; } };
}
function makeDuck(parent) { // rubber fish (yellow)
  const g = G(parent), y = '#ffd21f'; B(g, 0.2, 0.12, 0.09, y); B(g, 0.07, 0.16, 0.07, y, -0.13, -0.02, 0); B(g, 0.05, 0.05, 0.1, '#ff8a1f', 0.11, 0.03, 0); B(g, 0.03, 0.03, 0.1, '#1a1a2a', 0.05, 0.08, 0); B(g, 0.08, 0.05, 0.05, y, 0, 0.12, 0); return g;
}
class Burst {
  constructor(parent, n, seed, colA = '#ffffff', colB = '#7fc4f0') { this.n = n; this.seed = seed; this.m = new THREE.InstancedMesh(BGEO, white, n); this.m.frustumCulled = false; parent.add(this.m); for (let i = 0; i < n; i++) this.m.setColorAt(i, col.set(rnd(i + seed) > 0.5 ? colA : colB)); }
  update(dt, x, y, z, pow, size = 0.3) {
    for (let i = 0; i < this.n; i++) { const a = rnd(i * 3 + this.seed) * 6.28, r = (0.3 + rnd(i * 5 + this.seed)) * pow, vy = (1 + rnd(i * 7 + this.seed) * 1.5) * pow * 1.6; const py = y + vy * dt - 4.9 * dt * dt * 2;
      if (dt <= 0 || py < y - 0.6) D.scale.set(0, 0, 0); else { D.position.set(x + Math.cos(a) * r * dt, py, z + Math.sin(a) * r * dt); const s = size * (0.6 + rnd(i + 9)); D.scale.set(s, s, s); D.rotation.set(dt * 3 * rnd(i), dt * 4, 0); }
      D.updateMatrix(); this.m.setMatrixAt(i, D.matrix); }
    this.m.instanceMatrix.needsUpdate = true;
  }
}
class Confetti {
  constructor(parent, n = 220) { this.n = n; const g = new THREE.PlaneGeometry(1, 1); this.m = new THREE.InstancedMesh(g, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }), n); this.m.frustumCulled = false; parent.add(this.m); const cs = ['#ff4f6a', '#ffd21f', '#3fb6ff', '#5fd97a', '#ff8a1f', '#c77dff', '#ffffff']; for (let i = 0; i < n; i++) this.m.setColorAt(i, col.set(cs[i % cs.length])); }
  update(t, cx, top, cz, wx, wz, span = 8) {
    for (let i = 0; i < this.n; i++) { const d = t * (1.6 + rnd(i) * 1.6) - rnd(i + 50) * span * 0.6; if (t <= 0 || d < 0) D.scale.set(0, 0, 0); else { D.position.set(cx + (rnd(i + 1) - 0.5) * wx + Math.sin(t * 2 + i) * 0.25, top - (d % span), cz + (rnd(i + 2) - 0.5) * wz); D.scale.set(0.13, 0.08, 1); D.rotation.set(t * 5 * rnd(i + 3) + i, t * 4 * rnd(i + 4), i); }
      D.updateMatrix(); this.m.setMatrixAt(i, D.matrix); }
    this.m.instanceMatrix.needsUpdate = true;
  }
}
const glowTex = canvasTex(128, 128, (x) => { const g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 128, 128); });
function glow(parent, color, size) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); s.scale.set(size, size, 1); parent.add(s); return s; }
function disc(parent, r, color, x, y, z) { const m = new THREE.Mesh(new THREE.CircleGeometry(r, 40), new THREE.MeshBasicMaterial({ color, fog: false })); m.position.set(x, y, z); parent.add(m); return m; }
function palm(p, x, z, h = 3) { B(p, 0.3, h, 0.3, '#8a5a2b', x, 0, z); for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { B(p, 1.2, 0.2, 0.5, '#3f9a4f', x + dx * 0.7, h - 0.1, z + dz * 0.7).rotation.y = dz ? 1.57 : 0; B(p, 0.6, 0.2, 0.4, '#2f7f3f', x + dx * 1.4, h - 0.35, z + dz * 1.4).rotation.y = dz ? 1.57 : 0; } B(p, 0.6, 0.3, 0.6, '#3f9a4f', x, h, z); }
function house(p, x, z, w, h, d, c, door = 1) { B(p, w, h, d, c, x, 0, z); B(p, w + 0.3, 0.25, d + 0.3, '#b08a5a', x, h, z); if (door) { B(p, 0.7, 1.5, 0.1, '#5a3a22', x - w * 0.15, 0, z + d / 2); B(p, 0.5, 0.5, 0.1, '#3a2a3a', x + w * 0.25, h * 0.55, z + d / 2); } }

// ---------- SET: bathroom ----------
{
  const s = mk('bath'), w = s.w, tl = tiles('#bfe6ee', '#8fc7d6', 4, 5, 3), fl = tiles('#f2ecdf', '#cfc4ae', 4, 5, 4);
  B(w, 7, 0.1, 6, fl, 0, -0.1, 0.5); B(w, 7, 4.2, 0.2, tl, 0, 0, -1.7); B(w, 0.2, 4.2, 6, tl, 2.4, 0, 0.5); B(w, 0.2, 4.2, 6, tl, -2.4, 0, 0.5);
  B(w, 0.1, 2.2, 1.0, '#a9713f', 2.28, 0, 0.6); B(w, 0.08, 0.12, 0.12, '#ffd21f', 2.2, 1.0, 0.25);
  B(w, 1.5, 1.5, 0.12, '#ffffff', -0.2, 1.75, -1.6); B(w, 1.26, 1.26, 0.16, MB('#16224a'), -0.2, 1.87, -1.58);
  disc(w, 0.36, '#fff4b8', -0.05, 2.62, -1.49); B(w, 0.06, 1.26, 0.2, '#ffffff', -0.2, 1.87, -1.56); B(w, 1.26, 0.06, 0.2, '#ffffff', -0.2, 2.47, -1.56);
  // tub
  const tw = '#ffffff'; B(w, 2.5, 0.12, 1.3, tw, 0, 0.1, 0); B(w, 2.5, 0.68, 0.12, tw, 0, 0.1, 0.59); B(w, 2.5, 0.68, 0.12, tw, 0, 0.1, -0.59); B(w, 0.12, 0.68, 1.3, tw, -1.19, 0.1, 0); B(w, 0.12, 0.68, 1.3, tw, 1.19, 0.1, 0);
  B(w, 2.6, 0.08, 0.2, '#f0f4f8', 0, 0.78, 0.6); B(w, 2.6, 0.08, 0.2, '#f0f4f8', 0, 0.78, -0.6);
  for (const [x, z] of [[-1, 0.5], [1, 0.5], [-1, -0.5], [1, -0.5]]) B(w, 0.18, 0.1, 0.18, '#e0b040', x, 0, z);
  B(w, 2.26, 0.5, 1.06, '#9fd8f0', 0, 0.15, 0); B(w, 0.12, 0.5, 0.12, '#b8c0c8', -1.05, 0.86, -0.45); B(w, 0.3, 0.1, 0.12, '#b8c0c8', -0.93, 1.3, -0.45);
  B(w, 1.2, 0.04, 0.8, '#ff9fb2', 0.3, 0, 1.6);
  const foam = []; for (let i = 0; i < 11; i++) for (let j = 0; j < 5; j++) { const m = B(w, 0.21, 0.21, 0.21, '#ffffff', -1.03 + i * 0.206, 0.55, -0.42 + j * 0.21); foam.push(m); }
  const duck = makeDuck(w); const bub = []; for (let i = 0; i < 8; i++) bub.push(glow(s.o, 0xffffff, 0.12));
  const girl = new Actor('girl', 1.1, s.o), boy = new Actor('boy', 1.1, s.o);
  const CK = [[0, 0.1, 2.6, 2.6, -0.1, 2.5, -1.6, 34], [2.4, 0, 1.9, 4.4, 0, 1.25, 0, 42], [7, 0.1, 1.7, 3.8, 0.1, 1.2, 0, 42], [8.6, 0.5, 1.5, 2.9, 0.42, 1.15, 0, 40], [12.3, 0.62, 1.45, 2.5, 0.48, 1.15, 0, 40]];
  s.update = (f, T) => {
    const t = T; look('#0f1a3a', '#22305a', '#22305a', 40, 200, 1.05, '#fff0d8', 1.3, 2, 5, 4, 0xffffff, 1);
    setCam(K(CK, t), f);
    foam.forEach((m, i) => { m.position.y = 0.66 + 0.05 * Math.sin(t * 2 + i * 1.7) + 0.06 * rnd(i); });
    const sp = ss(4.7, 5.6, t) - ss(6.2, 6.8, t); // girl pushes the fish
    duck.position.set(0.0 + Math.sin(t * 0.9) * 0.12 + sp * 0.1, 0.84 + 0.03 * Math.sin(t * 3) + sp * 0.12, 0.3); duck.rotation.set(0, t * 0.6, Math.sin(t * 3) * 0.15);
    bub.forEach((b, i) => { const u = (t * 0.3 + rnd(i)) % 1; b.position.set(-0.9 + rnd(i + 4) * 1.8, 0.9 + u * 1.3, 0.1); b.material.opacity = 0.5 * (1 - u); });
    const u = girl.unit, y0 = 0.8 - (466 - 338) * u;
    const ask = t > 8.6 && t < 11.9;
    girl.put(f, -0.5, y0 + 0.02 * Math.sin(t * 3), 0, { legs: 'none', bath: 1, arms: t > 2.3 && t < 7 ? 'cheer' : 'down', w: Math.round(Math.sin(t * 7) * 2) / 2, mouth: t < 7 ? 'laugh' : 'smile', look: t > 7.4 ? 0.9 : 0.5, lookY: t < 7 ? 0.6 : 0 }, { blob: false });
    boy.put(f, 0.5, y0 + 0.02 * Math.sin(t * 3 + 1), 0, { legs: 'none', bath: 1, arms: ask ? 'talk' : 'down', w: Math.round(Math.sin(t * 6)), mouth: ask ? talk(f) : (t > 7.2 ? 'o' : 'smile'), look: t > 7.2 ? 1 : -0.6, lookY: t < 7.2 ? 0.6 : -0.2, tilt: t > 7.2 ? 0.08 : 0 }, { blob: false });
  };
}
// ---------- SET: bedroom ----------
{
  const s = mk('bed'), w = s.w;
  B(w, 8, 0.1, 7, '#b9824f', 0, -0.1, 0.5); B(w, 8, 4.4, 0.2, '#f1d7ae', 0, 0, -2.1); B(w, 0.2, 4.4, 7, '#ecd0a4', -2.6, 0, 0.5); B(w, 0.2, 4.4, 7, '#ecd0a4', 2.9, 0, 0.5); B(w, 8, 0.25, 0.3, '#ffffff', 0, 0, -1.95);
  B(w, 1.3, 1.3, 0.1, '#ffffff', 1.6, 2.0, -2.0); const glass = B(w, 1.1, 1.1, 0.14, MB('#16224a'), 1.6, 2.1, -1.98); disc(w, 0.3, '#fff4b8', 1.75, 2.85, -1.9); B(w, 0.05, 1.1, 0.18, '#fff', 1.6, 2.1, -1.97);
  // bed (x -1.15..0.25)
  const bx = -0.45; B(w, 1.5, 0.35, 2.1, '#8a5a2b', bx, 0, -0.9); B(w, 1.4, 0.22, 2.0, '#ffffff', bx, 0.35, -0.9); B(w, 1.5, 1.25, 0.12, '#7a4a26', bx, 0, -1.98);
  B(w, 1.46, 0.16, 1.35, '#4f8fd9', bx, 0.55, -0.55); B(w, 1.46, 0.3, 0.28, '#6fa8e8', bx, 0.55, -1.12); B(w, 1.46, 0.06, 0.2, '#ffffff', bx, 0.85, -1.12);
  B(w, 0.56, 0.16, 0.4, '#ffffff', bx - 0.36, 0.57, -1.65); B(w, 0.56, 0.16, 0.4, '#ffffff', bx + 0.36, 0.57, -1.65);
  for (let i = 0; i < 5; i++) B(w, 0.14, 0.02, 0.14, '#ffd21f', bx - 0.5 + i * 0.25, 0.71, -0.3 - (i % 2) * 0.4);
  // table + lamp
  B(w, 0.42, 0.7, 0.4, '#a9713f', 0.52, 0, -1.7); B(w, 0.1, 0.28, 0.1, '#e0b040', 0.44, 0.7, -1.7); const shade = B(w, 0.3, 0.26, 0.3, MB('#fff0a8'), 0.44, 0.98, -1.7); const lg = glow(s.o, 0xffc060, 2.6); lg.position.set(0.44, 1.1, -1.5);
  const duck = makeDuck(w); duck.position.set(0.62, 0.77, -1.6); duck.scale.setScalar(0.9);
  // chair
  const cx = 1.05, cz = -0.35, gr = '#5f9a6e'; B(w, 0.9, 0.5, 0.8, gr, cx, 0, cz); B(w, 0.9, 1.3, 0.2, '#4f8a5e', cx, 0, cz - 0.45); B(w, 0.16, 0.72, 0.8, '#4f8a5e', cx - 0.5, 0, cz); B(w, 0.16, 0.72, 0.8, '#4f8a5e', cx + 0.5, 0, cz); B(w, 0.5, 0.22, 0.4, '#8a5a2b', cx, 0, cz + 0.62);
  B(w, 1.7, 0.03, 1.1, '#c0504d', -0.2, 0, 1.0); B(w, 1.4, 0.035, 0.8, '#e08a6a', -0.2, 0, 1.0);
  // book
  const page = (kind) => texMat(256, 340, (x) => { x.fillStyle = '#fbf3dc'; x.fillRect(0, 0, 256, 340); x.fillStyle = '#b9a98a'; if (kind) { for (let i = 0; i < 9; i++) x.fillRect(24, 40 + i * 30, 208 - (i % 3) * 30, 9); } else { x.fillStyle = '#9fd0f5'; x.fillRect(24, 30, 208, 150); x.fillStyle = '#ffe58a'; x.beginPath(); x.moveTo(128, 30); x.lineTo(90, 180); x.lineTo(166, 180); x.fill(); x.fillStyle = '#e2c98f'; x.fillRect(24, 140, 208, 40); x.fillStyle = '#e8d3a8'; x.fillRect(40, 100, 60, 50); x.fillStyle = '#b9a98a'; for (let i = 0; i < 4; i++) x.fillRect(24, 210 + i * 30, 208 - i * 20, 9); } }, true);
  const book = G(w, cx, 0.92, cz + 0.2); book.rotation.x = -0.4; const bc = '#7a3b2e';
  const L = G(book), R = G(book, 0, 0, 0.07); B(L, 0.3, 0.42, 0.03, bc, -0.15, -0.21, 0); const pl = new THREE.Mesh(new THREE.PlaneGeometry(0.27, 0.38), page(0)); pl.position.set(-0.15, 0, 0.03); L.add(pl);
  B(R, 0.3, 0.42, 0.03, bc, 0.15, -0.21, -0.07); const pr = new THREE.Mesh(new THREE.PlaneGeometry(0.27, 0.38), page(1)); pr.position.set(0.15, 0, -0.04); R.add(pr); B(R, 0.14, 0.14, 0.02, '#e0b040', 0.15, -0.07, -0.1);
  const girl = new Actor('girlpj', 1.1, s.o), boy = new Actor('boypj', 1.1, s.o), vovo = new Actor('vovo', 1.5, s.o), dog = new Actor('dog', 0.55, s.o);
  const C2 = [[0, 0.15, 1.75, 5.6, 0.15, 0.95, -0.8, 45], [3, 0.3, 1.6, 4.6, 0.35, 1.0, -0.7, 45], [5.3, 0.8, 1.35, 2.6, 0.95, 0.98, -0.2, 42], [7.05, 0.9, 1.05, 0.42, 0.9, 0.93, -0.15, 32]];
  const C10 = [[0, 0.15, 2.5, 5.4, 0.15, 0.95, -0.8, 45], [4, 0.1, 2.45, 4.8, 0.1, 0.95, -0.8, 45], [7.4, 0.0, 2.4, 4.4, 0.05, 1.0, -0.8, 44]];
  s.update = (f, T, night) => {
    const u = girl.unit;
    if (!night) {
      const t = T - 12.2; look('#0f1a3a', '#22305a', '#22305a', 40, 200, 1.0, '#fff0d8', 1.25, 2, 5, 4, 0xffffff, 1); lamp.position.set(0.44, 1.2, -1.4); lamp.intensity = 2.5; lg.material.opacity = 0.3;
      setCam(K(C2, t), f); U.flash.value = ss(6.75, 7.0, t);
      const open = eout((t - 1.5) / 1.4); R.rotation.y = -Math.PI * (1 - open); book.position.y = 0.92 + 0.05 * open;
      const yk = 0.86 - (466 - 380) * u, laugh = t < 1.3, tk = t > 3.6 && t < 6.7;
      girl.put(f, -0.82, yk, -1.3, { legs: 'none', mouth: t < 1.5 ? 'o' : 'smile', look: 0.9, arms: 'down' }, { blob: false });
      boy.put(f, -0.1, yk, -1.3, { legs: 'none', mouth: 'smile', look: 0.9, eyes: t < 1 ? 'wide' : 'open' }, { blob: false });
      vovo.put(f, cx, 0.5 - 56 * vovo.unit + (laugh ? 0.02 * Math.abs(Math.sin(t * 14)) : 0), cz + 0.05, { legs: 'sit', arms: 'hold', mouth: laugh ? 'laugh' : tk ? talk(f) : 'smile', eyes: laugh ? 'closed' : 'open', look: t > 3.4 ? -0.8 : 0, lookY: t > 1.4 && t < 3.4 ? 0.8 : 0, tilt: laugh ? 0.06 * Math.sin(t * 14) : 0 }, { blob: false });
      dog.put(f, -0.2, 0.03, 1.0, { pose: 'lie', wag: Math.round(Math.sin(t * 8) * 2) / 2, eyes: 'open' }, {});
    } else {
      const t = T - 78.75; look('#0a1230', '#182448', '#182448', 40, 200, 0.5, '#9fb4ff', 0.5, 2, 5, 4, 0xc9c6e8, 1); lamp.position.set(0.44, 1.2, -1.2); lamp.intensity = 5; lg.material.opacity = 0.5 + 0.04 * Math.sin(t * 5);
      setCam(K(C10, t), f); U.flash.value = 1 - ss(0, 0.25, t);
      const cl = ss(0.3, 1.3, t); R.rotation.y = -Math.PI * cl; book.position.y = 0.97 - 0.05 * cl;
      const tk = t > 2.6 && t < 7.05, sleepy = t > 5.6, yk = 0.86 - (466 - 262) * u;
      girl.put(f, -0.82, yk, -1.3, { legs: 'none', mouth: 'smile', look: 0.6, eyes: sleepy ? 'closed' : 'open', tilt: -0.12 }, { blob: false });
      boy.put(f, -0.1, yk, -1.3, { legs: 'none', mouth: 'smile', look: 0.6, eyes: t > 6.2 ? 'closed' : 'open', tilt: 0.1 }, { blob: false });
      vovo.put(f, cx, 0.5 - 56 * vovo.unit, cz + 0.05, { legs: 'sit', arms: 'hold', mouth: tk ? talk(f) : 'smile', look: -0.8, tilt: tk ? 0.03 * Math.sin(t * 4) : 0 }, { blob: false });
      const j = clamp((t - 1.0) / 0.8), ju = ss(0, 1, j), onbed = j >= 1;
      dog.put(f, lerp(-0.2, bx + 0.1, ju), lerp(0.03, 0.73, ju) + Math.sin(j * Math.PI) * 0.6, lerp(1.0, -0.1, ju), { pose: j > 0 && !onbed ? 'stand' : 'lie', wag: Math.round(Math.sin(t * 8) * 2) / 2, eyes: t > 4 ? 'closed' : 'open', step: j * 6 }, { flip: true, blob: onbed || j === 0, bs: 1 });
    }
  };
}
// ---------- SET: the call ----------
{
  const s = mk('call'), w = s.w;
  B(w, 300, 1, 300, '#e2c98f', 0, -1, -60); for (let i = 0; i < 26; i++) B(w, 1 + rnd(i) * 2, 0.08, 1 + rnd(i + 1) * 2, i % 2 ? '#d9bd80' : '#ecd6a2', (rnd(i + 2) - 0.5) * 16, 0, 2 - rnd(i + 3) * 18);
  house(w, -1.9, -2.6, 2.6, 2.3, 2.4, '#ecd9b0'); B(w, 0.9, 0.5, 0.9, '#d9c49a', -2.4, 2.55, -2.9); for (let i = 0; i < 4; i++) B(w, 0.6, 0.05, 0.5, '#c9b088', -1.9 + i * 0.5, 0, -0.9 + i * 0.35);
  palm(w, -4.6, -1.5, 3.4); palm(w, -4, -6, 3); B(w, 0.5, 0.5, 0.5, '#b0a090', 1.6, 0, -1.2); B(w, 0.3, 0.3, 0.3, '#3f9a4f', 1.2, 0, 0.8);
  // Nineveh far away
  const n = G(w, 11, 0, -42); B(n, 30, 4, 1.5, '#c9a26b'); for (let i = 0; i < 15; i++) B(n, 1, 0.8, 1.5, '#c9a26b', -14 + i * 2, 4, 0); for (const x of [-15, -5, 5, 15]) { B(n, 3, 6.5, 3, '#b98f58', x, 0, 0); B(n, 3.6, 0.6, 3.6, '#a57c48', x, 6.5, 0); }
  for (let i = 0; i < 14; i++) { const h = 3 + rnd(i) * 6; B(n, 2 + rnd(i + 1) * 2, h, 2, ['#ecd9b0', '#d8a56a', '#e8c088', '#c98b5e'][i % 4], -13 + i * 2, 0, -4 - rnd(i + 2) * 6); if (i % 4 === 1) B(n, 1.4, 1.2, 1.4, '#3f8fd0', -13 + i * 2, h, -4 - rnd(i + 2) * 6); }
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.1, 16, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0xfff0a0, transparent: true, opacity: 0.3, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })); beam.position.set(0.2, 8, 0); s.o.add(beam);
  const bg = glow(s.o, 0xfff0a0, 3.5); const sp = []; for (let i = 0; i < 14; i++) sp.push(glow(s.o, 0xffffff, 0.14));
  const jonas = new Actor('jonas', 1.65, s.o);
  const CK = [[0, 0.3, 1.0, 4.6, 0.2, 2.1, 0, 50], [3.0, 0.2, 1.3, 5.0, 0.2, 1.7, 0, 50], [4.4, -3.4, 1.8, 7.0, 3.2, 1.6, -8, 50], [5.6, -3.0, 1.8, 6.6, 3.0, 1.6, -8, 50], [6.5, 0.3, 1.45, 3.8, 0.2, 1.2, 0, 46], [7.6, 0.45, 1.45, 3.4, 0.2, 1.22, 0, 46]];
  s.update = (f, T) => {
    const t = T - 19.2; look('#3f9be8', '#cfeaff', '#e8dcc0', 30, 160, 1.0, '#fff4d8', 1.6, 3, 6, 4); U.flash.value = 1 - ss(0, 0.3, t);
    setCam(K(CK, t), f);
    const bo = 1 - ss(5.2, 6.2, t); beam.material.opacity = (0.15 + 0.03 * Math.sin(t * 4)) * bo; beam.rotation.y = t * 0.3; bg.position.set(0.2, 0.3, 0.1); bg.material.opacity = 0.22 * bo;
    sp.forEach((g, i) => { const u = (t * 0.35 + rnd(i)) % 1; g.position.set(0.2 + Math.cos(i * 2.4 + t) * 0.6, 5 - u * 5, Math.sin(i * 2.4 + t) * 0.6); g.material.opacity = bo * Math.sin(u * 3.14); });
    const turn = ss(6.5, 6.9, t), back = turn > 0.5;
    const pose = t < 3.3 ? { lookY: -1, mouth: 'o', eyes: 'wide', arms: 'down' } : t < 5.75 ? { look: 1, lookY: -0.1, mouth: 'sad', arms: 'hip', brow: -0.5 } : { arms: 'cross', mouth: 'flat', eyes: 'closed', brow: 1, back, tilt: back ? 0 : 0.05 };
    jonas.put(f, 0.2, 0, 0, pose, { sx: Math.abs(Math.cos(turn * Math.PI)) * 0.9 + 0.1 });
  };
}
// ---------- SET: port ----------
{
  const s = mk('port'), w = s.w; const sea = makeSea(w, 48, 44, 1.5);
  B(w, 30, 1.6, 40, '#e2c98f', -21, -0.6, -8); B(w, 3, 1.3, 40, '#d9bd80', -6.5, -0.6, -8); house(w, -12, -6, 4, 3, 3, '#ecd9b0'); house(w, -15, -1, 3, 2.4, 3, '#d8a56a'); palm(w, -9, -3, 3.6);
  for (let i = 0; i < 26; i++) B(w, 0.5, 0.14, 1.7, i % 2 ? '#a9713f' : '#96622f', -7 + i * 0.52, 0.86, 0); for (let i = 0; i < 7; i++) for (const z of [-0.75, 0.75]) B(w, 0.2, 2.6, 0.2, '#6b4423', -6.6 + i * 2.1, -1.5, z);
  B(w, 0.3, 0.5, 0.3, '#6b4423', 5.9, 1.0, 0.7); B(w, 0.5, 0.5, 0.5, '#c9a26b', -2, 1.0, -0.5); B(w, 0.5, 0.45, 0.5, '#a9713f', -1.4, 1.0, -0.6);
  const sm = texMat(512, 200, (x) => { x.fillStyle = '#f4e6c8'; x.fillRect(0, 0, 512, 200); x.strokeStyle = '#6b4423'; x.lineWidth = 14; x.strokeRect(7, 7, 498, 186); x.fillStyle = '#4a2545'; x.font = 'bold 92px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('NÍNIVE', 300, 104); x.beginPath(); x.moveTo(30, 100); x.lineTo(92, 50); x.lineTo(92, 150); x.fill(); });
  for (const x of [-3.2, 4.2]) { B(w, 0.16, 2.4, 0.16, '#6b4423', x, 0.9, -0.95); const b = B(w, 1.5, 0.6, 0.08, '#f4e6c8', x, 2.7, -0.9); const p = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.6), sm); p.position.set(x, 3.0, -0.85); w.add(p); }
  const boat = makeBoat(w); const jonas = new Actor('jonas', 1.65, s.o), sl = [new Actor('sailor1', 1.65, s.o), new Actor('sailor2', 1.65, s.o), new Actor('sailor3', 1.65, s.o)];
  const CK = [[0, -4.8, 2.4, 9.5, -4.2, 1.9, 0, 50], [2.4, 3.6, 2.5, 10.5, 4.4, 1.9, 0, 50], [3.1, 5.2, 2.8, 12, 6.2, 1.9, 0, 50], [4.95, 6.6, 3.6, 16.5, 8.2, 1.8, 0, 50]];
  s.update = (f, T) => {
    const t = T - 26.7; look('#3f9be8', '#cfeaff', '#cfeaff', 40, 170, 1.0, '#fff4d8', 1.6, 3, 6, 5); setCam(K(CK, t), f);
    sea.update(t, 0.16, -30, -58, '#2f86c9', '#58b4ea');
    const dep = Math.max(0, t - 3.1), bx = 8.0 + 1.3 * dep * dep, by = 0.42 + 0.06 * Math.sin(t * 2.2), rz = 0.03 * Math.sin(t * 1.7);
    boat.g.position.set(bx, by, 0); boat.g.rotation.z = rz; boat.sail.scale.z = 0.08 + 0.1 * Math.abs(Math.sin(t * 3)) * (dep > 0 ? 1 : 0.3);
    const run = clamp((t - 0.2) / 2.2), hop = clamp((t - 2.4) / 0.5), onb = hop >= 1;
    const jx = onb ? bx - 1.6 : lerp(lerp(-7, 5.4, run), 6.4, hop), jy = onb ? by + 0.55 : 1.0 + Math.sin(hop * Math.PI) * 0.7 + (run < 1 ? Math.abs(Math.sin(t * 14)) * 0.08 : 0) - hop * 0.03;
    jonas.put(f, jx, jy, 0.25, onb ? { arms: 'hip', mouth: 'smile', look: 1, eyes: 'closed' } : { arms: hop > 0 ? 'cheer' : 'fwd', step: t * 16, mouth: 'open', look: 1, brow: 0.4 }, { rot: onb ? rz : -0.12, blob: !onb && hop === 0, by: 1.0 });
    [[-0.5, 'hold'], [1.0, 'down'], [1.8, 'point']].forEach(([x, a], i) => sl[i].put(f, bx + x, by + 0.55, 0.3 - i * 0.12, { arms: dep > 0 && i === 2 ? 'point' : a === 'point' ? 'down' : a, mouth: i === 1 && onb ? 'o' : 'smile', look: onb && dep === 0 ? -1 : 1 }, { rot: rz, blob: false }));
  };
}
// ---------- SET: open sea (storm + fish) ----------
{
  const s = mk('sea'), w = s.w; const sea = makeSea(w, 52, 60, 1.5), boat = makeBoat(w), fish = makeFish(w);
  const clouds = []; for (let i = 0; i < 16; i++) { const g = G(w, (rnd(i) - 0.5) * 70, 20 + rnd(i + 1) * 8, -30 - rnd(i + 2) * 35); const m = new THREE.MeshToonMaterial({ color: 0x555b66 }); B(g, 10 + rnd(i) * 8, 2.5, 5, m); B(g, 6, 2, 4, m, 2, 2, 0); B(g, 5, 1.6, 4, m, -4, 1.6, 0); g.userData = { x: g.position.x, m }; clouds.push(g); }
  const rg = new THREE.BufferGeometry(), RN = 700, rp = new Float32Array(RN * 6); rg.setAttribute('position', new THREE.BufferAttribute(rp, 3)); const rain = new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0xcfe0ff, transparent: true, opacity: 0.55 })); rain.frustumCulled = false; s.o.add(rain);
  const bolt = G(s.o); { let x = 0; for (let i = 0; i < 7; i++) { const nx = x + (rnd(i * 3) - 0.5) * 3; const m = new THREE.Mesh(BGEO, MB(0xffffff)); m.scale.set(0.5, 3.2, 0.3); m.position.set((x + nx) / 2, 20 - i * 3, 0); m.rotation.z = (nx - x) / 3.2; bolt.add(m); x = nx; } }
  const b1 = new Burst(w, 46, 1), b2 = new Burst(w, 70, 2), b3 = new Burst(w, 70, 3);
  const jonas = new Actor('jonas', 1.65, s.o), sl = [new Actor('sailor1', 1.65, s.o), new Actor('sailor2', 1.65, s.o), new Actor('sailor3', 1.65, s.o)];
  const LT = [32.3, 34.3, 36.7, 39.1, 41.6, 43.9];
  const C5 = [[31.6, 7, 3.2, 12, 0, 1.8, 0, 50], [35.4, -5.5, 2.6, 9.5, 0, 2.0, 0, 50], [38.2, -3.4, 2.5, 6.2, -1.0, 2.0, 0, 48], [42, -2.8, 2.3, 5.2, -1.3, 2.0, 0, 46], [44.9, -3.0, 2.4, 5.6, -1.6, 1.9, 0, 46]];
  const C6 = [[44.9, -3.4, 2.6, 7.5, -2.6, 1.4, 0.6, 48], [45.5, -5.5, 2.4, 9.5, -5, 0.8, 1.5, 48], [47.4, -4.5, 5, 17, -4.5, 1.6, 0.5, 50], [48.7, -6, 15, 21, -6, 0, 0, 50], [49.6, -6, 13, 25, -6.5, 1, 1, 52], [50.5, -5.8, 6, 33, -6.5, 5, 2, 55], [51.6, -5.8, 7, 35, -6.5, 7.5, 2, 55], [53.75, -5.8, 5, 33, -6.5, 3, 2, 55]];
  s.update = (f, T) => {
    const calm = ss(46.5, 47.6, T), clear = ss(46.5, 48.3, T), st = 1 - calm, amp = lerp(1.35, 0.14, calm);
    let fl = 0; for (const l of LT) { const d = T - l; if (d >= 0 && d < 0.2) fl = Math.max(fl, d < 0.07 || d > 0.12 ? 1 : 0.3); }
    look(lerpC('#232c3a', '#3f9be8', clear), lerpC('#4a5564', '#cfeaff', clear), lerpC('#4a5564', '#cfeaff', clear), 30, 150, lerp(0.75, 1.0, clear) + fl * 1.5, lerpC('#b8c8e8', '#fff4d8', clear), lerp(0.8, 1.6, clear) + fl * 2, 3, 6, 5, lerpC('#b9c2d6', '#ffffff', clear).lerp(new THREE.Color(1, 1, 1), fl));
    U.glow.value.setScalar(fl * 0.12);
    const six = T >= 44.9; const k = K(six ? C6 : C5, T);
    const by = wave(0, 0, T, amp) * 0.8 + 0.35, rz = (wave(1.5, 0, T, amp) - wave(-1.5, 0, T, amp)) * 0.22, rx = (wave(0, 1, T, amp) - wave(0, -1, T, amp)) * 0.2;
    if (!six) { k[2] += by * 0.6; k[5] += by * 0.8; }
    const sh = six ? ss(49.9, 50.3, T) * (1 - ss(50.6, 51.4, T)) * 0.25 + ss(52.5, 52.7, T) * (1 - ss(52.9, 53.5, T)) * 0.2 : 0.02 * st + fl * 0.04; setCam(k, f, sh);
    // fish shadow path
    const su = clamp((T - 48.2) / 1.5), sx = lerp(16, -10, su), sz = lerp(-12, 3, su), sa = six && T < 50.4 ? ss(48.2, 48.6, T) : 0;
    sea.update(T, amp, -39, -76, lerpC('#1d3550', '#2f86c9', calm), lerpC('#3a6a8a', '#58b4ea', calm), sa > 0 ? (x, z) => { const dx = (x - sx) * 0.87 + (z - sz) * 0.5, dz = -(x - sx) * 0.5 + (z - sz) * 0.87; return sa * (1 - ss(0.6, 1.1, Math.hypot(dx / 12, dz / 4.5))); } : null);
    clouds.forEach((g, i) => { g.position.x = g.userData.x + Math.sign(g.userData.x || 1) * clear * 40 + T * 0.5; g.userData.m.color.set(lerpC('#4a505c', '#ffffff', clear)); });
    rain.material.opacity = 0.55 * st; { const cx = camera.position.x, cz = camera.position.z - 8; for (let i = 0; i < RN; i++) { const x = cx + (rnd(i) - 0.5) * 30, z = cz + (rnd(i + 7) - 0.5) * 26, y = 15 - ((T * 24 + rnd(i + 3) * 16) % 16); rp.set([x, y, z, x - 0.25, y - 0.8, z], i * 6); } rg.attributes.position.needsUpdate = true; }
    bolt.visible = fl > 0; if (fl) { const i = LT.findIndex(l => T - l >= 0 && T - l < 0.2); bolt.position.set([-14, 10, -6, 16, -12, 6][i], 6, -45); }
    boat.g.position.set(0, by, 0); boat.g.rotation.set(rx, 0, rz); boat.sail.scale.z = 0.08 + 0.2 * st * Math.abs(Math.sin(T * 6));
    const onb = (x, z) => { const v = new THREE.Vector3(x, 0.55, z).applyEuler(boat.g.rotation); return [v.x, by + v.y, v.z]; };
    const fear = !six || T < 46.6, awe = T > 49.9;
    [[-0.45, 0.3], [0.85, 0.35], [1.8, 0.2]].forEach(([x, z], i) => { const p = onb(x, z); sl[i].put(f, p[0], p[1], p[2], awe ? { mouth: 'o', eyes: 'wide', look: -1, lookY: -0.6, arms: i === 1 ? 'cheer' : 'down' } : fear ? { arms: i < 2 ? 'hold' : 'cheer', w: Math.round(Math.sin(T * 9 + i)), mouth: 'o', eyes: i === 1 ? 'closed' : 'wide', look: T > 40.6 ? -1 : 0, brow: -0.6 } : { mouth: 'o', eyes: 'wide', look: -1, arms: 'down' }, { rot: rz + (fear ? 0.05 * Math.sin(T * 5 + i) : 0), blob: false }); });
    // Jonas
    const fy = T < 49.7 ? -30 : T < 51.5 ? lerp(-26, -2.5, eout((T - 49.7) / 1.8)) : lerp(-2.5, -30, ss(51.9, 53.4, T));
    const jawA = T < 51.15 ? 0.62 : lerp(0.62, 0, ss(51.15, 51.5, T));
    fish.g.visible = T > 49.6; fish.g.position.set(-10, fy, 3); fish.g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3(0, 0, 1), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0))); fish.g.rotateX(0.08 * Math.sin(T * 3)); fish.jaw(jawA); fish.swim(T);
    if (T < 44.95) { const p = onb(-1.6, 0.3), tk = T > 40.6 && T < 44.7; jonas.put(f, p[0], p[1], p[2], T < 38.1 ? { arms: 'hold', mouth: 'o', eyes: 'wide', look: 1, brow: -0.6 } : T < 40.5 ? { arms: 'cheek', mouth: 'sad', lookY: 0.7, brow: -0.8 } : { arms: 'talk', w: Math.round(Math.sin(T * 6)), mouth: tk ? talk(f) : 'flat', look: 1, brow: -0.3 }, { rot: rz, blob: false }); }
    else {
      const j = clamp((T - 44.95) / 0.33), p = onb(-1.6, 0.3), dr = ss(45.4, 48.6, T), wx = lerp(-5, -10, dr), wz = lerp(1.5, 3, dr), wy = wave(wx, wz, T, amp);
      const inm = fy + 7.2; const y = j < 1 ? lerp(p[1], wy - 0.9, j) + Math.sin(j * 3.14) * 1.6 : Math.max(wy - 0.6 + 0.06 * Math.sin(T * 4), inm);
      jonas.put(f, j < 1 ? lerp(p[0], -5, j) : wx, y, j < 1 ? lerp(p[2], 1.5, j) : wz, { arms: 'cheer', w: Math.round(Math.sin(T * 8)), mouth: T > 49.9 ? 'o' : j < 1 ? 'o' : 'flat', eyes: T > 48.7 || j < 1 ? 'wide' : 'open', lookY: T > 48.7 && T < 49.9 ? 0.9 : T >= 49.9 ? -0.8 : 0 }, { rot: j < 1 ? -j * (1 - j) * 3 : 0, blob: false, vis: T < 51.4 });
    }
    b1.update(T - 45.27, -5, 0, 1.5, 3.2, 0.32); b2.update(T - 50.25, -10, 0, 3, 9, 0.9); b3.update(T - 52.6, -10, 0, 3, 9, 0.9);
  };
}
// ---------- SET: inside the fish ----------
{
  const s = mk('belly'), w = s.w, P = ['#e88fa0', '#e07f94', '#ee9bab', '#d9778c'];
  for (let i = -5; i <= 5; i++) for (let j = -5; j <= 4; j++) B(w, 1, 1 + rnd(i * 13 + j) * 0.22, 1, P[(i * 3 + j * 5 + 40) % 3], i, -1, j);
  for (let i = -5; i <= 5; i++) for (let k = 0; k < 6; k++) { B(w, 1, 1, 1 + rnd(i * 7 + k) * 0.5, P[(i + k + 20) % 4], i, k, -4.2); }
  for (let j = -4; j <= 4; j++) for (let k = 0; k < 6; k++) { B(w, 1 + rnd(j * 5 + k) * 0.5, 1, 1, P[(j + k + 21) % 4], -4.4, k, j); B(w, 1 + rnd(j * 9 + k) * 0.5, 1, 1, P[(j + k + 22) % 4], 4.4, k, j); }
  for (let i = -5; i <= 5; i++) for (let j = -5; j <= 4; j++) B(w, 1, 1, 1, P[(i + j + 30) % 4], i, 5 + rnd(i * 3 + j) * 0.4, j);
  for (const z of [-3.2, -1.2, 0.8]) { for (const x of [-3.7, 3.7]) B(w, 0.5, 5.2, 0.5, '#c9637b', x, 0, z); B(w, 7.9, 0.5, 0.5, '#c9637b', 0, 4.7, z); }
  B(w, 1.0, 0.45, 0.8, '#d9778c', -0.4, 0.05, -0.75); B(w, 2.4, 0.06, 1.6, '#7fc4f0', 1.6, 0.14, 0.2);
  const alg = []; for (const [x, z, n] of [[-2.4, -2, 5], [-2.9, -0.6, 4], [2.6, -2.4, 6], [3.0, -1.2, 4], [1.9, -2.9, 3], [-1.6, -3, 4]]) { const a = []; for (let k = 0; k < n; k++) a.push(B(w, 0.22, 0.34, 0.22, k % 2 ? '#3fae5f' : '#2f8f4a', x, 0.15 + k * 0.34, z)); alg.push({ a, x }); }
  const fs = []; for (let i = 0; i < 6; i++) { const g = G(w); const c = ['#ff8a1f', '#ffd21f', '#5fd9c0', '#ff6f91', '#9f7fff', '#ffd21f'][i]; B(g, 0.3, 0.2, 0.1, c); B(g, 0.12, 0.26, 0.08, c, -0.2, -0.03, 0); B(g, 0.04, 0.04, 0.12, '#1a1a2a', 0.09, 0.11, 0); fs.push(g); }
  // bubble window
  const cv = document.createElement('canvas'); cv.width = cv.height = 256; const wx = cv.getContext('2d'), wt = new THREE.CanvasTexture(cv); wt.colorSpace = THREE.SRGBColorSpace;
  const win = new THREE.Mesh(new THREE.CircleGeometry(0.85, 40), new THREE.MeshBasicMaterial({ map: wt })); win.position.set(1.15, 2.95, -3.55); w.add(win);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.11, 10, 36), M('#f4b6c4')); ring.position.copy(win.position); w.add(ring); const wg = glow(s.o, 0xbfe0ff, 3.4); wg.position.set(1.15, 2.95, -3.3);
  const hc = canvasTex(128, 128, (x) => { x.fillStyle = '#fff'; x.shadowColor = '#ffd0e0'; x.shadowBlur = 14; x.beginPath(); x.moveTo(64, 108); x.bezierCurveTo(10, 66, 20, 22, 64, 46); x.bezierCurveTo(108, 22, 118, 66, 64, 108); x.fill(); });
  const heart = new THREE.Sprite(new THREE.SpriteMaterial({ map: hc, color: 0xffe9a8, transparent: true, depthWrite: false })); s.o.add(heart); const hg = glow(s.o, 0xffd070, 2);
  const jonas = new Actor('jonas', 1.65, s.o);
  const CK = [[0, 0.5, 1.9, 5.8, 0.4, 1.9, -1.5, 50], [4.6, 0.3, 1.8, 4.9, 0.35, 1.85, -1.5, 50], [7.6, 0.1, 1.5, 4.2, 0.0, 1.4, -1, 48], [8.3, -0.25, 1.25, 3.3, -0.4, 1.05, -0.6, 44], [9.95, -0.3, 1.5, 3.5, -0.4, 1.7, -0.6, 44]];
  s.update = (f, T) => {
    const t = T - 53.75, cyc = clamp((t - 0.2) / 7.3) * 3, ph = cyc % 1, day = cyc >= 3 ? 1 : ph < 0.5 ? 1 : 0, dn = cyc >= 3 ? 1 : ss(0, 0.06, ph) * (1 - ss(0.47, 0.53, ph)) + ss(0.94, 1, ph);
    look('#1a0f1e', '#1a0f1e', '#3a1a2a', 6, 22, 0.42 + 0.2 * dn, '#ffd0d8', 0.35, 1, 4, 3, lerpC('#b9a0c0', '#f0d8dc', dn)); lamp.position.set(1.15, 2.6, -2.4); lamp.color.set(lerpC('#8fa8ff', '#fff0c0', dn)); lamp.intensity = 14;
    U.fade.value = ss(0, 0.3, t); setCam(K(CK, t), f);
    // window sky
    wx.fillStyle = '#' + lerpC('#101a44', '#6fc0f5', dn).getHexString(); wx.fillRect(0, 0, 256, 256); if (dn < 0.5) { wx.fillStyle = '#fff'; for (let i = 0; i < 14; i++) wx.fillRect(rnd(i) * 256, rnd(i + 5) * 256, 4, 4); }
    const hp = ph < 0.5 ? ph * 2 : (ph - 0.5) * 2, bx = lerp(-40, 296, cyc >= 3 ? 0.5 : hp), byy = 150 - Math.sin((cyc >= 3 ? 0.5 : hp) * Math.PI) * 90; wx.beginPath(); wx.arc(bx, byy, 34, 0, 7); wx.fillStyle = (cyc >= 3 || ph < 0.5) ? '#ffd84a' : '#f4f4ff'; wx.fill(); wx.lineWidth = 6; wx.strokeStyle = '#4a2545'; wx.stroke(); wt.needsUpdate = true;
    wg.material.opacity = 0.1 + 0.12 * dn; lamp.color.set(lerpC('#8fa8ff', '#fff0c0', dn));
    alg.forEach((g, i) => g.a.forEach((m, k) => { m.position.x = g.x + Math.sin(t * 1.6 + i + k * 0.5) * 0.05 * k; }));
    fs.forEach((g, i) => { const a = t * (0.5 + i * 0.12) + i * 2; g.position.set([2.2, -2.4, 1.6, -2.9, 2.9, 0.9][i] + Math.cos(a) * 0.5, [1.2, 2.2, 0.4, 0.9, 2.6, 3.9][i] + Math.sin(a * 1.3) * 0.2, [-1.5, -2.2, 0.3, -1, -2.6, -2.8][i]); g.rotation.y = Math.sin(a) > 0 ? Math.PI : 0; if (i === 2) { g.position.y = 0.3 + Math.abs(Math.sin(t * 6)) * 0.25; g.rotation.z = Math.sin(t * 12) * 0.5; } });
    const pray = t > 7.7; const pose = pray ? { legs: 'kneel', arms: 'pray', eyes: 'closed', mouth: t > 9 ? 'smile' : 'flat', nod: 8, tilt: 0.04 } : t > 4.9 ? { legs: 'sit', arms: 'cheek', mouth: 'sad', lookY: -0.6, look: 0.6, brow: -0.6 } : { legs: 'sit', arms: 'down', mouth: 'sad', look: Math.round(Math.sin(t * 1.4) * 2) / 2, lookY: -0.3, brow: -0.7 };
    if (pray) jonas.put(f, -0.4, 0.12, 0.1, pose, { bs: 1.2 }); else jonas.put(f, -0.4, 0.5 - 56 * jonas.unit, -0.5, pose, { blob: false });
    const hu = clamp((t - 8.45) / 1.5), hv = hu > 0; heart.visible = hg.visible = hv; const hy = 1.5 + eout(hu) * 1.9, hs = (0.25 + 0.3 * hu) * (1 + 0.08 * Math.sin(t * 12)); heart.position.set(-0.4 + Math.sin(hu * 5) * 0.12, hy, 0.3); heart.scale.set(hs, hs, 1); hg.position.copy(heart.position); hg.scale.setScalar(hs * 4); hg.material.opacity = 0.7; if (hv) { lamp.position.set(-0.4, hy, 0.8); lamp.color.set('#ffd890'); lamp.intensity = 10 + 20 * hu; U.glow.value.set(0.10 * hu, 0.07 * hu, 0.02 * hu); }
  };
}
// ---------- SET: beach ----------
{
  const s = mk('beach'), w = s.w; const sea = makeSea(w, 52, 50, 1.5), fish = makeFish(w);
  B(w, 90, 2, 40, '#f0deb0', 0, -2, 23.5); B(w, 90, 1.85, 1.5, '#e6d19c', 0, -2, 3.2); B(w, 90, 1.7, 1.5, '#dcc48c', 0, -2, 2.0);
  for (let i = 0; i < 20; i++) B(w, 0.3 + rnd(i) * 0.5, 0.12, 0.3 + rnd(i + 1) * 0.4, ['#ffffff', '#ffb3c8', '#c9b088'][i % 3], (rnd(i + 2) - 0.5) * 14, 0, 5 + rnd(i + 3) * 9);
  palm(w, -3.6, 9, 4); palm(w, 7.5, 5.5, 3.4); B(w, 1.4, 0.9, 1.2, '#a09488', -3.2, 0, 7.5); B(w, 0.8, 0.5, 0.8, '#b0a498', -2.4, 0, 7.9);
  const sunD = disc(w, 16, '#fff0a0', -45, 4, -170), sg = glow(s.o, 0xffc060, 120); const b1 = new Burst(w, 40, 5, '#ffffff', '#f0deb0');
  const jonas = new Actor('jonas', 1.65, s.o);
  const CK = [[0, 10, 3.2, 17, 0, 3.0, -8, 50], [1.9, 9, 2.8, 15, 0, 2.6, -1, 50], [3.5, 5, 1.9, 14, 0.3, 1.5, 5.5, 48], [5.6, 4.6, 1.9, 13.6, 0.3, 1.7, 4.5, 48]];
  s.update = (f, T) => {
    const t = T - 63.7; look('#58aef0', '#ffd9a0', '#ffd9a0', 40, 190, 1.0, '#ffe8c0', 1.5, 2, 4, -6, 0xfff2e0); U.fade.value = ss(0, 0.3, t);
    setCam(K(CK, t), f, ss(1.6, 1.9, t) * (1 - ss(1.9, 2.4, t)) * 0.08);
    sea.update(T, 0.14, -39, -73.5, '#2f86c9', '#58b4ea'); sunD.position.y = 2 + t * 1.2; sg.position.set(-45, sunD.position.y, -160); sg.material.opacity = 0.5;
    const arr = eout(t / 1.9), leave = ss(4.5, 5.6, t); fish.g.position.set(0, 0.9 - leave * 7, lerp(-55, -12.3, arr) - leave * 26); fish.g.rotation.set(-0.06 + leave * 0.25, 0, Math.sin(T * 2) * 0.02); fish.swim(T * (leave > 0 ? 2 : 1));
    fish.jaw(0.55 * (ss(1.8, 2.5, t) - ss(3.3, 3.9, t)));
    const e = clamp((t - 2.55) / 0.85), out = e > 0, land = e >= 1;
    const up = ss(3.6, 4.0, t), shake = t > 4.0 && t < 4.5, back = t > 4.55;
    const jz = lerp(-0.5, 6.5, e), jy = land ? 0 : lerp(2.2, 0, e) + Math.sin(e * Math.PI) * 1.8;
    jonas.put(f, 0.3, jy, jz, !land ? { arms: 'cheer', mouth: 'o', eyes: 'wide' } : up < 1 ? { legs: 'sit', arms: 'down', mouth: 'o', eyes: 'wide' } : back ? { back: true, arms: 'wave', w: Math.round(Math.sin(t * 14)), nod: 4 + 4 * Math.sin(t * 12) } : { arms: shake ? 'out' : 'down', mouth: 'smile', eyes: shake ? 'closed' : 'open' }, { vis: out, rot: !land ? e * 6.28 : shake ? 0.12 * Math.sin(t * 40) : 0, sy: land && up < 1 ? 1 - 0.1 * Math.sin(clamp((t - 3.4) / 0.25) * 3.14) : 1, floorU: land && up < 1 ? undefined : undefined });
    b1.update(t - 3.4, 0.3, 0, 6.5, 2.2, 0.2);
  };
}
// ---------- SET: Nineveh ----------
{
  const s = mk('nin'), w = s.w;
  B(w, 60, 1, 60, tiles('#dcbd8c', '#c9a878', 4, 20, 20), 0, -1, -5);
  B(w, 40, 5, 1.6, '#c9a26b', 0, 0, -13); for (let i = 0; i < 20; i++) B(w, 1, 0.9, 1.6, '#c9a26b', -19 + i * 2, 5, -13); B(w, 2.6, 3.4, 1.8, '#5a3a22', 0, 0, -12.95); B(w, 3.4, 0.6, 2, '#a57c48', 0, 3.4, -12.9);
  for (const x of [-9, 9]) { B(w, 3.4, 8, 3.4, '#b98f58', x, 0, -13); B(w, 4, 0.7, 4, '#a57c48', x, 8, -13); B(w, 2, 1.4, 2, '#3f8fd0', x, 8.7, -13); }
  const hs = [[-5.2, -2, 3.4, 3.6, 3.5, '#ecd9b0'], [-5.6, -6.5, 3.8, 5.2, 4, '#d8a56a'], [-4.9, 2.6, 3, 2.8, 3, '#e8c088'], [5.2, -2.4, 3.4, 4.2, 3.6, '#e8c088'], [5.7, -7, 3.8, 3.4, 4, '#ecd9b0'], [4.9, 2.4, 3, 3.2, 3, '#c98b5e'], [-2.2, -9.5, 3, 4.4, 3, '#f0deb8'], [2.6, -9.8, 3.2, 3.6, 3, '#d8a56a']];
  hs.forEach(([x, z, ww, h, d, c], i) => { house(w, x, z, ww, h, d, c, 0); const sd = x < 0 ? 1 : -1; if (Math.abs(x) > 3) { B(w, 0.1, 1.6, 0.8, '#5a3a22', x + sd * ww / 2, 0, z); B(w, 0.1, 0.6, 0.6, '#3a2a3a', x + sd * ww / 2, h * 0.6, z + 0.9); B(w, 0.9, 0.1, 1.6, ['#d94f6a', '#3f8fd0', '#3fa37a', '#f2c94c'][i % 4], x + sd * (ww / 2 + 0.45), 2.0, z); } else { B(w, 0.8, 1.6, 0.1, '#5a3a22', x, 0, z + d / 2); B(w, 0.6, 0.6, 0.1, '#3a2a3a', x + 0.9, h * 0.6, z + d / 2); } if (i % 3 === 0) B(w, 1.4, 1.1, 1.4, '#3f8fd0', x, h + 0.25, z); });
  B(w, 1.5, 0.45, 1.5, '#b0a090', 0, 0, -1.2); B(w, 1.1, 0.4, 1.1, '#c0b0a0', 0, 0.45, -1.2); palm(w, -3.2, -5.5, 4.2); palm(w, 3.4, -6, 3.8);
  for (let i = 0; i < 4; i++) B(w, 0.5, 0.6, 0.5, ['#c98b5e', '#a9713f'][i % 2], -3.2 + (i % 2) * 0.6, 0, 0.6 + i * 0.3);
  const conf = new Confetti(s.o, 260), gl = glow(s.o, 0xffd060, 30);
  const jonas = new Actor('jonas', 1.65, s.o), pp = ['nin1', 'nin2', 'nin3', 'nin4', 'nin5'].map(n => new Actor(n, 1.6 + rnd(n.charCodeAt(3)) * 0.1, s.o));
  const pos = [[-1.55, 0.2], [-0.85, 1.25], [0.85, 1.25], [1.55, 0.2], [0.05, 2.3]];
  const CK = [[0, 0, 10, 17, 0, 2.5, -5, 50], [2.3, 0, 2.7, 8.6, 0, 1.6, -0.5, 50], [7, 0.25, 2.3, 7.9, 0, 1.6, -0.5, 50], [7.5, 0.1, 2.2, 8.2, 0, 1.9, -0.5, 50], [9.5, 0, 2.6, 10, 0, 2.6, -0.5, 50]];
  s.update = (f, T) => {
    const t = T - 69.3, joy = ss(6.95, 7.3, t); look('#3f9be8', '#cfeaff', lerpC('#e8dcc0', '#ffe9b0', joy), 30, 120, 1.0 + 0.15 * joy, lerpC('#fff4d8', '#ffd870', joy), 1.6 + 0.5 * joy, 3, 6, 5, lerpC('#ffffff', '#fff0c8', joy)); U.fade.value = ss(0, 0.3, t); U.glow.value.set(0.08 * joy, 0.055 * joy, 0.01 * joy);
    setCam(K(CK, t), f);
    const tk = t > 1.2 && t < 4.4, hear = t > 4.75 && t < 6.95;
    jonas.put(f, 0, 0.85 + (joy ? Math.abs(Math.sin(t * 7)) * 0.2 : 0), -1.2, joy ? { arms: 'cheer', w: Math.round(Math.sin(t * 9)), mouth: 'laugh', eyes: 'closed' } : { arms: tk ? 'point' : 'out', mouth: tk ? talk(f) : 'smile', look: Math.round(Math.sin(t * 1.5) * 2) / 2, brow: 0.2 }, {});
    pp.forEach((a, i) => { const inn = eout((t - 0.3 - i * 0.12) / 1.6), sd = pos[i][0] < 0 ? -1 : 1, x = pos[i][0] + (1 - inn) * (i === 4 ? 0 : sd * 4), z = pos[i][1] + (i === 4 ? (1 - inn) * 4 : 0), jmp = joy ? Math.abs(Math.sin(t * 8 + i * 1.1)) * 0.45 : 0;
      a.put(f, x, jmp, z, joy ? { arms: 'cheer', w: Math.round(Math.sin(t * 10 + i)), mouth: 'laugh', eyes: i % 2 ? 'closed' : 'open', back: i === 4, lookY: -0.4 } : hear ? { arms: i % 2 ? 'pray' : 'down', mouth: 'sad', eyes: 'down', nod: 12, back: i === 4, brow: -0.7 } : { arms: 'down', step: inn < 1 ? t * 12 : 0, mouth: 'o', look: i === 4 ? 0 : -sd * 0.9, lookY: -0.4, back: i === 4 }, {}); });
    conf.update(t - 7.0, 0, 7.5, 0, 9, 6, 8); gl.position.set(0, 6, -3); gl.material.opacity = 0.35 * joy;
  };
}
// ---------- SET: yard ----------
{
  const s = mk('yard'), w = s.w;
  B(w, 60, 1, 60, '#3f9a55', 0, -1, -5); for (let i = 0; i < 30; i++) B(w, 0.5 + rnd(i), 0.06, 0.5 + rnd(i + 1), i % 2 ? '#4fae63' : '#358a4a', (rnd(i + 2) - 0.5) * 12, 0, 3 - rnd(i + 3) * 7);
  for (let i = 0; i < 24; i++) { B(w, 0.34, 1.3 + (i % 2) * 0.12, 0.1, '#f4f0e6', -5.6 + i * 0.48, 0, -3.4); } B(w, 12, 0.12, 0.08, '#e0dccf', 0, 0.9, -3.45); B(w, 12, 0.12, 0.08, '#e0dccf', 0, 0.4, -3.45);
  B(w, 0.5, 2.6, 0.5, '#7a4a26', -3.1, 0, -4.4); for (const [x, y, z, sz] of [[-3.1, 2.4, -4.4, 2.2], [-3.9, 3.2, -4.2, 1.5], [-2.4, 3.5, -4.6, 1.6], [-3.1, 4.2, -4.4, 1.5]]) B(w, sz, sz, sz, '#2f8f4a', x, y, z);
  house(w, 5.5, -7, 5, 4, 4, '#e8cfa8'); B(w, 5.6, 1.2, 4.6, '#c0504d', 5.5, 4.2, -7);
  B(w, 0.14, 3.3, 0.14, '#7a4a26', -3.0, 0, -2.6); B(w, 0.14, 3.3, 0.14, '#7a4a26', 3.0, 0, -2.6);
  const moon = disc(w, 5, '#fff4b8', 16, 46, -150), mg = glow(s.o, 0xfff0b0, 40); mg.position.set(16, 46, -145); mg.material.opacity = 0.35;
  const bulbs = []; for (let i = 0; i <= 14; i++) { const u = i / 14, x = -3 + u * 6, y = 3.25 - Math.sin(u * Math.PI) * 0.55; const c = ['#ff4f6a', '#ffd21f', '#3fb6ff', '#5fd97a', '#ff8a1f'][i % 5]; if (i < 14) { const nx = -3 + (i + 1) / 14 * 6, ny = 3.25 - Math.sin((i + 1) / 14 * Math.PI) * 0.55; const l = B(w, Math.hypot(nx - x, ny - y), 0.03, 0.03, '#3a3a3a', (x + nx) / 2, (y + ny) / 2, -2.6); l.rotation.z = Math.atan2(ny - y, nx - x); } const b = B(w, 0.16, 0.16, 0.16, MB(c), x, y - 0.2, -2.6), g = glow(s.o, c, 0.9); g.position.set(x, y - 0.1, -2.5); bulbs.push({ b, g }); }
  // like button
  const like = G(w, -1.05, 4.05, -0.6); B(like, 1.1, 1.1, 0.3, '#3b82f6', 0, -0.55, 0); B(like, 0.42, 0.4, 0.12, '#ffffff', 0.06, -0.3, 0.2); B(like, 0.16, 0.42, 0.12, '#ffffff', -0.26, -0.3, 0.2); const th = B(like, 0.17, 0.36, 0.12, '#ffffff', 0.02, 0.05, 0.2); th.rotation.z = -0.25;
  // subscribe
  const subT = texMat(512, 150, (x) => { x.fillStyle = '#e62117'; x.fillRect(0, 0, 512, 150); x.fillStyle = '#fff'; x.font = 'bold 76px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('INSCREVA-SE', 256, 80); }, true);
  const sub = G(w, 0.25, 2.95, -0.6); B(sub, 2.15, 0.64, 0.34, '#e62117', 0, -0.32, 0); B(sub, 2.15, 0.1, 0.36, '#a5140c', 0, -0.36, 0); const sp = new THREE.Mesh(new THREE.PlaneGeometry(2.05, 0.6), subT); sp.position.z = 0.175; sub.add(sp);
  const bell = G(w, 1.2, 4.35, -0.6); B(bell, 0.5, 0.5, 0.26, '#ffd21f', 0, -0.62, 0); B(bell, 0.36, 0.2, 0.26, '#ffd21f', 0, -0.14, 0); B(bell, 0.72, 0.14, 0.28, '#ffd21f', 0, -0.74, 0); B(bell, 0.16, 0.14, 0.2, '#e0a020', 0, -0.9, 0); B(bell, 0.12, 0.1, 0.2, '#e0a020', 0, 0.06, 0);
  const conf = new Confetti(s.o, 240), bp = new Burst(w, 24, 8, '#ffffff', '#ffd21f');
  const girl = new Actor('girl', 1.1, s.o), boy = new Actor('boy', 1.1, s.o), vovo = new Actor('vovo', 1.5, s.o), dog = new Actor('dog', 0.55, s.o);
  const CK = [[0, 0, 1.6, 6.4, 0, 1.3, 0, 50], [2.8, 0, 2.0, 7.6, 0, 2.2, 0, 50], [7.4, 0, 2.1, 8.0, 0, 2.35, 0, 50]];
  s.update = (f, T) => {
    const t = T - 86.1; look('#0a1230', '#1c2c5c', '#1c2c5c', 30, 160, 0.75, '#aebcff', 0.8, -3, 6, 4, 0xd6d6f4, 1); U.fade.value = ss(0, 0.3, t) * (1 - ss(7.1, 7.37, t) * 0.0);
    lamp.position.set(0, 2.6, 0.5); lamp.color.set('#ffd090'); lamp.intensity = 12; setCam(K(CK, t), f);
    bulbs.forEach(({ b, g }, i) => { const on = 0.6 + 0.4 * Math.sin(t * 6 + i * 2.1); g.material.opacity = 0.5 * on; });
    const jp = (ph, h) => Math.abs(Math.sin(t * 6.5 + ph)) * h, ch = i => ({ arms: 'cheer', w: Math.round(Math.sin(t * 9 + i)), mouth: 'laugh', eyes: Math.sin(t * 2 + i) > 0.3 ? 'closed' : 'open' });
    girl.put(f, -1.05, jp(0, 0.4), 0, ch(0)); boy.put(f, -0.3, jp(1, 0.42), 0.15, ch(1)); vovo.put(f, 0.55, jp(2, 0.2), -0.1, { ...ch(2), arms: t > 3 && t < 4.6 ? 'pointL' : 'wave', w: Math.round(Math.sin(t * 9)) });
    const lk = spring((t - 3.15) / 0.6); like.scale.setScalar(Math.max(0.001, lk)); like.rotation.z = 0.25 * Math.sin((t - 3.15) * 9) * Math.exp(-(t - 3.15) * 2.5) * (t > 3.15 ? 1 : 0); like.position.y = 4.05 + 0.06 * Math.sin(t * 3);
    const drop = clamp((t - 4.2) / 0.75), bounce = drop >= 1 ? Math.exp(-(t - 4.95) * 6) * Math.sin((t - 4.95) * 18) * 0.15 : 0, pr = t - 5.55, press = pr > 0 ? Math.exp(-pr * 5) * Math.cos(pr * 16) : 0;
    sub.visible = t > 4.2; sub.position.y = lerp(9, 2.95, drop * drop) + bounce + (pr > 0 ? 0.14 * press : 0); sub.scale.set(1 + 0.08 * press * (pr > 0 ? 1 : 0), 1 - 0.22 * Math.max(0, press) * (pr > 0 ? 1 : 0), 1);
    const dj = clamp((t - 5.15) / 0.8), dx = lerp(1.5, 0.35, ss(4.6, 5.2, t)), dy = dj > 0 && dj < 1 ? Math.sin(dj * Math.PI) * 1.72 : jp(3, 0.18);
    dog.put(f, dx, dy, 0.9, { pose: 'stand', wag: Math.round(Math.sin(t * 12) * 2) / 2, mouth: 'open', step: t < 5.15 ? t * 12 : 0, head: dj > 0 && dj < 1 ? -14 : 0 }, { flip: t < 5.2, rot: dj > 0 && dj < 1 ? (0.5 - dj) * -1.2 : 0, by: 0 });
    const bl = spring((t - 5.7) / 0.5); bell.scale.setScalar(Math.max(0.001, bl)); bell.rotation.z = t > 5.7 ? 0.5 * Math.sin((t - 5.7) * 14) * Math.exp(-(t - 5.7) * 1.4) : 0;
    bp.update(t - 5.55, 0.3, 2.5, -0.3, 2.4, 0.14); conf.update(t - 3.15, 0, 7, 0.3, 7, 3, 8);
  };
}

// ---------- timeline ----------
const SC = [[0, 'bath'], [366, 'bed'], [576, 'call'], [801, 'port'], [948, 'sea'], [1612, 'belly'], [1911, 'beach'], [2079, 'nin'], [2362, 'bed', 1], [2583, 'yard'], [2804, '']];
export const TOTAL = 2804;
window.renderFrame = (f) => {
  let i = 0; while (f >= SC[i + 1][0]) i++; const [a, name, arg] = SC[i], b = SC[i + 1][0];
  for (const k in sets) sets[k].w.visible = sets[k].o.visible = k === name;
  U.flash.value = 0; U.fade.value = 1; U.time.value = f / FPS; lamp.color.set('#ffc070'); camera.near = 0.3; camera.far = 400;
  sets[name].update(f, f / FPS, arg);
  // short dips at hard cuts (except book flashes)
  const noDip = [576, 2362]; const din = f - a, dout = b - 1 - f; let fd = 1; if (!noDip.includes(a) && a > 0) fd = Math.min(fd, (din + 1) / 4); if (!noDip.includes(b) && b < TOTAL) fd = Math.min(fd, (dout + 1) / 4); if (b === TOTAL) fd = Math.min(fd, (dout + 1) / 10);
  U.fade.value *= clamp(fd);
  draw();
};
window.ready = true;
