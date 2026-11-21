// 2D cartoon cast drawn on canvas (units: 320x480, feet near y=466)
const OUT = '#4a2545';
const CX = 160;
function fs(ctx, fill, lw = 5) { ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = lw; ctx.strokeStyle = OUT; ctx.lineJoin = 'round'; ctx.stroke(); }
function limb(ctx, pts, w, col) {
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.strokeStyle = OUT; ctx.lineWidth = w + 9; ctx.stroke();
  ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke();
}
function circ(ctx, x, y, r, fill, lw = 5) { ctx.beginPath(); ctx.arc(x, y, r, 0, 7); fs(ctx, fill, lw); }
function ell(ctx, x, y, rx, ry, fill, lw = 5) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 7); fs(ctx, fill, lw); }

export function geo(c, legs = 'stand') {
  const g = c.kid ? { headY: 180, hrx: 74, hry: 68, shY: 252, bw: 92, hw: 112, hem: c.dress ? 392 : 372, arm: 0.8, top: 108 }
    : { headY: 118, hrx: 60, hry: 56, shY: 180, bw: 108, hw: 132, hem: c.long ? 410 : 330, arm: 1, top: 58 };
  g.hip = g.shY + (c.kid ? 85 : 118);
  g.floor = 466; g.seat = g.hip + 38;
  if (legs === 'sit') g.floor = g.hip + 38 + 56;
  if (legs === 'kneel') g.floor = g.hip + 47;
  return g;
}

const ARMS = { // right arm offsets from shoulder: elbow, hand
  down: [[10, 45], [14, 95]], up: [[26, -28], [36, -88]], out: [[45, 10], [88, -4]], hip: [[42, 36], [12, 62]],
  point: [[42, -4], [90, -30]], hold: [[10, 46], [-26, 62]], cheek: [[30, 30], [-8, -40]], fwd: [[20, 30], [30, 60]],
};

