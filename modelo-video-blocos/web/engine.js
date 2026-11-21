import * as THREE from 'three';
import { drawPerson, drawDog, CAST, geo } from './chars.js';
export { THREE, CAST, geo };
export const W = 1080, H = 1920;
const canvas = document.getElementById('c');
export const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false); renderer.autoClear = false;
export const world = new THREE.Scene(), over = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(45, W / H, 0.3, 400);
export const hemi = new THREE.HemisphereLight(0xffffff, 0x8090a0, 1.0), sun = new THREE.DirectionalLight(0xffffff, 1.5), lamp = new THREE.PointLight(0xffc070, 0, 12, 1.5);
world.add(hemi, sun, lamp); world.fog = new THREE.Fog(0xffffff, 60, 300);
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, u) => a + (b - a) * u;
export const ss = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
export const eout = u => 1 - Math.pow(1 - clamp(u), 3);
export const spring = u => u <= 0 ? 0 : 1 + Math.exp(-6 * u) * Math.sin(u * 14 - 1.57);
export const rnd = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
// toon materials
const gd = new Uint8Array([120, 120, 120, 255, 200, 200, 200, 255, 255, 255, 255, 255]);
const grad = new THREE.DataTexture(gd, 3, 1); grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
const mats = {};
export const M = col => mats[col] ??= new THREE.MeshToonMaterial({ color: col, gradientMap: grad });
export const MB = (col, o = {}) => new THREE.MeshBasicMaterial({ color: col, ...o });
const BG = new THREE.BoxGeometry(1, 1, 1);
// box with bottom at y
export function B(parent, w, h, d, col, x = 0, y = 0, z = 0) { const m = new THREE.Mesh(BG, typeof col === 'string' || typeof col === 'number' ? M(col) : col); m.scale.set(w, h, d); m.position.set(x, y + h / 2, z); parent.add(m); return m; }
export function G(parent, x = 0, y = 0, z = 0) { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; }
export function canvasTex(w, h, fn) { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); fn(x, w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
export function texMat(w, h, fn, basic) { const t = canvasTex(w, h, fn); return basic ? new THREE.MeshBasicMaterial({ map: t }) : new THREE.MeshToonMaterial({ map: t, gradientMap: grad }); }
export function tiles(c1, c2, n, rx, ry) { const m = texMat(256, 256, (x) => { x.fillStyle = c1; x.fillRect(0, 0, 256, 256); x.strokeStyle = c2; x.lineWidth = 6; const s = 256 / n; for (let i = 0; i <= n; i++) { x.beginPath(); x.moveTo(i * s, 0); x.lineTo(i * s, 256); x.moveTo(0, i * s); x.lineTo(256, i * s); x.stroke(); } }); m.map.wrapS = m.map.wrapT = THREE.RepeatWrapping; m.map.repeat.set(rx, ry); return m; }
// cards
export class Card {
  constructor(wm, hm, cw, ch, parent = over) {
    this.cv = document.createElement('canvas'); this.cv.width = cw * 2; this.cv.height = ch * 2; this.ctx = this.cv.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.cv); this.tex.colorSpace = THREE.SRGBColorSpace;
    const g = new THREE.PlaneGeometry(wm, hm); g.translate(0, hm / 2, 0);
    this.mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, alphaTest: 0.03, depthWrite: false, side: THREE.DoubleSide }));
    this.hm = hm; this.ch = ch; this.key = null; parent.add(this.mesh);
  }
  draw(key, fn) { if (key === this.key) return; this.key = key; const c = this.ctx; c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, this.cv.width, this.cv.height); c.setTransform(2, 0, 0, 2, 0, 0); fn(c); this.tex.needsUpdate = true; }
}
const blobGeo = new THREE.CircleGeometry(0.5, 20); blobGeo.rotateX(-Math.PI / 2);
export const tint = new THREE.Color(1, 1, 1);
let seedN = 0;
export class Actor {
  constructor(name, height, parent) {
    this.c = CAST[name]; this.dog = name === 'dog'; this.seed = ++seedN; this.g = G(parent);
    if (this.dog) { this.unit = height / 150; this.card = new Card(320 * this.unit, 240 * this.unit, 320, 240, this.g); this.floor = 228; this.ch = 240; }
    else { const ge = geo(this.c); this.unit = height / (466 - ge.top); this.card = new Card(320 * this.unit, 480 * this.unit, 320, 480, this.g); this.ch = 480; }
    this.blob = new THREE.Mesh(blobGeo, new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.25, depthWrite: false })); this.blob.renderOrder = -1; this.g.add(this.blob);
  }
  // place feet (or floor line of pose) at x,y,z
  put(f, x, y, z, pose = {}, o = {}) {
    const p = { ...pose }; let floor = this.floor;
    if (!this.dog) { if ((p.eyes || 'open') === 'open' && (f + this.seed * 37) % 113 < 4) p.eyes = 'closed'; floor = o.floorU ?? geo(this.c, p.legs).floor; }
    const key = JSON.stringify(p); this.card.draw(key, c => this.dog ? drawDog(c, p) : drawPerson(c, this.c, p));
    const m = this.card.mesh, br = 1 + 0.012 * Math.sin(f * 0.13 + this.seed * 2);
    const sx = (o.sx ?? 1) * (o.flip ? -1 : 1), sy = (o.sy ?? 1) * br;
    m.visible = o.vis !== false; m.scale.set(sx, sy, 1);
    m.position.set(x, y - (this.ch - floor) * this.unit * sy, z); m.rotation.set(0, Math.atan2(camera.position.x - x, camera.position.z - z), 0); m.rotateZ(o.rot || 0);
    m.material.color.copy(tint); if (o.dark) m.material.color.multiplyScalar(o.dark);
    this.blob.visible = m.visible && o.blob !== false; this.blob.position.set(x, (o.by ?? y) + 0.02, z); const bs = (this.dog ? 0.9 : 0.7) * (o.bs ?? 1); this.blob.scale.set(bs, 1, bs * 0.6);
  }
  hide() { this.card.mesh.visible = false; this.blob.visible = false; }
}
// post: ink from depth + sky + grade
const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthTexture: new THREE.DepthTexture(W, H, THREE.UnsignedIntType) });
export const U = { tC: { value: rt.texture }, tD: { value: rt.depthTexture }, skyT: { value: new THREE.Color() }, skyB: { value: new THREE.Color() }, stars: { value: 0 }, flash: { value: 0 }, fade: { value: 1 }, time: { value: 0 }, ink: { value: 1 }, near: { value: 0.3 }, far: { value: 400 }, glow: { value: new THREE.Color(0, 0, 0) } };
const post = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({
  uniforms: U, depthFunc: THREE.AlwaysDepth, depthWrite: true,
  vertexShader: 'varying vec2 v;void main(){v=uv;gl_Position=vec4(position.xy,0.,1.);}',
  fragmentShader: `varying vec2 v;uniform sampler2D tC,tD;uniform vec3 skyT,skyB,glow;uniform float stars,flash,fade,time,ink,near,far;
  float iz(vec2 uv){float d=texture2D(tD,uv).x;float z=(2.*near*far)/(far+near-(d*2.-1.)*(far-near));return 1./z;}
  float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  void main(){vec2 px=vec2(1./1080.,1./1920.)*2.2;float d=texture2D(tD,v).x;vec3 c=texture2D(tC,v).rgb;
   float c0=iz(v);float e=0.;
   e=max(e,abs(iz(v+vec2(px.x,0.))+iz(v-vec2(px.x,0.))-2.*c0));e=max(e,abs(iz(v+vec2(0.,px.y))+iz(v-vec2(0.,px.y))-2.*c0));
   e=max(e,abs(iz(v+px)+iz(v-px)-2.*c0));e=max(e,abs(iz(v+vec2(px.x,-px.y))+iz(v-vec2(px.x,-px.y))-2.*c0));
   float m=max(c0,max(max(iz(v+vec2(px.x,0.)),iz(v-vec2(px.x,0.))),max(iz(v+vec2(0.,px.y)),iz(v-vec2(0.,px.y)))));
   float k=smoothstep(.012,.03,e/m)*ink*(1.-smoothstep(.006,.0035,m)*.75);
   if(d>=.99999){c=mix(skyB,skyT,smoothstep(.25,.95,v.y));vec2 g=floor(v*vec2(1080.,1920.)/7.);float s=step(.988,h(g))*stars*(.6+.4*sin(time*3.+h(g+3.)*40.))*smoothstep(.35,.6,v.y);c+=vec3(s);}
   c=mix(c,vec3(.05,.03,.07),k);
   c+=glow*(1.-.6*distance(v,vec2(.5,.6)));
   float vg=1.-.35*pow(distance(v,vec2(.5))*1.25,2.2);c*=vg;float l=dot(c,vec3(.3,.6,.1));c=mix(vec3(l),c,1.12);
   c=mix(c,vec3(1.),flash)*fade;gl_FragColor=vec4(c,1.);gl_FragDepth=d;
   #include <colorspace_fragment>
  }`}));
