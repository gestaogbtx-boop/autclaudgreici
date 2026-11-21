import { THREE, renderer, world, over, camera, hemi, sun, lamp, clamp, lerp, ss, eout, spring, rnd, M, MB, B, G, canvasTex, texMat, tiles, Actor, Card, U, draw, K, setCam, look, lerpC, tint } from './engine.js';
import { drawAnimal, ANIMALS } from './chars.js';

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

// ---------- Noah-specific builders ----------
const q8 = v => Math.round(v * 4 / Math.PI) * Math.PI / 4;
const GREY = ['#aab0b8', '#7f8794', '#f4f4f6', '#ff8a2a'], PUP = ['#c98a4b', '#8a5a2b', '#f1dcb8', '#3f8fd0'];
let critN = 0;
class Crit {
  constructor(kind, parent, scale = 1) { const [cw, ch, floor, h, span] = ANIMALS[kind]; this.kind = kind; this.unit = h * scale / span; this.floor = floor; this.ch = ch; this.card = new Card(cw * this.unit, ch * this.unit, cw, ch, parent); this.seed = ++critN; }
  put(f, x, y, z, pose = {}, o = {}) {
    const p = { ...pose }; if (p.step !== undefined) p.step = q8(p.step); if (!p.sleep && (f + this.seed * 29) % 127 < 4) p.blink = 1;
    this.card.draw(JSON.stringify(p), c => drawAnimal(c, this.kind, p)); const m = this.card.mesh; m.visible = o.vis !== false;
    const sy = (o.sy ?? 1) * (1 + 0.012 * Math.sin(f * 0.13 + this.seed)); m.scale.set((o.flip ? -1 : 1) * (o.sx ?? 1), sy, 1);
    m.position.set(x, y - (this.ch - this.floor) * this.unit * sy, z); m.rotation.set(0, Math.atan2(camera.position.x - x, camera.position.z - z), 0); m.rotateZ(o.rot || 0); m.material.color.copy(tint);
  }
  hide() { this.card.mesh.visible = false; }
}
function makeBook(parent) {
  const page = (kind) => texMat(256, 340, (x) => { x.fillStyle = '#fbf3dc'; x.fillRect(0, 0, 256, 340); x.fillStyle = '#b9a98a'; if (kind) { for (let i = 0; i < 9; i++) x.fillRect(24, 40 + i * 30, 208 - (i % 3) * 30, 9); } else { x.fillStyle = '#9fd0f5'; x.fillRect(24, 30, 208, 150); x.fillStyle = '#3f86c9'; x.fillRect(24, 140, 208, 40); x.fillStyle = '#a9713f'; x.fillRect(60, 110, 130, 34); x.fillRect(90, 84, 70, 28); x.fillStyle = '#b9a98a'; for (let i = 0; i < 4; i++) x.fillRect(24, 210 + i * 30, 208 - i * 20, 9); } }, true);
  const book = G(parent), bc = '#7a3b2e', L = G(book), R = G(book, 0, 0, 0.07); B(L, 0.3, 0.42, 0.03, bc, -0.15, -0.21, 0); const pl = new THREE.Mesh(new THREE.PlaneGeometry(0.27, 0.38), page(0)); pl.position.set(-0.15, 0, 0.03); L.add(pl);
  B(R, 0.3, 0.42, 0.03, bc, 0.15, -0.21, -0.07); const pr = new THREE.Mesh(new THREE.PlaneGeometry(0.27, 0.38), page(1)); pr.position.set(0.15, 0, -0.04); R.add(pr); B(R, 0.14, 0.14, 0.02, '#e0b040', 0.15, -0.07, -0.1);
  return { g: book, open(u) { R.rotation.y = -Math.PI * (1 - u); } };
}
function tree(p, x, z, h = 3.4) { B(p, 0.45, h * 0.55, 0.45, '#7a4a26', x, 0, z); B(p, 1.9, h * 0.35, 1.9, '#2f8f4a', x, h * 0.5, z); B(p, 1.3, h * 0.25, 1.3, '#3fa85a', x, h * 0.82, z); }
function flower(p, x, z, c) { B(p, 0.05, 0.3, 0.05, '#3f9a4f', x, 0, z); return B(p, 0.16, 0.16, 0.16, c, x, 0.3, z); }
const RB = ['#ff3b3b', '#ff9a1f', '#ffe01f', '#3fd15a', '#2fa8ff', '#4a55e0', '#a04fe0'];
function makeRainbow(parent, r0, bw, seg = 30) { const g = G(parent), ps = []; RB.forEach((c, b) => { const r = r0 + (6 - b) * bw, m = MB(c, { fog: false }); for (let j = 0; j < seg; j++) { const a = Math.PI * (j + 0.5) / seg; const k = new THREE.Mesh(BGEO, m); k.scale.set(r * Math.PI / seg * 1.04, bw, bw); k.position.set(-Math.cos(a) * r, Math.sin(a) * r, 0); k.rotation.z = -(a - Math.PI / 2); k.userData = { j, sc: k.scale.clone() }; g.add(k); ps.push(k); } }); return { g, show(u) { ps.forEach(k => { const v = clamp(u * (seg + 3) - k.userData.j); k.visible = v > 0; k.scale.copy(k.userData.sc).multiplyScalar(0.3 + 0.7 * eout(v)); }); } }; }
function makeArk(parent) {
  const g = G(parent), pcs = [], Wd = ['#a9713f', '#96622f', '#b57d48'];
  const add = (w, h, d, c, x, y, z, rx = 0) => { const m = B(g, w, h, d, c, x, y, z); m.rotation.x = rx; m.userData = { p: m.position.clone(), rx }; pcs.push(m); return m; };
  for (let r = 0; r < 3; r++) for (let i = 0; i < 6; i++) add(2, 0.94, 4.4, Wd[(i + r) % 3], -5 + i * 2, 0.3 + r * 0.94, 0);
  for (const s of [-1, 1]) { add(1.2, 1.9, 3.4, Wd[1], s * 6.6, 1.2, 0); add(0.9, 1.0, 2.2, Wd[0], s * 7.5, 2.1, 0); }
  add(12, 0.5, 0.15, '#7a4a26', 0, 3.12, 2.15); add(12, 0.5, 0.15, '#7a4a26', 0, 3.12, -2.15);
  for (let r = 0; r < 2; r++) for (let i = 0; i < 4; i++) add(1.75, 1.0, 3.2, Wd[(i + r + 1) % 3], -2.625 + i * 1.75, 3.12 + r, 0);
  add(7.6, 0.3, 2.2, '#7a4a26', 0, 5.3, 0.9, 0.45); add(7.6, 0.3, 2.2, '#7a4a26', 0, 5.3, -0.9, -0.45); add(7.6, 0.3, 0.4, '#6b4423', 0, 5.75, 0);
  const fin = G(g); B(fin, 2.8, 2.6, 0.1, '#3a2416', 0, 0.3, 2.21); B(fin, 3.2, 0.25, 0.2, '#6b4423', 0, 2.9, 2.25); B(fin, 1.3, 1.1, 0.1, '#3a2416', 1.9, 3.6, 1.61); B(fin, 1.7, 0.9, 0.12, '#96622f', 1.9, 3.12, 2.12);
  const ramp = G(fin, 0, 0.3, 2.25); B(ramp, 2.8, 0.18, 3.4, '#b57d48', 0, -0.09, 1.7); for (let i = 0; i < 5; i++) B(ramp, 2.8, 0.08, 0.12, '#7a4a26', 0, 0.09, 0.5 + i * 0.65);
  const sL = G(fin, 1.25, 3.6, 1.66), sR = G(fin, 2.55, 3.6, 1.66); B(sL, 0.65, 1.1, 0.08, '#7a4a26', 0.325, 0, 0); B(sR, 0.65, 1.1, 0.08, '#7a4a26', -0.325, 0, 0);
  const N = pcs.length;
  return { g, build(u) { fin.visible = u >= 0.995; pcs.forEach((m, i) => { const v = clamp((u * (N + 5) - i) / 5), e = eout(v), p = m.userData.p; m.visible = v > 0; m.position.set(p.x + (1 - e) * (rnd(i) - 0.3) * 12, p.y + (1 - e) * (7 + rnd(i + 1) * 5), p.z + (1 - e) * (5 + rnd(i + 2) * 5)); m.rotation.set(m.userData.rx + (1 - e) * 2, (1 - e) * 4, 0); }); },
    rampA(u) { ramp.rotation.x = lerp(-Math.PI / 2, 0.09, u); }, shut(u) { sL.rotation.y = -2.3 * u; sR.rotation.y = 2.3 * u; } };
}
function makeRain(parent, n = 700) { const rg = new THREE.BufferGeometry(), rp = new Float32Array(n * 6); rg.setAttribute('position', new THREE.BufferAttribute(rp, 3)); const rain = new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0xcfe0ff, transparent: true, opacity: 0.55 })); rain.frustumCulled = false; parent.add(rain);
  return (T, amt) => { rain.visible = amt > 0.01; rain.material.opacity = 0.55 * amt; const cx = camera.position.x, cy = camera.position.y, cz = camera.position.z - 8; for (let i = 0; i < n; i++) { const x = cx + (rnd(i) - 0.5) * 34, z = cz + (rnd(i + 7) - 0.5) * 28, y = cy + 12 - ((T * 24 + rnd(i + 3) * 18) % 18); rp.set([x, y, z, x - 0.25, y - 0.8, z], i * 6); } rg.attributes.position.needsUpdate = true; }; }