export function drawPerson(ctx, c, p = {}) {
  const legs = p.legs || 'stand', g = geo(c, legs), a = p.arms || 'down', w = p.w || 0;
  const { headY, hrx, hry, shY, bw, hw } = g;
  const sk = c.skin, top = p.bath ? sk : c.top;
  const bot = legs === 'stand' || legs === 'none' ? g.hem : (legs === 'sit' ? g.hip : g.hip + 20);
  // long hair behind
  if (c.hair === 'long') { ctx.beginPath(); ctx.roundRect(CX - hrx - 9, headY - hry - 6, 2 * hrx + 18, 2 * hry + 46, 44); fs(ctx, c.hairC); }
  // legs
  const legC = c.legsC || sk, lw = c.kid ? 20 : 22;
  if (legs === 'stand') {
    const s = p.step || 0, d = Math.sin(s) * 16, l1 = Math.max(0, Math.cos(s)) * 12, l2 = Math.max(0, -Math.cos(s)) * 12;
    limb(ctx, [[CX - 24, g.hem - 12], [CX - 24 + d, 452 - l1]], lw, legC);
    limb(ctx, [[CX + 24, g.hem - 12], [CX + 24 - d, 452 - l2]], lw, legC);
    ell(ctx, CX - 24 + d + 3, 458 - l1, 19, 10, c.shoe || '#8a5a2b'); ell(ctx, CX + 24 - d + 3, 458 - l2, 19, 10, c.shoe || '#8a5a2b');
  } else if (legs === 'sit') {
    limb(ctx, [[CX - 26, g.seat - 6], [CX - 28, g.seat + 42]], lw, legC); limb(ctx, [[CX + 26, g.seat - 6], [CX + 28, g.seat + 42]], lw, legC);
    ell(ctx, CX - 28, g.seat + 48, 20, 11, c.shoe || '#8a5a2b'); ell(ctx, CX + 28, g.seat + 48, 20, 11, c.shoe || '#8a5a2b');
  }
  // arms (back layer)
  const shL = [CX - bw / 2 + 4, shY + 16], shR = [CX + bw / 2 - 4, shY + 16], am = g.arm;
  const sleeve = p.bath ? sk : (c.sleeve || top), aw = c.kid ? 19 : 22;
  const arm = (side, key, wig = 0) => {
    const A = ARMS[key] || ARMS.down, sh = side > 0 ? shR : shL;
    const e = [sh[0] + side * A[0][0] * am, sh[1] + A[0][1] * am], h = [sh[0] + side * (A[1][0] + wig) * am, sh[1] + A[1][1] * am];
    limb(ctx, [sh, e, h], aw, sleeve); circ(ctx, h[0], h[1], c.kid ? 12 : 13, sk, 4);
  };
  const front = a === 'cross' || a === 'pray' || a === 'hold';
  if (!front) {
    if (a === 'wave') { arm(-1, 'down'); arm(1, 'up', w * 22); }
    else if (a === 'point') { arm(-1, 'down'); arm(1, 'point'); }
    else if (a === 'pointL') { arm(1, 'down'); arm(-1, 'point'); }
    else if (a === 'cheer') { arm(-1, 'up', w * 14); arm(1, 'up', w * 14); }
    else if (a === 'talk') { arm(-1, 'down'); arm(1, 'out', w * 10); }
    else if (a === 'cheek') { arm(-1, 'down'); arm(1, 'cheek'); }
    else { arm(-1, a); arm(1, a); }
  }
  // body
  ctx.beginPath(); ctx.moveTo(CX - bw / 2, shY); ctx.lineTo(CX + bw / 2, shY); ctx.lineTo(CX + hw / 2, bot); ctx.lineTo(CX - hw / 2, bot); ctx.closePath();
  fs(ctx, top);
  if (c.stripes && !p.bath) {
    ctx.save(); ctx.beginPath(); ctx.moveTo(CX - bw / 2 + 3, shY + 3); ctx.lineTo(CX + bw / 2 - 3, shY + 3); ctx.lineTo(CX + hw / 2 - 3, bot - 3); ctx.lineTo(CX - hw / 2 + 3, bot - 3); ctx.closePath(); ctx.clip();
    ctx.fillStyle = c.stripes; for (let y = shY + 14; y < bot; y += 40) ctx.fillRect(0, y, 320, 20); ctx.restore();
  }
  if (c.belt && !p.bath) { ctx.fillStyle = c.belt; ctx.fillRect(CX - bw / 2 - 6, g.hip - 22, bw + 12, 12); }
  if (c.shawl) { ctx.beginPath(); ctx.moveTo(CX - bw / 2 - 4, shY); ctx.lineTo(CX + bw / 2 + 4, shY); ctx.lineTo(CX, shY + 62); ctx.closePath(); fs(ctx, c.shawl, 4); }
  if (legs === 'sit') { ctx.beginPath(); ctx.roundRect(CX - hw / 2 - 12, g.hip - 10, hw + 24, 48, 18); fs(ctx, c.long || c.dress ? top : legC); }
  if (legs === 'kneel') { ctx.beginPath(); ctx.roundRect(CX - hw / 2 - 8, g.hip + 4, hw + 16, 42, 16); fs(ctx, c.long || c.dress ? top : legC); }
  // head
  ctx.save(); ctx.translate(CX, headY + hry - 6); ctx.rotate(p.tilt || 0); ctx.translate(-CX, -(headY + hry - 6) + (p.nod || 0));
  circ(ctx, CX - hrx + 2, headY + 8, 11, sk, 4); circ(ctx, CX + hrx - 2, headY + 8, 11, sk, 4);
  ctx.beginPath(); ctx.roundRect(CX - hrx, headY - hry, 2 * hrx, 2 * hry, hry * 0.72); fs(ctx, p.back ? (c.hair === 'scarf' ? c.scarfC : c.hairC) : sk);
  const dx = (p.look || 0) * 11, dy = (p.lookY || 0) * 9;
  if (!p.back) {
    if (c.beard) { ctx.save(); ctx.beginPath(); ctx.roundRect(CX - hrx + 2, headY - hry + 2, 2 * hrx - 4, 2 * hry - 4, hry * 0.7); ctx.clip(); ctx.fillStyle = c.beard; ctx.fillRect(0, headY + hry * 0.28, 320, 100); ctx.restore(); }
    // cheeks
    ctx.globalAlpha = 0.45; ctx.fillStyle = '#ff7a8a';
    ctx.beginPath(); ctx.arc(CX - hrx * 0.62 + dx, headY + hry * 0.3 + dy, 10, 0, 7); ctx.arc(CX + hrx * 0.62 + dx, headY + hry * 0.3 + dy, 10, 0, 7); ctx.fill(); ctx.globalAlpha = 1;
    // eyes
    const ex = hrx * 0.4, ey = headY + 2 + dy, E = p.eyes || 'open';
    for (const s of [-1, 1]) {
      const x = CX + s * ex + dx;
      ctx.lineWidth = 5; ctx.strokeStyle = '#2b1630'; ctx.lineCap = 'round';
      if (E === 'closed') { ctx.beginPath(); ctx.arc(x, ey + 3, 9, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); }
      else if (E === 'down') { ctx.beginPath(); ctx.arc(x, ey - 4, 9, Math.PI * 0.1, Math.PI * 0.9); ctx.stroke(); }
      else if (E === 'wide') { ctx.beginPath(); ctx.arc(x, ey, 14, 0, 7); ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 3; ctx.stroke(); ctx.beginPath(); ctx.arc(x + dx * 0.3, ey + dy * 0.3, 6, 0, 7); ctx.fillStyle = '#2b1630'; ctx.fill(); }
      else { ctx.beginPath(); ctx.ellipse(x, ey, 7.5, 11, 0, 0, 7); ctx.fillStyle = '#2b1630'; ctx.fill(); ctx.beginPath(); ctx.arc(x + 2.5, ey - 4, 3, 0, 7); ctx.fillStyle = '#fff'; ctx.fill(); }
      if (p.brow) { ctx.lineWidth = 5; ctx.strokeStyle = '#2b1630'; ctx.beginPath(); ctx.moveTo(x - s * 12, ey - 20 - p.brow * 7 * 1); ctx.lineTo(x + s * 12, ey - 20 + p.brow * 7); ctx.stroke(); }
    }
    if (c.glasses) { ctx.lineWidth = 4; ctx.strokeStyle = '#5a4a6a'; for (const s of [-1, 1]) { ctx.beginPath(); ctx.arc(CX + s * ex + dx, ey, 19, 0, 7); ctx.stroke(); } ctx.beginPath(); ctx.moveTo(CX - ex + 19 + dx, ey); ctx.lineTo(CX + ex - 19 + dx, ey); ctx.stroke(); }
    // mouth
    const mx = CX + dx * 0.7, my = headY + hry * 0.52 + dy * 0.6, Mo = p.mouth || 'smile';
    ctx.lineWidth = 5; ctx.strokeStyle = '#2b1630'; ctx.lineCap = 'round';
    if (Mo === 'smile') { ctx.beginPath(); ctx.arc(mx, my - 8, 15, Math.PI * 0.15, Math.PI * 0.85); ctx.stroke(); }
    else if (Mo === 'sad') { ctx.beginPath(); ctx.arc(mx, my + 12, 14, Math.PI * 1.2, Math.PI * 1.8); ctx.stroke(); }
    else if (Mo === 'flat') { ctx.beginPath(); ctx.moveTo(mx - 11, my); ctx.lineTo(mx + 11, my); ctx.stroke(); }
    else if (Mo === 'o') { ctx.beginPath(); ctx.ellipse(mx, my, 9, 12, 0, 0, 7); ctx.fillStyle = '#5a1f2e'; ctx.fill(); ctx.stroke(); }
    else if (Mo === 'open') { ctx.beginPath(); ctx.ellipse(mx, my, 14, 10, 0, 0, 7); ctx.fillStyle = '#5a1f2e'; ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.ellipse(mx, my + 5, 8, 4, 0, 0, 7); ctx.fillStyle = '#ff8fa0'; ctx.fill(); }
    else if (Mo === 'laugh') { ctx.beginPath(); ctx.arc(mx, my - 6, 18, 0, Math.PI); ctx.closePath(); ctx.fillStyle = '#5a1f2e'; ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.ellipse(mx, my + 6, 9, 4, 0, 0, 7); ctx.fillStyle = '#ff8fa0'; ctx.fill(); }
  }
  // hair / hats
  const hairTop = (col, h = 0.8) => { ctx.save(); ctx.beginPath(); ctx.roundRect(CX - hrx - 3, headY - hry - 5, 2 * hrx + 6, 2 * hry + 4, hry * 0.74); ctx.clip(); ctx.beginPath(); ctx.rect(0, 0, 320, headY - hry + hry * h); ctx.fillStyle = col; ctx.fill(); ctx.restore(); ctx.beginPath(); ctx.roundRect(CX - hrx, headY - hry, 2 * hrx, 2 * hry, hry * 0.72); ctx.lineWidth = 5; ctx.strokeStyle = OUT; ctx.stroke(); };
  if (!p.back) {
    if (c.hair === 'short') hairTop(c.hairC, 0.62);
    if (c.hair === 'long') { hairTop(c.hairC, 0.66); if (c.bow) { for (const s of [-1, 1]) { ctx.beginPath(); ctx.moveTo(CX + 38, headY - hry + 6); ctx.lineTo(CX + 38 + s * 26, headY - hry - 12); ctx.lineTo(CX + 38 + s * 26, headY - hry + 24); ctx.closePath(); fs(ctx, c.bow, 4); } circ(ctx, CX + 38, headY - hry + 6, 8, c.bow, 4); } }
    if (c.hair === 'bun') { circ(ctx, CX, headY - hry - 12, 24, c.hairC); hairTop(c.hairC, 0.6); }
    if (c.hair === 'cap') { hairTop(c.hairC, 0.7); }
    if (c.hair === 'scarf') hairTop(c.scarfC, 0.62);
  } else if (c.hair === 'bun') circ(ctx, CX, headY - hry - 12, 24, c.hairC);
  if (c.hair === 'cap') { ctx.beginPath(); ctx.roundRect(CX - hrx - 5, headY - hry - 12, 2 * hrx + 10, hry * 0.8, [46, 46, 6, 6]); fs(ctx, c.capC); if (!p.back) { ctx.beginPath(); ctx.roundRect(CX - 10, headY - hry * 0.42, hrx + 42, 17, 9); fs(ctx, c.capC); } circ(ctx, CX, headY - hry - 12, 6, '#fff', 3); }
  if (c.hair === 'scarf') { circ(ctx, CX + hrx - 2, headY - hry * 0.3, 12, c.scarfC, 4); limb(ctx, [[CX + hrx + 4, headY - hry * 0.2], [CX + hrx + 14, headY + 12]], 8, c.scarfC); }
  ctx.restore();
  // front arms
  if (a === 'cross') {
    limb(ctx, [shL, [shL[0] - 6, shY + 62 * am], [CX + bw / 2 - 16, shY + 56 * am]], aw, sleeve);
    limb(ctx, [shR, [shR[0] + 6, shY + 62 * am], [CX - bw / 2 + 16, shY + 70 * am]], aw, sleeve);
    circ(ctx, CX - bw / 2 + 14, shY + 70 * am, 13, sk, 4);
  } else if (a === 'pray') {
    limb(ctx, [shL, [shL[0] - 8, shY + 62 * am], [CX - 6, shY + 34 * am]], aw, sleeve);
    limb(ctx, [shR, [shR[0] + 8, shY + 62 * am], [CX + 6, shY + 34 * am]], aw, sleeve);
    circ(ctx, CX, shY + 30 * am, 15, sk, 4);
  } else if (a === 'hold') {
    limb(ctx, [shL, [shL[0] - 8, shY + 60 * am], [CX - 26, shY + 74 * am]], aw, sleeve);
    limb(ctx, [shR, [shR[0] + 8, shY + 60 * am], [CX + 26, shY + 74 * am]], aw, sleeve);
    circ(ctx, CX - 26, shY + 74 * am, 13, sk, 4); circ(ctx, CX + 26, shY + 74 * am, 13, sk, 4);
  }
}