post.frustumCulled = false; const postScene = new THREE.Scene(); postScene.add(post); const oc = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
export function draw() {
  camera.updateProjectionMatrix(); U.near.value = camera.near; U.far.value = camera.far;
  renderer.setRenderTarget(rt); renderer.clear(); renderer.render(world, camera);
  renderer.setRenderTarget(null); renderer.clear(); renderer.render(postScene, oc); renderer.render(over, camera);
}
export function K(keys, t) { let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++; const a = keys[i], b = keys[i + 1]; let u = clamp((t - a[0]) / (b[0] - a[0])); u = u * u * (3 - 2 * u); return a.map((v, j) => v + (b[j] - v) * u); }
export function setCam(k, f, shake = 0) { const dx = Math.sin(f * 0.031) * 0.04 + Math.sin(f * 1.9) * shake, dy = Math.sin(f * 0.043 + 1) * 0.03 + Math.cos(f * 2.3) * shake; camera.position.set(k[1] + dx, k[2] + dy, k[3]); camera.fov = k[7]; camera.lookAt(k[4] + dx * 0.5, k[5] + dy * 0.5, k[6]); }
export function look(skyT, skyB, fogC, fogN, fogF, hemiI, sunC, sunI, sx, sy, sz, tintC = 0xffffff, stars = 0) { U.skyT.value.set(skyT); U.skyB.value.set(skyB); world.fog.color.set(fogC); world.fog.near = fogN; world.fog.far = fogF; hemi.intensity = hemiI; sun.color.set(sunC); sun.intensity = sunI; sun.position.set(sx, sy, sz); tint.set(tintC); U.stars.value = stars; lamp.intensity = 0; U.glow.value.set(0, 0, 0); }
export const lerpC = (a, b, u) => new THREE.Color(a).lerp(new THREE.Color(b), u);