// ---------- SET: living room ----------
{
  const s = mk('room'), w = s.w;
  B(w, 9, 0.1, 7, '#b9824f', 0, -0.1, 0.5); B(w, 9, 4.4, 0.2, '#e9e2d0', 0, 0, -2.1); B(w, 0.2, 4.4, 7, '#e2d9c4', -3.2, 0, 0.5); B(w, 0.2, 4.4, 7, '#e2d9c4', 3.4, 0, 0.5); B(w, 9, 0.22, 0.3, '#ffffff', 0, 0, -1.95);
  // window
  const wx0 = -1.2, cv = document.createElement('canvas'); cv.width = 256; cv.height = 224; const gx = cv.getContext('2d'), gt = new THREE.CanvasTexture(cv); gt.colorSpace = THREE.SRGBColorSpace;
  B(w, 1.95, 1.75, 0.1, '#ffffff', wx0, 0.75, -2.0); const glass = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 1.5), new THREE.MeshBasicMaterial({ map: gt })); glass.position.set(wx0, 1.62, -1.94); w.add(glass);
  B(w, 0.06, 1.5, 0.06, '#ffffff', wx0, 0.87, -1.92); B(w, 1.7, 0.06, 0.06, '#ffffff', wx0, 1.6, -1.92); B(w, 2.1, 0.08, 0.3, '#ffffff', wx0, 0.75, -1.9);
  B(w, 0.3, 1.9, 0.1, '#ff9fc0', wx0 - 1.05, 0.7, -1.88); B(w, 0.3, 1.9, 0.1, '#ff9fc0', wx0 + 1.05, 0.7, -1.88); B(w, 2.5, 0.12, 0.14, '#8a5a2b', wx0, 2.6, -1.88);
  const drops = []; for (let i = 0; i < 46; i++) { const m = new THREE.Mesh(BGEO, MB('#bfe0ff')); m.scale.set(0.05, 0.14, 0.02); w.add(m); drops.push(m); }
  // sofa
  const sx = 0.55, pk = '#ff9fc0', pd = '#f07fa8'; B(w, 2.0, 0.42, 0.85, pk, sx, 0, -1.1); B(w, 2.0, 1.05, 0.25, pd, sx, 0, -1.6); B(w, 0.25, 0.7, 0.9, pd, sx - 1.1, 0, -1.1); B(w, 0.25, 0.7, 0.9, pd, sx + 1.1, 0, -1.1); B(w, 0.4, 0.3, 0.12, '#ffe58a', sx + 0.72, 0.45, -1.4);
  // shelf
  const hx = 2.4; B(w, 1.1, 2.3, 0.1, '#7a4a26', hx, 0, -1.92); B(w, 0.08, 2.3, 0.4, '#8a5a2b', hx - 0.55, 0, -1.75); B(w, 0.08, 2.3, 0.4, '#8a5a2b', hx + 0.55, 0, -1.75); for (let k = 0; k < 5; k++) B(w, 1.1, 0.06, 0.4, '#8a5a2b', hx, k * 0.56, -1.75);
  for (let k = 0; k < 4; k++) for (let i = 0; i < 6; i++) { if (k === 3 && i === 2) continue; const bh = 0.3 + rnd(k * 7 + i) * 0.14; B(w, 0.12, bh, 0.26, ['#d94f6a', '#3f8fd0', '#3fa37a', '#f2c94c', '#7a5fd0', '#e07a3a'][(i + k * 2) % 6], hx - 0.4 + i * 0.16, 0.06 + k * 0.56, -1.72); }
  B(w, 0.9, 0.7, 0.06, '#f2c94c', 0.55, 2.0, -1.97); B(w, 0.74, 0.54, 0.08, '#9fd0f5', 0.55, 2.08, -1.96); B(w, 0.3, 0.2, 0.09, '#3fa37a', 0.45, 2.08, -1.955);
  B(w, 2.6, 0.03, 1.5, '#7fb8e0', 0.2, 0, 0.4); B(w, 2.2, 0.035, 1.1, '#bfe0f5', 0.2, 0, 0.4);
  const book = makeBook(w);
  const girl = new Actor('girl2', 1.1, s.o), boy = new Actor('boy2', 1.1, s.o), vovo = new Actor('vovo2', 1.5, s.o), dog = new Actor('dog', 0.55, s.o);
  function win(rain, bow, sunA) { gx.fillStyle = '#' + lerpC('#6f7f96', '#6fc4ff', 1 - rain).getHexString(); gx.fillRect(0, 0, 256, 224); gx.fillStyle = '#' + lerpC('#56657a', '#5fc070', 1 - rain).getHexString(); gx.fillRect(0, 176, 256, 48);
    if (sunA > 0) { gx.globalAlpha = sunA; gx.fillStyle = '#ffe66a'; gx.beginPath(); gx.arc(206, 46, 26, 0, 7); gx.fill(); gx.globalAlpha = 1; }
    if (bow > 0) { gx.globalAlpha = bow; gx.lineWidth = 9; RB.forEach((c, i) => { gx.strokeStyle = c; gx.beginPath(); gx.arc(118, 190, 132 - i * 9, Math.PI, Math.PI * (1 + bow)); gx.stroke(); }); gx.globalAlpha = 1; } gt.needsUpdate = true; }
  function rainDrops(T, amt) { drops.forEach((m, i) => { const u = (T * (1.2 + rnd(i) * 0.8) + rnd(i + 9)) % 1; m.visible = rnd(i + 20) < amt; m.position.set(wx0 - 0.8 + rnd(i + 3) * 1.6, 2.33 - u * 1.42, -1.9); }); }
  
  const C1 = [[0, -1.2, 1.7, 1.2, -1.2, 1.65, -1.9, 40], [3.2, -1.1, 1.35, 3.4, -1.15, 1.3, -1.9, 45], [7.1, -1.0, 1.3, 3.2, -1.1, 1.25, -1.9, 45], [8.9, -0.75, 1.15, 2.3, -0.85, 1.0, -1.5, 42], [13.5, -0.6, 1.15, 2.2, -0.75, 1.0, -1.5, 42]];
  const C2 = [[13.5, 1.0, 1.6, 5.2, 1.1, 1.15, -1.2, 50], [17.6, 1.2, 1.55, 4.6, 1.3, 1.15, -1.2, 50], [20.2, 0.6, 1.4, 4.0, 0.55, 1.0, -1.1, 46], [23.5, 0.58, 1.3, 3.0, 0.55, 0.95, -0.9, 44], [25.4, 0.48, 1.16, -0.3, 0.44, 0.98, -0.82, 32]];
  const C12 = [[127.1, 0.6, 1.5, 4.4, 0.55, 1.05, -1.1, 48], [130.4, 0.5, 1.5, 4.6, 0.5, 1.1, -1.1, 48], [131.8, -0.5, 1.5, 5.0, -0.45, 1.25, -1.5, 50], [134.0, -0.5, 1.5, 4.9, -0.45, 1.25, -1.5, 50], [135.2, 0.35, 1.35, 3.2, 0.5, 1.15, -1.1, 44], [141, 0.4, 1.32, 2.8, 0.52, 1.15, -1.1, 44]];
  s.update = (f, T, part) => {
    const ku = girl.unit, ks = 0.42 - 56 * ku, vs = 0.42 - 56 * vovo.unit;
    if (part === 1) { // rain at the window
      look('#5f6f86', '#8fa0b4', '#8fa0b4', 40, 200, 0.95, '#cfe0ff', 0.9, -2, 5, 4, 0xdde6f5); setCam(K(C1, T), f); win(1, 0, 0); rainDrops(T, 1); book.g.position.set(hx - 0.08, 1.95, -1.72); book.g.rotation.set(0, 0, 0); book.open(0);
      const ask = T > 8.9 && T < 12.7, tb = T > 7.2;
      girl.put(f, -1.55, 0, -1.5, { back: true, arms: 'up' }, {}); 
      boy.put(f, -0.85, 0, -1.5, tb ? { arms: ask ? 'talk' : 'down', w: Math.round(Math.sin(T * 6)), mouth: ask ? talk(f) : 'o', look: 1, lookY: -0.3 } : { back: true, arms: 'up' }, { sx: 0.2 + 0.8 * Math.abs(Math.cos(ss(7.0, 7.4, T) * Math.PI)) });
      vovo.hide(); dog.put(f, -0.1, 0.02, -0.5, { pose: 'lie', sad: 1, pal: GREY, wag: 0 }, { flip: true });
    } else if (part === 2) {
      look('#5f6f86', '#8fa0b4', '#8fa0b4', 40, 200, 1.0, '#e8ecff', 1.1, 2, 5, 4, 0xeef0fa); lamp.position.set(0.6, 2.2, 0.5); lamp.color.set('#ffd9a0'); lamp.intensity = 5;
      setCam(K(C2, T), f); U.flash.value = ss(25.3, 25.6, T); win(1, 0, 0); rainDrops(T, 1);
      const take = ss(15.9, 16.8, T), walk = ss(17.5, 19.2, T), sit = T > 19.3, vx = lerp(hx - 0.15, sx + 0.02, walk), vz = lerp(-1.2, -0.95, walk);
      const tk = (T > 21.5 && T < 22.2) || (T > 22.7 && T < 24.8), op = eout((T - 20.6) / 1.2);
      girl.put(f, sx - 0.62, ks, -1.0, { legs: 'sit', mouth: 'smile', look: sit ? 0.8 : 1, arms: 'down' }, { blob: false }); boy.put(f, sx + 0.66, ks, -1.0, { legs: 'sit', mouth: T < 15 ? 'o' : 'smile', look: sit ? -0.8 : 1 }, { blob: false });
      if (!sit) vovo.put(f, vx, 0, vz, T < 15.6 ? { mouth: 'laugh', eyes: 'closed', arms: 'hip', look: -0.8 } : walk > 0 ? { arms: 'hold', step: T * 10, look: -1, mouth: 'smile' } : { back: true, arms: 'wave', w: 0 }, {});
      else vovo.put(f, sx + 0.02, vs, -0.95, { legs: 'sit', arms: 'hold', mouth: tk ? talk(f) : 'smile', lookY: T > 20.5 && T < 21.4 ? 0.8 : 0, look: T > 21.4 ? (Math.sin(T * 1.5) > 0 ? 0.7 : -0.7) : 0 }, { blob: false });
      if (walk <= 0) { book.g.position.set(hx - 0.08, 1.95 - 0.0 * take, -1.72 + 0.35 * take); book.g.rotation.set(0, 0, 0); } else if (!sit) { book.g.position.set(vx, 0.93, vz + 0.22); book.g.rotation.set(-0.2, 0, 0); } else { book.g.position.set(sx + 0.02, 0.86 + 0.06 * op, -0.72); book.g.rotation.set(-0.4, 0, 0); }
      book.open(sit ? op : 0); dog.put(f, -0.6, 0.02, 0.2, { pose: 'lie', pal: GREY, wag: Math.round(Math.sin(T * 6) * 2) / 2 }, {});
    } else {
      const sunny = ss(127.6, 131, T); look(lerpC('#5f6f86', '#3f9be8', sunny), lerpC('#8fa0b4', '#cfeaff', sunny), '#cfeaff', 40, 200, 1.0 + 0.1 * sunny, lerpC('#e8ecff', '#fff0cc', sunny), 1.1 + 0.4 * sunny, 2, 5, 4, lerpC('#eef0fa', '#fff8ea', sunny));
      lamp.position.set(-1.2, 1.8, -1.0); lamp.color.set('#fff0b0'); lamp.intensity = 3 * sunny; setCam(K(C12, T), f); U.flash.value = 1 - ss(127.1, 127.4, T);
      win(1 - sunny, ss(130.2, 132.2, T), sunny); rainDrops(T, 1 - ss(127.5, 129.6, T));
      const cl = ss(127.4, 128.4, T); book.g.position.set(sx + 0.02, 0.92 - 0.06 * cl, -0.72); book.g.rotation.set(-0.4, 0, 0); book.open(1 - cl);
      const run = ss(130.5, 131.6, T), up = run > 0, at = run >= 1, tk = (T > 136.8 && T < 137.4) || (T > 138 && T < 140.1), wink = T > 134.5 && T < 135.7;
      const kp = (a, x0, x1, ph) => up ? a.put(f, lerp(x0, x1, run), at ? Math.abs(Math.sin(T * 7 + ph)) * 0.12 : Math.sin(run * 3.14) * 0.15, lerp(-0.7, -1.5, run), at ? { back: true, arms: 'cheer', w: Math.round(Math.sin(T * 9 + ph)) } : { step: T * 14, arms: 'fwd', look: -1, mouth: 'open' }, {}) : a.put(f, x0, ks, -1.0, { legs: 'sit', mouth: T > 129.4 ? 'o' : 'smile', look: T > 129.4 ? -1 : (ph ? -0.8 : 0.8), eyes: T > 129.4 ? 'wide' : 'open' }, { blob: false });
      kp(girl, sx - 0.62, -1.55, 0); kp(boy, sx + 0.66, -0.85, 1.3);
      vovo.put(f, sx + 0.02, vs, -0.95, { legs: 'sit', arms: 'hold', mouth: tk ? talk(f) : 'smile', eyes: wink ? 'wink' : 'open', look: T > 131 && T < 134 ? -1 : 0, tilt: wink ? 0.08 : 0 }, { blob: false });
      const dx = lerp(-0.6, -0.2, run); dog.put(f, dx, run > 0 ? Math.abs(Math.sin(T * 8)) * 0.08 : 0.02, lerp(0.2, -0.5, run), { pose: run > 0 ? 'stand' : 'lie', pal: GREY, wag: Math.round(Math.sin(T * 14) * 2) / 2, mouth: run > 0 ? 'open' : 'smile', step: run < 1 && run > 0 ? T * 12 : 0 }, { flip: true });
    }
  };
}
// ---------- SET: old village ----------
{
  const s = mk('vila'), w = s.w;
  B(w, 200, 1, 200, '#b8a888', 0, -1, -40); for (let i = 0; i < 24; i++) B(w, 1 + rnd(i) * 2, 0.06, 1 + rnd(i + 1) * 2, i % 2 ? '#ad9c7c' : '#c4b494', (rnd(i + 2) - 0.5) * 14, 0, 3 - rnd(i + 3) * 12);
  house(w, -3.6, -3.2, 3, 3, 3, '#cdbf9f'); house(w, 3.4, -3.6, 3.2, 3.6, 3, '#bda98a'); house(w, -0.2, -7, 3.4, 4.2, 3, '#c9b594'); house(w, -6.5, -7.5, 3, 3, 3, '#bda98a'); house(w, 6.5, -8, 3, 3.4, 3, '#cdbf9f');
  B(w, 0.5, 0.5, 0.5, '#8a7a5a', -2.6, 0, 1.6); B(w, 0.7, 0.4, 0.5, '#7a6a4a', 2.4, 0, 1.2);
  const cl = G(w, 0, 7.2, -3), cm = M('#6f747c'); B(cl, 7, 1.6, 3.4, cm); B(cl, 4, 1.3, 3, cm, 1.5, 1.4, 0); B(cl, 3.4, 1.1, 2.6, cm, -2.6, 1.2, 0); B(cl, 3, 1, 2.4, cm, 4.2, -0.2, 0.4);
  const c1 = B(w, 0.7, 0.7, 0.7, '#a9713f', 0, 0, 0.4), c2 = B(w, 0.7, 0.7, 0.7, '#96622f', 0, 0, 0.4), c3 = B(w, 0.5, 0.5, 0.5, '#b57d48', 0, 0, 0);
  const pp = ['p1', 'p2', 'p3'].map(n => new Actor(n, 1.62, s.o));
  const CK = [[25.6, 0, 2.6, 9.5, 0, 2.6, 0, 50], [27.6, 0, 1.8, 7.6, 0, 1.35, 0, 50], [32.8, 0.2, 1.7, 6.6, 0, 1.3, 0, 50]];
  s.update = (f, T) => {
    look('#7d858f', '#aab0b6', '#aab0b6', 25, 110, 1.1, '#dfe2ea', 1.0, -2, 6, 4, 0xeeeeee); U.flash.value = 1 - ss(25.6, 25.9, T); setCam(K(CK, T), f, T > 27.9 && T < 28.2 ? 0.03 : 0);
    cl.position.x = Math.sin(T * 0.4) * 1.2; cl.position.y = 7.2 + Math.sin(T * 0.9) * 0.15;
    const push = clamp((T - 26.0) / 1.9), hit = T > 27.9, sh = hit && T < 30.3 ? Math.sin(T * 30) * 0.03 : 0, turn = ss(30.4, 30.9, T), tb = turn > 0.5;
    const x1 = lerp(-2.6, -1.05, push) + sh, x2 = lerp(2.6, 1.05, push) + sh;
    c1.position.x = x1 + 0.75; c2.position.x = x2 - 0.75; c1.rotation.z = hit ? 0.06 * Math.sin(T * 20) * (1 - turn) : 0; c2.rotation.z = -c1.rotation.z;
    const ang = (i) => ({ arms: tb ? 'cross' : hit ? 'talk' : 'fwd', w: Math.round(Math.sin(T * 9 + i)), step: !hit ? T * 12 : 0, mouth: tb ? 'flat' : talk(f + i * 4), brow: 1, look: i ? -1 : 1, back: false, eyes: tb ? 'closed' : 'open' });
    pp[0].put(f, x1 - turn * 0.5, 0, 0.4, { ...ang(0), look: tb ? -1 : 1 }, { rot: hit && !tb ? 0.06 : 0 }); pp[1].put(f, x2 + turn * 0.5, 0, 0.4, { ...ang(1), look: tb ? 1 : -1 }, { rot: hit && !tb ? -0.06 : 0 });
    const kick = (T * 0.9) % 1; c3.position.set(0.9 + (kick < 0.3 ? kick * 1.5 : 0.45), 0.25 + (kick < 0.3 ? Math.sin(kick / 0.3 * 3.14) * 0.3 : 0), -1.6);
    pp[2].put(f, 0.1, 0, -1.6, { arms: 'cross', back: T > 29.5, mouth: 'flat', brow: 1, look: 0.6, lookY: 0.6 }, { rot: kick < 0.15 ? -0.08 : 0 });
  };
}
// ---------- SET: Noah's garden ----------
{
  const s = mk('garden'), w = s.w;
  B(w, 200, 1, 200, '#6fb86a', 0, -1, -40); for (let i = 0; i < 28; i++) B(w, 0.6 + rnd(i) * 1.4, 0.05, 0.6 + rnd(i + 1) * 1.4, i % 2 ? '#7cc476' : '#62a95e', (rnd(i + 2) - 0.5) * 14, 0, 3 - rnd(i + 3) * 12);
  house(w, -2.6, -3.4, 3, 2.5, 2.6, '#ecd9b0'); B(w, 3.4, 0.5, 3, '#c98b5e', -2.6, 2.75, -3.4); tree(w, 3.2, -4.2, 4); tree(w, -6, -6, 3.4); tree(w, 6.5, -9, 4.4);
  for (let i = 0; i < 9; i++) B(w, 0.12, 0.7, 0.12, '#f4f0e6', -1.6 + i * 0.5, 0, -1.9); B(w, 4.4, 0.08, 0.06, '#e0dccf', 0.4, 0.5, -1.9);
  B(w, 3.4, 0.08, 1.5, '#8a6a4a', 0.5, 0, 0.9); const fls = []; for (let i = 0; i < 18; i++) fls.push(flower(w, -1.0 + (i % 9) * 0.37, 0.55 + Math.floor(i / 9) * 0.6 + rnd(i) * 0.15, ['#ff5f8a', '#ffd21f', '#ff8a1f', '#c77dff', '#ffffff', '#ff3b3b'][i % 6]));
  const can = G(w); B(can, 0.26, 0.26, 0.2, '#7fa8c0'); B(can, 0.22, 0.06, 0.06, '#7fa8c0', 0.22, 0.14, 0); B(can, 0.06, 0.2, 0.06, '#5f88a0', -0.16, 0.06, 0); const dr = []; for (let i = 0; i < 8; i++) dr.push(B(w, 0.05, 0.08, 0.05, MB('#7fd0ff')));
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 2.4, 18, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0xffe9a0, transparent: true, opacity: 0.2, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })); beam.position.set(0.2, 9, -0.3); s.o.add(beam); const bg = glow(s.o, 0xffe090, 7);
  // blueprint of light
  const cells = [], rows = [[2, 11], [1, 12], [0, 13], [3, 10], [3, 10], [4, 9]]; const bpG = G(s.o, 0.3, 3.6, -2.6), bm = new THREE.MeshBasicMaterial({ color: 0xffcf3a });
  rows.forEach(([a, b], r) => { for (let x = a; x <= b; x++) { const m = new THREE.Mesh(BGEO, bm); m.position.set((x - 6.5) * 0.3, r * 0.3, 0); bpG.add(m); cells.push(m); } }); const bgl = glow(s.o, 0xfff0a0, 6);
  const noe = new Actor('noe', 1.65, s.o), fam = [new Actor('wife', 1.58, s.o), new Actor('son1', 1.65, s.o), new Actor('son2', 1.62, s.o)];
  const C4 = [[32.8, 0.8, 2.4, 8.2, 0.2, 1.8, -0.5, 50], [36.0, 0.5, 1.6, 6.0, 0.2, 1.25, -0.2, 50], [40.85, 0.3, 1.5, 5.2, 0.2, 1.25, -0.2, 48]];
  const C5 = [[40.85, 0.7, 1.35, 3.3, 0.3, 1.5, 0.3, 46], [44.2, 0.6, 1.3, 3.6, 0.3, 1.7, 0.3, 46], [47.2, 0.4, 1.0, 5.6, 0.3, 3.1, -1.5, 50], [52.9, 0.4, 0.95, 6.2, 0.3, 3.3, -1.5, 50]];
  s.update = (f, T, part) => {
    const five = part === 2, open = five ? ss(41.2, 44, T) : 0;
    look(lerpC('#7d858f', '#6fb6f0', open), lerpC('#aab0b6', '#a8d4f5', open), lerpC('#aab0b6', '#a8d4f5', open), 25, 120, 0.95 + 0.1 * open, '#fff0c8', 1.3, 2, 6, 4, lerpC('#eeeae0', '#fff6e0', open));
    setCam(K(five ? C5 : C4, T), f); if (!five) U.fade.value = ss(32.8, 33.1, T);
    beam.material.opacity = (0.07 + 0.015 * Math.sin(T * 3)) * (five ? 0.5 : 1); beam.rotation.y = T * 0.2; bg.position.set(0.2, 0.6, 0.6); bg.material.opacity = 0.14; lamp.position.set(0.2, 3, 1.5); lamp.color.set('#ffe0a0'); lamp.intensity = 6;
    fls.forEach((m, i) => { m.rotation.z = Math.sin(T * 2 + i) * 0.15; m.position.y = 0.38 + 0.02 * Math.sin(T * 3 + i); });
    const wat = !five && T < 40.2; can.visible = !five; const cx = 0.78 + Math.sin(T * 0.8) * 0.15; can.position.set(cx, 1.0, 0.5); can.rotation.z = -0.5;
    dr.forEach((m, i) => { const u = (T * 1.6 + i / 8) % 1; m.visible = wat; m.position.set(cx + 0.3 + u * 0.1, 1.05 - u * 0.75, 0.52); });
    const tk = five && T > 44.5;
    noe.put(f, 0.2, 0, 0.3, five ? { lookY: -1, mouth: T > 47.3 ? 'o' : T > 41.6 ? 'smile' : 'o', eyes: T > 47.3 ? 'wide' : 'open', arms: T > 47.3 ? 'up' : 'down' } : { arms: 'talk', w: 0, mouth: 'smile', look: 0.6, lookY: 0.5, eyes: T > 38.4 ? 'closed' : 'open' }, {});
    [[-1.15, -0.7, 'wave'], [1.3, -0.9, 'hip'], [-0.35, -1.5, 'down']].forEach(([x, z, a], i) => five ? fam[i].hide() : fam[i].put(f, x, 0, z, { arms: a, w: Math.round(Math.sin(T * 7)), mouth: 'smile', look: x < 0 ? 0.8 : -0.8 }, {}));
    const bu = five ? clamp((T - 47.3) / 4.4) : 0; bpG.visible = bgl.visible = bu > 0; cells.forEach((m, i) => { const v = spring((bu * (cells.length + 6) - i) / 6); m.visible = v > 0; m.scale.setScalar(0.24 * Math.min(1.3, v)); }); bpG.position.y = 3.6 + 0.08 * Math.sin(T * 2); bgl.position.set(0.3, 4.3, -2.8); bgl.material.opacity = 0.22 * bu;
  };
}
// ---------- SET: hill + ark ----------
{
  const s = mk('hill'), w = s.w; const sea = makeSea(w, 56, 56, 1.6), ark = makeArk(w), rainF = makeRain(s.o), bow = makeRainbow(w, 11, 0.8);
  bow.g.position.set(0, 0, -22);
  B(w, 300, 1, 300, '#6fb86a', 0, -1, -40); for (let i = 0; i < 40; i++) B(w, 1 + rnd(i) * 2.5, 0.06, 1 + rnd(i + 1) * 2.5, i % 2 ? '#7cc476' : '#62a95e', (rnd(i + 2) - 0.5) * 34, 0, 14 - rnd(i + 3) * 30);
  for (const [x, z, h] of [[-11, 6, 3.6], [-13, -2, 4], [-9.5, -7, 3.4], [11, -7, 4], [14, -3, 3.4], [-15, 9, 3.2], [9, -12, 3.6]]) tree(w, x, z, h);
  house(w, -13, 2.5, 3, 2.6, 3, '#cdbf9f'); house(w, 13.5, -9, 3, 2.8, 3, '#bda98a'); house(w, -16, -6, 3, 2.6, 3, '#c9b594');
  for (let i = 0; i < 9; i++) { const a = i * 0.7, r = 70 + rnd(i) * 30, h = 8 + rnd(i + 4) * 10; for (let k = 0; k < 3; k++) B(w, (3 - k) * 9, h / 3, (3 - k) * 9, ['#4f9a58', '#5aa863', '#68b870'][k], Math.cos(a) * r, k * h / 3 - 1, -Math.abs(Math.sin(a)) * r - 20); }
  const clouds = []; for (let i = 0; i < 14; i++) { const g = G(w, (rnd(i) - 0.5) * 80, 22 + rnd(i + 1) * 8, -25 - rnd(i + 2) * 40), m = new THREE.MeshToonMaterial({ color: 0x555b66 }); B(g, 10 + rnd(i) * 8, 2.5, 5, m); B(g, 6, 2, 4, m, 2, 2, 0); g.userData = { x: g.position.x, m }; clouds.push(g); }
  const sunD = disc(w, 6, '#ffe66a', 0, 0, -160), moonD = disc(w, 5, '#f4f4ff', 0, 0, -160);
  const peak = G(w, -22, 0, -26); for (let k = 0; k < 4; k++) B(peak, 12 - k * 3, 1.2, 10 - k * 2.5, ['#4f9a58', '#5aa863', '#68b870', '#7cc476'][k], 0, k * 1.2, 0); tree(peak, 0.5, 0, 2.6);
  // tools
  const horse = G(w, 4.6, 0, 6); B(horse, 0.12, 0.8, 0.9, '#7a4a26', -0.9, 0, 0); B(horse, 0.12, 0.8, 0.9, '#7a4a26', 0.9, 0, 0); B(horse, 2.6, 0.12, 0.5, '#b57d48', 0, 0.8, 0);
  const saw = G(w); B(saw, 0.9, 0.3, 0.04, '#c8d0d8', 0, -0.3, 0); B(saw, 0.25, 0.3, 0.08, '#d93a3a', 0.55, -0.2, 0);
  const ham = G(w); B(ham, 0.08, 0.6, 0.08, '#8a5a2b', 0, 0, 0); B(ham, 0.34, 0.18, 0.18, '#8a94a2', 0, 0.55, 0);
  const dust = new Burst(w, 20, 11, '#f0d9a8', '#d9b98a');
  const cnt = new Card(1.0, 0.5, 256, 128, s.o); cnt.mesh.material.depthTest = false; cnt.mesh.renderOrder = 10;
  const noe = new Actor('noe', 1.65, s.o), fam = [new Actor('wife', 1.58, s.o), new Actor('son1', 1.65, s.o), new Actor('son2', 1.62, s.o)], pp = ['p1', 'p2', 'p3'].map(n => new Actor(n, 1.62, s.o));
  const kinds = ['sheep', 'zebra', 'lion', 'giraffe', 'elephant', 'rabbit'], crit = kinds.map(k => [new Crit(k, s.o, k === 'lion' ? 1.45 : k === 'rabbit' ? 1.3 : 1), new Crit(k, s.o, k === 'lion' ? 1.3 : k === 'rabbit' ? 1.3 : 1)]), pups = [new Actor('dog', 0.42, s.o), new Actor('dog', 0.42, s.o)], dove = new Crit('dove', s.o, 1.5);
  const TE = [72.0, 73.5, 75.5, 77.0, 78.5, 80.4, 82.2], LEN = [1.2, 1.9, 1.8, 2.2, 3.4, 0.7, 0.7];
  const C6 = [[52.9, 9.5, 3.6, 17.5, 1, 2.6, 2, 50], [60.2, 8, 3, 15.5, 1.2, 2.4, 2.5, 50], [60.6, -3.0, 1.9, 13, -5.6, 1.35, 7.4, 46], [62.6, -3.4, 1.8, 12.4, -5.6, 1.35, 7.4, 46], [63.0, 5.4, 1.7, 9.6, 3.9, 1.3, 5.6, 44], [64.7, 5.2, 1.65, 9.0, 3.9, 1.3, 5.6, 44]];
  const C7 = [[64.7, 11, 2, 18, 0, 3.2, 0, 52], [69.3, 9.5, 2.4, 16.5, 1, 2.6, 2.5, 52], [70.4, 7.6, 2.7, 15.6, 1.3, 1.9, 4.2, 52], [80.0, 7.0, 2.6, 15.0, 1.2, 1.9, 4.2, 52], [80.8, 3.2, 1.0, 8.8, 0.9, 0.6, 4.4, 44], [84.4, 2.8, 1.0, 8.2, 0.7, 0.65, 4.2, 44]];
  const C8 = [[84.4, 7, 2.4, 14, 0, 2.4, 2.5, 50], [86.2, 11, 4.5, 22, 0, 3, 0, 50], [91.3, 13, 8, 28, 0, 4, 0, 50], [93.4, 14, 8.6, 30, 0, 4, 0, 50]];
  const C10 = [[99.9, 12, 5, 24, 0, 3.5, 0, 50], [103.2, 5.2, 4.3, 10, 1.9, 4.0, 1.9, 46], [105.0, 4.8, 4.3, 9.4, 1.9, 4.1, 1.9, 46], [106.2, 6, 4.4, 12, 6, 5.5, -4, 50], [107.6, 6, 4.4, 12, 6, 5.5, -4, 50], [109.6, 4.8, 4.3, 9.2, 2.0, 4.2, 1.9, 44], [110.9, 4.6, 4.3, 8.6, 2.0, 4.2, 1.9, 44], [112.4, 9, 6, 20, -6, 3, -6, 50], [114.5, 11, 6.5, 23, -8, 2.8, -8, 50]];
  const C11 = [[114.5, 1.5, 1.4, 9, 0.2, 1.5, 3, 52], [117.3, 1.0, 1.4, 9.4, 0.2, 1.8, 2, 52], [119.6, 0.5, 1.5, 16.2, 0, 8.6, -6, 56], [127.1, 0.2, 1.6, 17.6, 0, 9.2, -6, 56]];
  s.update = (f, T, part) => {
    [noe, ...fam, ...pp, ...pups].forEach(a => a.hide()); crit.flat().forEach(c => c.hide()); dove.hide(); cnt.mesh.visible = false; saw.visible = ham.visible = horse.visible = part === 6; bow.g.visible = part === 11; peak.visible = part === 10; sunD.visible = moonD.visible = false;
    let level = -5, rain = 0, dark = 0, arkY = 0;
    if (part === 8) { rain = ss(85.1, 86.2, T); dark = ss(84.6, 86.2, T); level = lerp(-5, 5, ss(86.0, 91.4, T)); }
    if (part === 10) { level = 5; rain = 1 - ss(100.6, 102.4, T); dark = 1 - ss(100.6, 104.5, T); }
    arkY = Math.max(0, level - 1.0) + (level > 0.6 ? 0.1 * Math.sin(T * 1.6) : 0); const flick = part === 8 && T > 87.4 && T < 90.9 ? 0.5 + 0.5 * Math.sin((T - 87.4) * 15.7) : 0;
    const sunset = 0;
    look(lerpC('#3f9be8', '#232c3a', dark).lerp(new THREE.Color('#4a5f8a'), flick * 0.5), lerpC('#cfeaff', '#4a5564', dark), lerpC('#cfeaff', '#4a5564', dark), 40, 190, lerp(1.0, 0.75, dark) + flick * 0.15, lerpC('#fff4d8', '#b8c8e8', dark), lerp(1.6, 0.8, dark), 3, 6, 5, lerpC('#ffffff', '#b9c2d6', dark));
    clouds.forEach(g => { g.visible = dark > 0.02; g.position.x = g.userData.x + T * 0.4 + Math.sign(g.userData.x || 1) * (1 - dark) * 50; g.userData.m.color.set(lerpC('#ffffff', '#4a505c', dark)); });
    const k = K({ 6: C6, 7: C7, 8: C8, 10: C10, 11: C11 }[part], T); if (part === 8) { k[2] += Math.max(0, level) * 0.8; k[5] += arkY; } if (part === 10) { k[2] += arkY; k[5] += arkY; }
    setCam(k, f, part === 8 ? 0.015 * rain : 0); rainF(T, rain);
    sea.m.visible = level > -4.5; sea.m.position.y = level; if (sea.m.visible) sea.update(T, lerp(0.14, 0.5, rain), -45, -62, lerpC('#2f86c9', '#1d3550', dark), lerpC('#58b4ea', '#3a6a8a', dark));
    ark.g.position.y = arkY; ark.g.rotation.z = level > 0.6 ? 0.025 * Math.sin(T * 1.3) : 0; ark.build(part === 6 ? ss(53.1, 64.6, T) * 0.985 : 1); ark.rampA(part === 7 ? ss(65.2, 66.8, T) : part === 8 ? 1 - ss(84.5, 85.7, T) : part === 11 ? 1 : 0); ark.shut(part === 10 ? ss(103.4, 104.1, T) : 0);
    if (part === 6) {
      const firm = T > 62.7; saw.position.set(4.6 + Math.sin(T * 9) * 0.35, 1.25, 6); saw.rotation.z = -0.25; const hk = Math.abs(Math.sin(T * 7)); ham.position.set(3.2, 1.0, 5.6); ham.rotation.z = -1.2 + hk * 1.1;
      dust.update((T * 1.2) % 1 * 0.6, 4.3, 0.95, 6, 1.2, 0.07);
      noe.put(f, 3.9, 0, 5.6, firm ? { arms: 'up', w: 0, mouth: 'smile', brow: 0.6, eyes: 'open', look: -0.3 } : { arms: 'hold', mouth: 'smile', look: 0.4, lookY: 0.4, brow: 0.2 }, { rot: firm ? 0 : 0.04 * Math.sin(T * 7) });
      fam[0].put(f, -1.6 + Math.sin(T * 0.6) * 0.8, 0, 6.4, { arms: 'hold', step: T * 9, mouth: 'smile', look: 0.8 }, {}); fam[1].put(f, 1.0, 0, 5.2, { arms: 'point', lookY: -0.8, mouth: 'open', look: -0.4 }, {}); fam[2].put(f, -3.4, 0, 4.6, { arms: 'cheer', w: Math.round(Math.sin(T * 6)), lookY: -0.8, mouth: 'smile' }, {});
      const lg = T > 60.3; pp.forEach((a, i) => a.put(f, -6.6 + i * 0.95, lg ? Math.abs(Math.sin(T * 11 + i)) * 0.06 : 0, 7.2 + (i % 2) * 0.5, lg ? { arms: i === 1 ? 'point' : 'hip', mouth: 'laugh', eyes: i === 2 ? 'open' : 'closed', look: 1, tilt: 0.06 * Math.sin(T * 11 + i) } : { arms: i === 0 ? 'point' : 'down', mouth: 'smile', look: 1, brow: 0.5 }, {}));
    }
    if (part === 7 || part === 11) {
      if (part === 7) noe.put(f, -1.5, 0, 5.5, { arms: 'point', w: 0, mouth: T > 70 ? (Math.floor(T * 2) % 2 ? 'open' : 'smile') : 'smile', look: 1, tilt: 0.03 * Math.sin(T * 6.28) }, { rot: 0 });
      const pair = (i, j) => i < 6 ? crit[i][j] : pups[j];
      for (let i = 0; i < 7; i++) for (let j = 0; j < 2; j++) {
        const a = pair(i, j); let x, y = 0, z, pose = { step: T * 8 + j }, o = { flip: true };
        if (part === 7) { const te = TE[i] + j * 0.5, dt = T - te, v = 2.5; if (dt < 0) { x = 0.5 + j * 0.25 - dt * v; z = 4.5 + j * 0.45; } else { const u = clamp(dt / 0.9); x = 0.5 + j * 0.25 - u * 0.4; z = lerp(4.5 + j * 0.45, 2.2, u); y = 0.32 * u; if (kinds[i] === 'giraffe') pose.neck = ss(0.1, 0.6, u) * 0.8; if (u >= 1) continue; }
          if (x > 19) continue; }
        else { const t0 = 114.7 + i * 0.4 + j * 0.2, dt = T - t0; if (dt < 0) continue; const u = clamp(dt / 2.6), dir = (i % 2 ? 1 : -1) * (1 + (i >> 1) * 0.9) + (j ? 0.5 : -0.5); x = dir * eout(u) * 2.4; z = lerp(2.3, 6.2 + (i % 3) * 1.1 + j * 0.5, eout(u)); y = dt < 0.5 ? 0.32 * (1 - dt / 0.5) : 0; y += Math.abs(Math.sin(T * (5 + i * 0.5) + j)) * (u < 1 ? 0.3 : 0.14) * (kinds[i] === 'elephant' || kinds[i] === 'giraffe' ? 0.3 : 1); o.flip = dir < 0; if (u >= 1) pose.step = 0; if (T > 119) pose.neck = 0; }
        if (kinds[i] === 'rabbit') y += Math.abs(Math.sin(T * 9 + j)) * 0.3; if (kinds[i] === 'lion') pose.mane = j === 0;
        if (i < 6) a.put(f, x, y, z, pose, o); else a.put(f, x, y + Math.abs(Math.sin(T * 10 + j)) * 0.1, z, { pose: 'stand', pal: j ? GREY : PUP, wag: Math.round(Math.sin(T * 14 + j) * 2) / 2, step: T * 12, mouth: 'open' }, { flip: o.flip });
      }
    }
    if (part === 8) { const du = clamp((T - 87.5) / 3.3); if (T > 87.3 && T < 91.2) { const d = Math.max(1, Math.round(du * 40)); cnt.draw('d' + d, c => { c.fillStyle = '#4a2545'; c.beginPath(); c.roundRect(4, 4, 248, 120, 22); c.fill(); c.fillStyle = '#fff3c4'; c.beginPath(); c.roundRect(12, 12, 232, 104, 16); c.fill(); c.fillStyle = '#4a2545'; c.font = 'bold 70px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('DIA ' + d, 128, 68); }); cnt.mesh.visible = true; const dir = new THREE.Vector3(); camera.getWorldDirection(dir); cnt.mesh.position.copy(camera.position).addScaledVector(dir, 4).add(new THREE.Vector3(0, 1.15, 0)); cnt.mesh.quaternion.copy(camera.quaternion); cnt.mesh.material.color.set(0xffffff);
        const ph = ((T - 87.4) * 2.5) % 1, isSun = Math.floor((T - 87.4) * 2.5) % 2 === 0, d2 = isSun ? sunD : moonD; d2.visible = true; d2.position.set(lerp(-70, 70, ph) + camera.position.x * 0.5, 30 + Math.sin(ph * 3.14) * 45, -160); } }
    if (part === 10) {
      const dk = arkY + 3.12, up = ss(103.6, 104.3, T), rel = T > 105.0, back = T > 109.7, pk = ss(111.2, 113.6, T); peak.position.y = level - 3.2 + pk * 2.6;
      noe.put(f, 1.9, dk - 1.0 * (1 - up), 1.86, back ? { arms: 'up', mouth: T > 110.8 ? 'laugh' : 'smile', eyes: T > 110.8 ? 'closed' : 'open', look: 0.3 } : rel ? { arms: T < 105.6 ? 'cheer' : 'hip', w: 0, mouth: 'smile', look: 1, lookY: -0.7 } : { arms: 'hold', mouth: 'smile', lookY: 0.4 }, { blob: false, vis: up > 0.05 });
      let dx, dy, dz, tw = false; const hx = 2.25, hy = dk + 1.38, hz = 2.0;
      if (T < 105.0) { dx = 1.9; dy = dk + 1.0; dz = 2.02; } else if (T < 107.2) { const u = clamp((T - 105.0) / 1.9); dx = lerp(hx, 20, u * u); dy = hy + u * 7 + Math.sin(u * 9) * 0.3; dz = lerp(hz, -22, u * u); } else { const u = eout((T - 107.2) / 2.5); dx = lerp(20, hx, u); dy = lerp(hy + 7, hy, u) + Math.sin(u * 9) * 0.3 * (1 - u); dz = lerp(-22, hz, u); tw = true; }
      dove.put(f, dx, dy, dz, { wing: T > 105 && T < 109.7 ? Math.floor(T * 10) % 2 : 0, twig: tw }, { flip: T >= 107.2, vis: up > 0.6 });
    }
    if (part === 11) { bow.show(ss(117.5, 119.9, T)); const cheer = T > 120.5; [[noe, -1.25], [fam[0], -2.1], [fam[1], 1.6], [fam[2], 2.4]].forEach(([a, x], i) => a.put(f, x, cheer ? Math.abs(Math.sin(T * 5 + i)) * 0.08 : 0, 9.6 + (i % 2) * 0.5, { back: true, arms: cheer && i < 2 ? 'cheer' : i === 2 && T > 118 ? 'point' : 'down', w: 0 }, {})); U.glow.value.setScalar(0.04 * ss(118, 120, T)); U.fade.value = ss(114.5, 114.8, T); }
    if (part === 10) U.fade.value = ss(99.9, 100.2, T); if (part === 6) U.fade.value = ss(52.9, 53.2, T);
  };
}
// ---------- SET: inside the ark ----------
{
  const s = mk('hold'), w = s.w, Wd = ['#a9713f', '#96622f', '#b57d48'];
  for (let i = -5; i <= 5; i++) B(w, 1, 0.2, 9, Wd[(i + 9) % 3], i, -0.2, -0.5); for (let k = 0; k < 5; k++) { B(w, 11, 1, 0.3, Wd[k % 3], 0, k, -3.6); B(w, 0.3, 1, 9, Wd[(k + 1) % 3], -5, k, -0.5); B(w, 0.3, 1, 9, Wd[(k + 2) % 3], 5, k, -0.5); }
  for (const x of [-3.2, 0, 3.2]) { B(w, 0.35, 5, 0.35, '#6b4423', x, 0, -3.3); } for (const z of [-2.5, -0.5, 1.5]) B(w, 11, 0.35, 0.35, '#6b4423', 0, 4.6, z); B(w, 11, 0.2, 9, '#7a4a26', 0, 5, -0.5);
  for (const [x, z, sz] of [[-3.6, -2.6, 1], [3.8, -2.4, 0.9], [-4, 0.4, 0.8], [2.9, 1.2, 0.7], [-2.2, 1.4, 0.5]]) B(w, sz * 1.4, sz * 0.6, sz, '#f2d36a', x, 0, z);
  B(w, 0.04, 1.2, 0.04, '#3a2416', 0.2, 3.5, 0.2); B(w, 0.3, 0.4, 0.3, MB('#ffe9a0'), 0.2, 3.1, 0.2); B(w, 0.36, 0.06, 0.36, '#3a2416', 0.2, 3.5, 0.2); B(w, 0.36, 0.06, 0.36, '#3a2416', 0.2, 3.05, 0.2); const lg = glow(s.o, 0xffc060, 4.5);
  const noe = new Actor('noe', 1.65, s.o), wife = new Actor('wife', 1.58, s.o), son = new Actor('son1', 1.65, s.o);
  const A = { lion: new Crit('lion', s.o), rab: new Crit('rabbit', s.o), rab2: new Crit('rabbit', s.o), gir: new Crit('giraffe', s.o, 0.92), ele: new Crit('elephant', s.o), zeb: new Crit('zebra', s.o), sh1: new Crit('sheep', s.o), sh2: new Crit('sheep', s.o) }, pups = [new Actor('dog', 0.3, s.o), new Actor('dog', 0.3, s.o)];
  const zz = canvasTex(64, 64, x => { x.fillStyle = '#fff'; x.font = 'bold 54px sans-serif'; x.fillText('z', 14, 50); }); const zs = []; for (let i = 0; i < 6; i++) { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: zz, transparent: true, depthWrite: false })); s.o.add(sp); zs.push(sp); }
  const CK = [[93.4, -0.6, 1.5, 5.6, -0.5, 1.2, 0, 50], [96.5, 0.3, 1.8, 6.6, 0.4, 1.7, -0.5, 50], [99.9, 0.6, 1.9, 6.2, 0.6, 1.9, -0.5, 50]];
  s.update = (f, T) => {
    look('#1a1210', '#1a1210', '#2a1a10', 8, 26, 0.7, '#ffd9a0', 0.5, 1, 4, 3, 0xf6e6d0); lamp.position.set(0.2, 2.9, 0.6); lamp.color.set('#ffc070'); lamp.intensity = 9 + 1 * Math.sin(T * 9); lg.position.set(0.2, 3.2, 0.4); lg.material.opacity = 0.6 + 0.05 * Math.sin(T * 9);
    U.fade.value = ss(93.4, 93.7, T); setCam(K(CK, T), f);
    const br = k => 1 + 0.03 * Math.sin(T * 2 + k);
    A.ele.put(f, 3.0, 0, -2.2, { sleep: 1 }, { flip: true, sy: br(0) }); A.zeb.put(f, -3.0, 0, -2.0, { sleep: 1 }, { sy: br(1) }); A.sh1.put(f, -3.3, 0, -0.4, { sleep: 1 }, { sy: br(2) }); A.sh2.put(f, -2.5, 0, -0.1, { sleep: 1 }, { flip: true, sy: br(3) });
    A.gir.put(f, 1.5, 0, -1.2, { neck: 0.5 + 0.03 * Math.sin(T * 2), sleep: 0, blink: 1 }, { flip: true });
    A.lion.put(f, -1.25, 0, 1.0, { sleep: 1 }, { sy: br(4) }); A.rab.put(f, -0.3, 0, 1.25, { sleep: 1 }, { flip: true, sy: br(5) }); A.rab2.put(f, 2.7, 0.42, 1.2, { sleep: 1 }, { sy: br(6) });
    pups.forEach((p, j) => p.put(f, 1.1 + j * 0.55, 0.01, 1.7 + j * 0.15, { pose: 'lie', pal: j ? GREY : PUP, eyes: 'closed' }, { flip: !!j }));
    noe.put(f, 0.35, 0, -0.5, { arms: 'wave', w: Math.round(Math.sin(T * 3)) * 0.5, mouth: 'smile', look: 0.9, lookY: -0.5 }, {});
    wife.put(f, -1.9, 0.3 - 56 * wife.unit + 0.26, -1.6, { legs: 'sit', eyes: 'closed', mouth: 'smile', tilt: 0.1 }, { blob: false }); son.put(f, 2.3, 0.3 - 56 * son.unit + 0.2, 0.2, { legs: 'sit', eyes: 'closed', mouth: 'smile', tilt: -0.12 }, { blob: false });
    [[-1.0, 1.1], [3.2, 1.9], [-3.1, 1.2], [-0.2, 0.6], [1.3, 0.5], [-2.3, 1.9]].forEach(([x, y], i) => { const u = (T * 0.4 + i * 0.37) % 1; zs[i].position.set(x + u * 0.4, y + u * 0.9, 1.3); zs[i].scale.setScalar(0.18 + u * 0.2); zs[i].material.opacity = Math.sin(u * 3.14) * 0.8; });
  };
}
// ---------- SET: yard (sunset + rainbow) ----------
{
  const s = mk('yard'), w = s.w, bow = makeRainbow(w, 16, 1.1, 34); bow.g.position.set(-4, -3, -60); bow.show(1);
  B(w, 60, 1, 60, '#4fae63', 0, -1, -5); for (let i = 0; i < 30; i++) B(w, 0.5 + rnd(i), 0.06, 0.5 + rnd(i + 1), i % 2 ? '#62c076' : '#3f9a55', (rnd(i + 2) - 0.5) * 12, 0, 3 - rnd(i + 3) * 7);
  for (let i = 0; i < 24; i++) B(w, 0.34, 1.3 + (i % 2) * 0.12, 0.1, '#f4f0e6', -5.6 + i * 0.48, 0, -3.4); B(w, 12, 0.12, 0.08, '#e0dccf', 0, 0.9, -3.45); B(w, 12, 0.12, 0.08, '#e0dccf', 0, 0.4, -3.45);
  tree(w, -3.1, -4.4, 4.6); house(w, 5.5, -7, 5, 4, 4, '#e8cfa8'); B(w, 5.6, 1.2, 4.6, '#c0504d', 5.5, 4.2, -7);
  const sunD = disc(w, 9, '#ffd27a', 14, 9, -150), sg = glow(s.o, 0xffb060, 70); sg.position.set(14, 9, -140); sg.material.opacity = 0.5;
  const like = G(w, -1.05, 4.05, -0.6); B(like, 1.1, 1.1, 0.3, '#3b82f6', 0, -0.55, 0); B(like, 0.42, 0.4, 0.12, '#ffffff', 0.06, -0.3, 0.2); B(like, 0.16, 0.42, 0.12, '#ffffff', -0.26, -0.3, 0.2); const th = B(like, 0.17, 0.36, 0.12, '#ffffff', 0.02, 0.05, 0.2); th.rotation.z = -0.25;
  const subT = texMat(512, 150, (x) => { x.fillStyle = '#e62117'; x.fillRect(0, 0, 512, 150); x.fillStyle = '#fff'; x.font = 'bold 76px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('INSCREVA-SE', 256, 80); }, true);
  const sub = G(w, 0.25, 2.95, -0.6); B(sub, 2.15, 0.64, 0.34, '#e62117', 0, -0.32, 0); const sp = new THREE.Mesh(new THREE.PlaneGeometry(2.05, 0.6), subT); sp.position.z = 0.175; sub.add(sp);
  const bell = G(w, 1.2, 4.35, -0.6); B(bell, 0.5, 0.5, 0.26, '#ffd21f', 0, -0.62, 0); B(bell, 0.36, 0.2, 0.26, '#ffd21f', 0, -0.14, 0); B(bell, 0.72, 0.14, 0.28, '#ffd21f', 0, -0.74, 0); B(bell, 0.16, 0.14, 0.2, '#e0a020', 0, -0.9, 0); B(bell, 0.12, 0.1, 0.2, '#e0a020', 0, 0.06, 0);
  const conf = new Confetti(s.o, 240), bp = new Burst(w, 24, 8, '#ffffff', '#ffd21f');
  const girl = new Actor('girl2', 1.1, s.o), boy = new Actor('boy2', 1.1, s.o), vovo = new Actor('vovo2', 1.5, s.o), dog = new Actor('dog', 0.55, s.o);
  const CK = [[0, 0, 1.6, 6.4, 0, 1.3, 0, 50], [3.2, 0, 2.0, 7.6, 0, 2.2, 0, 50], [8.8, 0, 2.1, 8.0, 0, 2.35, 0, 50]];
  s.update = (f, T) => {
    const t = T - 141.0; look('#4f7fd0', '#ffb070', '#ffc890', 30, 200, 1.0, '#ffd9a0', 1.3, -3, 4, 5, 0xfff0dc); U.fade.value = ss(0, 0.3, t); setCam(K(CK, t), f);
    const jp = (ph, h) => Math.abs(Math.sin(t * 6.5 + ph)) * h, ch = i => ({ arms: 'cheer', w: Math.round(Math.sin(t * 9 + i)), mouth: 'laugh', eyes: Math.sin(t * 2 + i) > 0.3 ? 'closed' : 'open' });
    girl.put(f, -1.05, jp(0, 0.4), 0, ch(0)); boy.put(f, -0.3, jp(1, 0.42), 0.15, ch(1)); vovo.put(f, 0.55, jp(2, 0.2), -0.1, { ...ch(2), arms: t > 3.6 && t < 5 ? 'pointL' : 'wave', w: Math.round(Math.sin(t * 9)) });
    const t1 = 3.7, t2 = 5.1, t3 = 6.5; const lk = spring((t - t1) / 0.6); like.scale.setScalar(Math.max(0.001, lk)); like.rotation.z = t > t1 ? 0.25 * Math.sin((t - t1) * 9) * Math.exp(-(t - t1) * 2.5) : 0; like.position.y = 4.05 + 0.06 * Math.sin(t * 3);
    const drop = clamp((t - t2) / 0.75), bounce = drop >= 1 ? Math.exp(-(t - t2 - 0.75) * 6) * Math.sin((t - t2 - 0.75) * 18) * 0.15 : 0, pr = t - t3, press = pr > 0 ? Math.exp(-pr * 5) * Math.cos(pr * 16) : 0;
    sub.visible = t > t2; sub.position.y = lerp(9, 2.95, drop * drop) + bounce + (pr > 0 ? 0.14 * press : 0); sub.scale.set(1 + (pr > 0 ? 0.08 * press : 0), 1 - (pr > 0 ? 0.22 * Math.max(0, press) : 0), 1);
    const dj = clamp((t - (t3 - 0.4)) / 0.8), dx = lerp(1.5, 0.35, ss(t3 - 1, t3 - 0.4, t)), dy = dj > 0 && dj < 1 ? Math.sin(dj * Math.PI) * 1.72 : jp(3, 0.18);
    dog.put(f, dx, dy, 0.9, { pose: 'stand', pal: GREY, wag: Math.round(Math.sin(t * 12) * 2) / 2, mouth: 'open', step: t < t3 - 0.4 ? t * 12 : 0, head: dj > 0 && dj < 1 ? -14 : 0 }, { flip: t < t3 - 0.35, rot: dj > 0 && dj < 1 ? (0.5 - dj) * -1.2 : 0, by: 0 });
    const bl = spring((t - t3 - 0.15) / 0.5); bell.scale.setScalar(Math.max(0.001, bl)); bell.rotation.z = t > t3 + 0.15 ? 0.5 * Math.sin((t - t3 - 0.15) * 14) * Math.exp(-(t - t3 - 0.15) * 1.4) : 0;
    bp.update(t - t3, 0.3, 2.5, -0.3, 2.4, 0.14); conf.update(t - t1, 0, 7, 0.3, 7, 3, 8);
  };
}
// ---------- timeline ----------
const SC = [[0, 'room', 1], [405, 'room', 2], [768, 'vila'], [984, 'garden', 1], [1226, 'garden', 2], [1587, 'hill', 6], [1941, 'hill', 7], [2532, 'hill', 8], [2802, 'hold'], [2997, 'hill', 10], [3435, 'hill', 11], [3813, 'room', 12], [4230, 'yard'], [4491, '']];
export const TOTAL = 4491;
window.renderFrame = (f) => {
  let i = 0; while (f >= SC[i + 1][0]) i++; const [a, name, arg] = SC[i], b = SC[i + 1][0];
  for (const k in sets) sets[k].w.visible = sets[k].o.visible = k === name;
  U.flash.value = 0; U.fade.value = 1; U.time.value = f / FPS; lamp.color.set('#ffc070');
  sets[name].update(f, f / FPS, arg);
  const noDip = [768, 3813, 405, 1226]; const din = f - a, dout = b - 1 - f; let fd = 1; if (!noDip.includes(a) && a > 0) fd = Math.min(fd, (din + 1) / 4); if (!noDip.includes(b) && b < TOTAL) fd = Math.min(fd, (dout + 1) / 4); if (b === TOTAL) fd = Math.min(fd, (dout + 1) / 10);
  U.fade.value *= clamp(fd); draw();
};
window.ready = true;