// dog, side view facing right. units 320x240, feet y=228
export function drawDog(ctx, p = {}) {
  const lie = p.pose === 'lie', by = lie ? 150 : 108, col = '#c98a4b', dk = '#8a5a2b';
  const wag = (p.wag || 0) * 26;
  limb(ctx, [[82, by + 22], [52 + wag * 0.3, by - 30 + Math.abs(wag) * 0.3]], 14, col);
  if (!lie) { const s = p.step || 0, d = Math.sin(s) * 14; for (const [x, k] of [[100, 1], [128, -1], [200, -1], [226, 1]]) limb(ctx, [[x, by + 60], [x + d * k, 220]], 17, k > 0 ? col : dk); }
  else { limb(ctx, [[215, 214], [262, 218]], 16, col); limb(ctx, [[95, 214], [125, 218]], 16, col); }
  ctx.beginPath(); ctx.roundRect(70, by, 175, 76, 36); fs(ctx, col);
  ctx.beginPath(); ctx.ellipse(150, by + 58, 52, 14, 0, 0, 7); ctx.fillStyle = '#f1dcb8'; ctx.fill();
  const hx = 208, hy = by - 52 + (lie ? 30 : 0) + (p.head || 0);
  ctx.beginPath(); ctx.roundRect(hx, hy, 92, 84, 30); fs(ctx, col);
  ctx.beginPath(); ctx.roundRect(hx + 52, hy + 38, 54, 40, 16); fs(ctx, '#f1dcb8');
  circ(ctx, hx + 100, hy + 46, 9, '#2b1630', 2);
  ctx.beginPath(); ctx.roundRect(hx + 4, hy - 4, 30, 58, 14); fs(ctx, dk);
  ctx.lineWidth = 5; ctx.strokeStyle = '#2b1630'; ctx.lineCap = 'round';
  if (p.eyes === 'closed') { ctx.beginPath(); ctx.arc(hx + 58, hy + 30, 8, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); }
  else { ctx.beginPath(); ctx.ellipse(hx + 58, hy + 26, 7, 10, 0, 0, 7); ctx.fillStyle = '#2b1630'; ctx.fill(); ctx.beginPath(); ctx.arc(hx + 60, hy + 22, 3, 0, 7); ctx.fillStyle = '#fff'; ctx.fill(); }
  if (p.mouth === 'open') { ctx.beginPath(); ctx.ellipse(hx + 76, hy + 76, 13, 9, 0, 0, 7); ctx.fillStyle = '#5a1f2e'; ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.ellipse(hx + 78, hy + 82, 8, 6, 0, 0, 7); ctx.fillStyle = '#ff8fa0'; ctx.fill(); }
  else { ctx.beginPath(); ctx.arc(hx + 76, hy + 62, 12, Math.PI * 0.15, Math.PI * 0.85); ctx.stroke(); }
  ctx.fillStyle = '#d93a3a'; ctx.fillRect(hx - 2, hy + 74, 44, 10);
}

export const CAST = {
  girl: { kid: 1, skin: '#f6c9a8', hair: 'long', hairC: '#6b3a1e', top: '#ff7fb0', bow: '#ff4f93', dress: 1, shoe: '#ffffff' },
  boy: { kid: 1, skin: '#e9b48c', hair: 'cap', hairC: '#3a2a20', capC: '#3b82d6', top: '#f2c94c', legsC: '#4a6fa5', shoe: '#d9534f' },
  girlpj: { kid: 1, skin: '#f6c9a8', hair: 'long', hairC: '#6b3a1e', top: '#ff9cc4', bow: '#ff4f93', dress: 1, shoe: '#ffffff' },
  boypj: { kid: 1, skin: '#e9b48c', hair: 'cap', hairC: '#3a2a20', capC: '#3b82d6', top: '#8fb8f0', legsC: '#8fb8f0', shoe: '#d9534f' },
  vovo: { skin: '#f3c7a6', hair: 'bun', hairC: '#dcdce6', top: '#8e6bbf', long: 1, glasses: 1, shoe: '#6b4a3a', shawl: '#f4e6c8' },
  jonas: { skin: '#e0a878', hair: 'short', hairC: '#6b4423', beard: '#6b4423', top: '#a9d6f7', long: 1, belt: '#8a5a2b', shoe: '#8a5a2b' },
  sailor1: { skin: '#d99a6c', hair: 'scarf', scarfC: '#d93a3a', top: '#ffffff', stripes: '#d93a3a', long: 1, shoe: '#6b4a3a' },
  sailor2: { skin: '#f0c098', hair: 'scarf', scarfC: '#2f6fb5', top: '#ffffff', stripes: '#d93a3a', long: 1, beard: '#3a2a20', shoe: '#6b4a3a' },
  sailor3: { skin: '#b97a50', hair: 'scarf', scarfC: '#e0a020', top: '#ffffff', stripes: '#d93a3a', long: 1, shoe: '#6b4a3a' },
  nin1: { skin: '#d99a6c', hair: 'short', hairC: '#2b1c14', top: '#e07a3a', long: 1, belt: '#6b4423' },
  nin2: { skin: '#f0c098', hair: 'scarf', scarfC: '#7a4fb0', top: '#3fa37a', long: 1 },
  nin3: { skin: '#b97a50', hair: 'short', hairC: '#1f1410', beard: '#1f1410', top: '#d94f6a', long: 1, belt: '#f2c94c' },
  nin4: { skin: '#e0a878', hair: 'bun', hairC: '#3a2a20', top: '#f2c94c', long: 1, shawl: '#e07a3a' },
  nin5: { skin: '#d99a6c', hair: 'scarf', scarfC: '#f2c94c', top: '#7a5fd0', long: 1, belt: '#f4e6c8' },
};
