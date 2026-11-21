#!/usr/bin/env python3
"""Operação Sigilo – v2 (totalmente animado). 720x1280, 30fps.
Cada cena é desenhada quadro a quadro: personagens que se mexem, raios, interfaces
reagindo, tremor de câmera, glitch nas trocas de cena.
Uso: python3 build.py            -> gera o MP4 + roteiro
     python3 build.py --test 3 12 40   -> salva PNGs desses instantes (segundos)"""
import math, random, subprocess, os, json, sys
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 30
OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, NAVY2 = (4, 9, 28), (8, 20, 60)
BLUE, BLUE2 = (30, 90, 255), (90, 150, 255)
YEL, RED, WHITE = (255, 210, 31), (255, 52, 72), (255, 255, 255)
DARK, SKIN = (10, 14, 34), (205, 222, 255)
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
if not os.path.exists(FB): FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_fc = {}
def bf(s):
    s = int(s)
    if ("b", s) not in _fc: _fc[("b", s)] = ImageFont.truetype(FB, s)
    return _fc[("b", s)]
def mf(s):
    s = int(s)
    if ("m", s) not in _fc: _fc[("m", s)] = ImageFont.truetype(FM, s)
    return _fc[("m", s)]

# ---------------------------------------------------------------- ROTEIRO
SCENES = []
WPS = 2.55
SPEED = dict(lupa=.55, cta=.9, relogio2=1.0)
IMPACTS = dict(contador5=[0, .5, 1.0, 1.5, 2.0], padrao=[], tesouro=[1.0], pix=[1.0], caixa=[1.6], petrobras=[1.8], enem=[2.2], cinco=[], porta=[3.0], chave=[3.0], testes=[4.2, 5.0], misterio=[], ataque=[2.8], relogio2=[.2], calmar=[1.2], alvo=[3.3], cadeado=[1.1], entrev=[1.3], entrev2=[1.3], malic=[.5], codigo=[3.4, 6.6], arquivos=[.4],
               relogio=[.2], calend=[1.9], escudo=[.5], download=[1.2], cta=[4.4], app=[1.6], app2=[.3])

def parse(t):
    res, cur = [], WHITE
    for tok in t.split():
        if tok == "|": res.append(("|", WHITE)); continue
        if tok[0] in "*_": cur = YEL if tok[0] == "*" else RED
        clean = tok.replace("*", "").replace("_", "")
        res.append((clean, cur))
        if tok.rstrip(".,:!?")[-1:] in "*_": cur = WHITE
    return res

CENAS = os.environ.get("CENAS", "cenas.json"); PREFIX = os.environ.get("PREFIX", "operacao-sigilo")
ORIG = dict(alvo=(2.5, 1.9), app=(2.0, 1.5), app2=(1.85, 2.4), cadeado=(2.2, 1.3), entrev=(2.2, 1.2), entrev2=(3.0, 2.3), malic=(2.0, 1.0), codigo=(3.0, 2.4), arquivos=(3.0, 1.5), relogio=(2.0, 1.0), calend=(2.5, 1.1), escudo=(2.2, 1.2), celular=(3.0, 1.5), download=(3.0, 1.2), lupa=(3.0, 1.3), cta=(5.0, 1.2))
timeline, t0 = [], 0.0
for c in json.load(open(os.path.join(OUT, CENAS))):
    chs = c["chunks"]; end = c["start"] + c["dur"]
    for i, ch in enumerate(chs):
        ch["dur"] = (chs[i + 1]["start"] if i + 1 < len(chs) else end) - ch["start"]; ch["words"] = parse(ch["text"])
    timeline.append(dict(kind=c["kind"], tag="", words=chs[0]["words"], chunks=chs, start=c["start"], dur=c["dur"], speed=(max(.6, min(3.0, ORIG[c["kind"]][1] * ORIG[c["kind"]][0] / c["dur"])) if "hacker" in CENAS and c["kind"] in ORIG else SPEED.get(c["kind"], 1.0))))
    t0 = end
TOTAL = t0

# ---------------------------------------------------------------- utilidades de animação
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ep(t, a, b): return cl((t - a) / (b - a))
def eo(k): k = cl(k); return 1 - (1 - k) ** 3
def bk(k):
    k = cl(k); c = 1.70158
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2
def pulse(t, f): return 0.5 + 0.5 * math.sin(t * f * 2 * math.pi)

# ---------------------------------------------------------------- fundo
def make_bg():
    bg = Image.new("RGB", (W, H), NAVY); px = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] * (1 - k) + NAVY2[i] * k) for i in range(3)))
    g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).ellipse((-100, 380, W + 100, 1100), fill=255)
    g = g.filter(ImageFilter.GaussianBlur(120))
    glow = Image.new("RGB", (W, H), (18, 50, 160))
    return Image.composite(glow, bg, g.point(lambda v: int(v * .55)))
BG = make_bg().convert("RGBA")
VIG = Image.new("L", (W, H), 0)
_v = ImageDraw.Draw(VIG); _v.rectangle((0, 0, W, H), fill=140); _v.ellipse((-160, -120, W + 160, H + 120), fill=0)
VIG = VIG.filter(ImageFilter.GaussianBlur(140))
VIGL = Image.new("RGBA", (W, H), (0, 0, 8, 255)); VIGL.putalpha(VIG)
SCAN = Image.new("RGBA", (W, H), (0, 0, 0, 0)); _s = ImageDraw.Draw(SCAN)
for y in range(0, H, 4): _s.line([(0, y), (W, y)], fill=(0, 0, 0, 38))

def grid_layer(t):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l); hz = 1010
    for i in range(-14, 15): d.line([(W / 2 + i * 22, hz), (W / 2 + i * 190, H)], fill=BLUE + (70,), width=1)
    ph = (t * 0.6) % 1
    for j in range(9):
        k = (j + ph) / 9; y = hz + (H - hz) * (k ** 2)
        d.line([(0, y), (W, y)], fill=BLUE + (int(30 + 70 * k),), width=1)
    d.line([(0, hz), (W, hz)], fill=BLUE2 + (120,), width=2)
    return l

random.seed(7)
PARTS = [(random.random() * W, random.random() * H, random.random() * .5 + .2, random.choice("01{}<>/#$"), random.choice([BLUE2, YEL, WHITE])) for _ in range(34)]
def particles(t):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l); f = mf(16)
    for x, y, sp, ch, col in PARTS: d.text((x, (y - t * 60 * sp) % H), ch, font=f, fill=col + (70,))
    return l

# ---------------------------------------------------------------- primitivas (palco 600x600, desenhado a 2x)
S = 2
SX, SY, SSZ = 50, 520, 620            # onde o palco cai no quadro
def tf(x, y): return (SX + x * SSZ / 600, SY + y * SSZ / 600)
def P(*a): return [v * S for v in a]
def rr(d, box, r, fill, outline=None, w=0): d.rounded_rectangle(P(*box), radius=r * S, fill=fill, outline=outline, width=int(w * S))
def poly(d, pts, fill, outline=None, w=0):
    pp = [(x * S, y * S) for x, y in pts]
    d.polygon(pp, fill=fill)
    if outline: d.line(pp + [pp[0]], fill=outline, width=int(w * S), joint="curve")
def ell(d, box, fill=None, outline=None, w=0): d.ellipse(P(*box), fill=fill, outline=outline, width=int(w * S))
def circ(d, cx, cy, r, fill=None, outline=None, w=0):
    if r < 1: return
    ell(d, (cx - r, cy - r, cx + r, cy + r), fill, outline, w)
def line(d, pts, fill, w): d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(w * S)), joint="curve")
def txt(d, xy, s, size, fill, mono=False, anchor="mm"):
    if size < 2: return
    d.text((xy[0] * S, xy[1] * S), s, font=(mf if mono else bf)(size * S), fill=fill, anchor=anchor)
def cursor(d, x, y, press=0):
    k = 1 - .12 * press
    pts = [(0, 0), (0, 34), (9, 26), (16, 40), (22, 37), (15, 24), (27, 24)]
    poly(d, [(x + px * k, y + py * k) for px, py in pts], WHITE, DARK, 2)

def alpha_layer(): return Image.new("RGBA", (600 * S, 600 * S), (0, 0, 0, 0))

# ---------------------------------------------------------------- personagens
def hacker(im, cx, cy, sc, lt, mode="type", eyes=YEL):
    """hacker de capuz com braços animados. mode: type | wave | idle"""
    d = ImageDraw.Draw(im)
    sway = math.sin(lt * 2.6) * 3 * sc
    q = lambda x, y: (cx + x * sc + (sway if y < 0 else sway * .5), cy + y * sc)
    # braços (atrás do notebook)
    def arm(sx, sy, hx, hy, ex_off):
        s = q(sx, sy); h = (cx + hx * sc, cy + hy * sc)
        el = ((s[0] + h[0]) / 2 + ex_off * sc, (s[1] + h[1]) / 2 + 20 * sc)
        d.line([(s[0] * S, s[1] * S), (el[0] * S, el[1] * S), (h[0] * S, h[1] * S)], fill=BLUE2, width=int(34 * sc * S), joint="curve")
        d.line([(s[0] * S, s[1] * S), (el[0] * S, el[1] * S), (h[0] * S, h[1] * S)], fill=(10, 18, 52), width=int(26 * sc * S), joint="curve")
        circ(d, h[0], h[1], 15 * sc, fill=SKIN) if False else d.ellipse([(h[0] - 14 * sc) * S, (h[1] - 14 * sc) * S, (h[0] + 14 * sc) * S, (h[1] + 14 * sc) * S], fill=SKIN)
    # corpo
    poly(d, [q(-135, 190), q(-118, 40), q(-72, -45), q(0, -88), q(72, -45), q(118, 40), q(135, 190)], (6, 10, 30), BLUE2, int(3))
    if mode == "type":
        b1 = math.sin(lt * 17) * 9; b2 = math.sin(lt * 17 + 2.1) * 9
        arm(-95, 70, -48, 150 + b1, -26); arm(95, 70, 48, 150 + b2, 26)
    elif mode == "wave":
        ang = math.radians(-60 + math.sin(lt * 9) * 25)
        hx, hy = 150 * math.cos(ang) + 95 - 20, 150 * math.sin(ang) + 70
        s = q(95, 70); h = (cx + (95 + 70 * math.cos(ang)) * sc, cy + (70 + 150 * math.sin(ang)) * sc)
        d.line([(s[0] * S, s[1] * S), (h[0] * S, h[1] * S)], fill=BLUE2, width=int(34 * sc * S))
        d.line([(s[0] * S, s[1] * S), (h[0] * S, h[1] * S)], fill=(10, 18, 52), width=int(26 * sc * S))
        d.ellipse([(h[0] - 16 * sc) * S, (h[1] - 16 * sc) * S, (h[0] + 16 * sc) * S, (h[1] + 16 * sc) * S], fill=SKIN)
    # capuz + rosto
    poly(d, [q(-92, 60), q(-84, -20), q(-50, -90), q(0, -118), q(50, -90), q(84, -20), q(92, 60), q(40, 20), q(-40, 20)], (6, 10, 30), BLUE2, 3)
    fx0, fy0 = q(-52, -62); fx1, fy1 = q(52, 52)
    d.ellipse([fx0 * S, fy0 * S, fx1 * S, fy1 * S], fill=(0, 2, 10), outline=(40, 80, 200), width=2 * S)
    blink = 0.12 if (lt % 2.7) < .12 else 1.0
    for ex in (-26, 26):
        x, y = q(ex, -6)
        w, h = 14 * sc, 9 * sc * blink
        d.ellipse([(x - w) * S, (y - h) * S, (x + w) * S, (y + h) * S], fill=eyes)
    if mode == "type":  # notebook
        x0, y0 = cx - 100 * sc, cy + 70 * sc; w, h = 200 * sc, 125 * sc
        d.rounded_rectangle([x0 * S, y0 * S, (x0 + w) * S, (y0 + h) * S], radius=8 * S, fill=(12, 22, 64), outline=BLUE2, width=3 * S)
        for i in range(6):
            ww = (40 + ((i * 53 + int(lt * 6) * 31) % 100)) * sc
            col = (RED, YEL, BLUE2, WHITE, BLUE2, YEL)[i]
            d.line([((x0 + 14 * sc) * S, (y0 + 16 * sc + i * 16 * sc) * S), ((x0 + 14 * sc + ww) * S, (y0 + 16 * sc + i * 16 * sc) * S)], fill=col, width=int(6 * sc * S))
        ph = [(x0 - 22 * sc, y0 + h), (x0 + w + 22 * sc, y0 + h), (x0 + w + 10 * sc, y0 + h + 14 * sc), (x0 - 10 * sc, y0 + h + 14 * sc)]
        d.polygon([(a * S, b * S) for a, b in ph], fill=(24, 36, 90), outline=BLUE2)

def mask_face(d, cx, cy, lt, talk=True):
    """avatar do 'recrutador' (máscara sorridente) falando, piscando, balançando."""
    nod = math.sin(lt * 3.2) * 6
    cy += nod
    circ(d, cx, cy, 70, fill=WHITE, outline=BLUE2, w=4)
    blink = (lt % 2.2) < .12
    for ex in (-26, 26):
        if blink: line(d, [(cx + ex - 12, cy - 12), (cx + ex + 12, cy - 12)], DARK, 5)
        else: circ(d, cx + ex, cy - 12, 8, fill=DARK)
    ell(d, (cx - 60, cy + 6, cx - 38, cy + 24), fill=RED + (140,)); ell(d, (cx + 38, cy + 6, cx + 60, cy + 24), fill=RED + (140,))
    mh = (6 + 16 * abs(math.sin(lt * 11)) * (0.4 + 0.6 * abs(math.sin(lt * 2.3)))) if talk else 8
    d.pieslice(P(cx - 34, cy + 6 - mh * .3, cx + 34, cy + 40 + mh * .4), 0, 180, fill=DARK) if talk else d.arc(P(cx - 34, cy - 4, cx + 34, cy + 40), 20, 160, fill=DARK, width=5 * S)
    # corpo + gravata
    poly(d, [(cx - 120, cy + 190), (cx - 80, cy + 80), (cx + 80, cy + 80), (cx + 120, cy + 190)], DARK, WHITE, 3)
    poly(d, [(cx - 14, cy + 80), (cx + 14, cy + 80), (cx + 10, cy + 110), (cx + 22, cy + 175), (cx, cy + 195), (cx - 22, cy + 175), (cx - 10, cy + 110)], RED)

# ---------------------------------------------------------------- relâmpago (efeito de quadro inteiro)
def bolt_pts(x0, y0, x1, y1, seed, depth=5, disp=.22):
    rnd = random.Random(seed); pts = [(x0, y0), (x1, y1)]
    amp = math.hypot(x1 - x0, y1 - y0) * disp
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2 + rnd.uniform(-amp, amp), (a[1] + b[1]) / 2 + rnd.uniform(-amp, amp) * .4
            new += [(mx, my), b]
        pts = new; amp *= .55
    return pts

def draw_bolts(frame, bolts):
    """bolts: lista de (x0,y0,x1,y1,seed,cor) em coordenadas de quadro."""
    if not bolts: return
    sm = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); sd = ImageDraw.Draw(sm)
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(core)
    for (x0, y0, x1, y1, seed, col) in bolts:
        pts = bolt_pts(x0, y0, x1, y1, seed)
        sd.line([(x / 2, y / 2) for x, y in pts], fill=col + (255,), width=9)
        cd.line(pts, fill=col + (255,), width=7); cd.line(pts, fill=WHITE + (255,), width=3)
        # ramificação
        rnd = random.Random(seed + 99)
        for _ in range(3):
            i = rnd.randrange(len(pts) // 4, len(pts) * 3 // 4); px, py = pts[i]
            ex, ey = px + rnd.uniform(-170, 170), py + rnd.uniform(60, 220)
            bp = bolt_pts(px, py, ex, ey, seed + i, 4, .25)
            sd.line([(x / 2, y / 2) for x, y in bp], fill=col + (255,), width=5)
            cd.line(bp, fill=col + (255,), width=3); cd.line(bp, fill=WHITE + (255,), width=1)
    glow = sm.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    frame.alpha_composite(glow); frame.alpha_composite(glow); frame.alpha_composite(core)

# ---------------------------------------------------------------- CENAS (cada uma desenha o palco no instante lt)
def sc_alvo(im, d, lt, gt, fx):
    for i in range(-250, 251, 50):
        line(d, [(300 + i, 40), (300 + i, 560)], BLUE + (50,), 1); line(d, [(40, 300 + i), (560, 300 + i)], BLUE + (50,), 1)
    for r in (260, 190, 120): circ(d, 300, 300, r + 5 * math.sin(gt * 3 + r), outline=BLUE2 + (150,), w=2)
    a0 = (lt * 150) % 360
    for i in range(22): d.pieslice(P(40, 40, 560, 560), a0 - i * 3 - 3, a0 - i * 3, fill=BLUE + (max(0, 170 - i * 8),))
    rnd = random.Random(4)
    for i in range(7):
        bx, by = 300 + rnd.uniform(-200, 200), 300 + rnd.uniform(-200, 200)
        if lt > .3 + i * .25: circ(d, bx, by, 7 + 3 * pulse(gt + i, 2), fill=YEL + (int(200 * pulse(gt * 1.3 + i, 1.5) + 40),))
    k = ep(lt, 1.8, 3.3)
    if k > 0:
        r = 250 * (1 - eo(k)) + 48
        circ(d, 300, 300, r, outline=RED, w=5)
        for a in range(0, 360, 90):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            line(d, [(300 + (r + 30) * ca, 300 + (r + 30) * sa), (300 + (r - 24) * ca, 300 + (r - 24) * sa)], RED, 5)
    if lt > 3.3:
        if lt < 4.4:
            fx["bolts"].append((*tf(300 + random.Random(int(gt * 18)).uniform(-30, 30), 300), 0, 0, int(gt * 18), BLUE2))  # placeholder reescrito abaixo
            fx["bolts"][-1] = (tf(300, 300)[0] + random.Random(int(gt * 18)).uniform(-60, 60), -20, *tf(300, 300), int(gt * 18) % 5 + 3, BLUE2)
            fx["flash"] = (WHITE, int(190 * (1 - ep(lt, 3.3, 3.8))))
        for j in range(3):
            rad = (lt - 3.3 - j * .18) * 520
            if rad > 0: circ(d, 300, 300, rad, outline=(RED if j % 2 == 0 else YEL) + (int(255 * max(0, 1 - rad / 330)),), w=4)
        circ(d, 300, 300, 32 + 8 * pulse(gt, 4), fill=RED); circ(d, 300, 300, 14, fill=WHITE)
    if lt > 1.8 and int(gt * 4) % 2 == 0 or lt > 3.3: txt(d, (300, 80), "ALVO TRAVADO" if lt < 3.3 else "INVADIDO", 36, RED if lt > 3.3 else YEL)
    txt(d, (300, 540), "LAT 23.55  LON 46.63", 20, BLUE2, mono=True)

def browser(d, lt, gt, title="meu-app.vercel.app", slide=True):
    k = bk(lt / .45); oy = (1 - k) * 180
    rr(d, (50, 90 + oy, 550, 500 + oy), 18, (12, 20, 56), BLUE2, 4); rr(d, (50, 90 + oy, 550, 140 + oy), 18, BLUE)
    for i, c in enumerate((RED, YEL, WHITE)): circ(d, 81 + i * 28, 115 + oy, 9, fill=c)
    rr(d, (170, 104 + oy, 520, 128 + oy), 10, (8, 14, 44)); txt(d, (345, 116 + oy), title, 16, BLUE2, mono=True)
    return oy

def sc_app(im, d, lt, gt, fx):
    oy = browser(d, lt, gt)
    txt(d, (300, 220 + oy), "MEU APP", 56, WHITE); txt(d, (300, 280 + oy), "FEITO COM IA", 18, YEL, mono=True)
    press = ep(lt, 1.55, 1.7) * (1 - ep(lt, 1.7, 1.95))
    bw = 200 - 22 * press
    rr(d, (300 - bw / 2, 330 + oy + press * 4, 300 + bw / 2, 390 + oy + press * 4), 30, YEL); txt(d, (300, 360 + oy + press * 4), "COMEÇAR", 28, DARK)
    if lt > 1.6:  # ripple do clique
        r = (lt - 1.6) * 260; circ(d, 300, 360, r, outline=YEL + (int(255 * max(0, 1 - r / 150)),), w=3)
    for i in range(3): rr(d, (90 + i * 150, 430 + oy, 220 + i * 150, 470 + oy), 8, (20, 36, 96))
    # cursor percorre até o botão
    k = eo(ep(lt, .5, 1.5)); cx0, cy0 = 520 - 220 * k, 560 - 190 * k
    cursor(d, cx0, cy0, press)

def sc_app2(im, d, lt, gt, fx):
    oy = browser(d, lt, gt)
    steps = [("CRIANDO COM IA", 0.0), ("PUBLICANDO", 1.6), ("NO AR!", 4.2)]
    prog = ep(lt, .6, 4.2)
    txt(d, (300, 190 + oy), "DEPLOY", 50, WHITE)
    rr(d, (100, 250 + oy, 500, 290 + oy), 20, (8, 14, 44), BLUE2, 3)
    if prog > 0: rr(d, (104, 254 + oy, 104 + 392 * prog, 286 + oy), 16, YEL if prog < 1 else RED)
    txt(d, (300, 270 + oy), f"{int(prog * 100)}%", 22, DARK if prog > .5 else WHITE, mono=True)
    lab = [s for s, t in steps if lt >= t][-1]
    txt(d, (300, 330 + oy), lab, 24, YEL if lt < 4.2 else RED, mono=True)
    # linhas de "código" digitadas
    rnd = random.Random(2)
    for i in range(5):
        w = 40 + rnd.randint(60, 240); cur = w * cl((lt - .3 - i * .12) / .5)
        if cur > 0: line(d, [(110, 380 + oy + i * 22), (110 + cur, 380 + oy + i * 22)], (BLUE2, WHITE, YEL, BLUE2, WHITE)[i], 8)
    # faíscas de IA
    for i in range(4):
        a = gt * 1.7 + i * 1.6; sx_, sy_ = 300 + 235 * math.cos(a) * (0.7 + .3 * math.sin(gt + i)), 300 + 215 * math.sin(a)
        s = 12 + 8 * pulse(gt * 2 + i, 1.5)
        poly(d, [(sx_, sy_ - s), (sx_ + s * .3, sy_ - s * .3), (sx_ + s, sy_), (sx_ + s * .3, sy_ + s * .3), (sx_, sy_ + s), (sx_ - s * .3, sy_ + s * .3), (sx_ - s, sy_), (sx_ - s * .3, sy_ - s * .3)], YEL)
    if lt > 4.2:
        circ(d, 300, 300, (lt - 4.2) * 500, outline=RED + (int(255 * max(0, 1 - (lt - 4.2) * 1.4)),), w=5)

def sc_cadeado(im, d, lt, gt, fx):
    sh = bk(lt / .4); body_y = 260 + (1 - sh) * 120
    op = eo(ep(lt, 1.0, 1.5)); lift = 85 * op
    pts = [(210, body_y), (210, body_y - 80), (240, body_y - 140), (300, body_y - 160), (360, body_y - 140), (390, body_y - 80), (390, body_y - lift)]
    line(d, pts, WHITE, 26)
    shake = math.sin(lt * 60) * 4 * max(0, 1 - (lt - 1.1) * 4) if lt > 1.1 else 0
    rr(d, (150 + shake, body_y, 450 + shake, body_y + 220), 26, BLUE, WHITE, 6)
    circ(d, 300 + shake, body_y + 70, 30, fill=DARK); rr(d, (290 + shake, body_y + 90, 310 + shake, body_y + 150), 6, DARK)
    # pacotes de dados vazando
    if lt > 1.1:
        for i, lab in enumerate(("SENHA", "CPF", "EMAIL", "CARTÃO", "SENHA", "CPF")):
            t_ = ((lt - 1.1) * .55 + i * .17) % 1
            ang = math.radians(-70 + i * 28 + 8 * math.sin(i))
            x = 300 + math.cos(ang) * 330 * t_; y = body_y - 20 + math.sin(ang) * 380 * t_ - 60 * t_
            w = 100; a = int(255 * (1 - t_ ** 3))
            rr(d, (x - w / 2, y - 16, x + w / 2, y + 16), 8, RED + (a,)); txt(d, (x, y), lab, 16, WHITE + (a,), mono=True)
    wy = 1 + .1 * math.sin(gt * 9)
    sx_ = 480 + (math.sin(gt * 40) * 3 if lt > 1.1 else 0)
    sz = (bk((lt - .4) / .4)) * wy
    poly(d, [(sx_, 120 + 90 * (1 - sz)), (sx_ + 105 * sz, 300 + 0 * sz - 40 * (1 - sz)), (sx_ - 105 * sz, 300)], RED, WHITE, 5)
    txt(d, (sx_, 250), "!", int(90 * sz), WHITE)
    txt(d, (300, 560), "DADOS EXPOSTOS", 34, YEL if int(gt * 3) % 2 == 0 else WHITE)
    if lt > 1.0 and lt < 1.4: fx["flash"] = (RED, int(150 * (1 - ep(lt, 1.0, 1.4))))

def sc_entrev(im, d, lt, gt, fx, long=False):
    k = bk(lt / .45); oy = (1 - k) * 150
    rr(d, (30, 90 + oy, 570, 520 + oy), 16, (12, 20, 56), BLUE2, 4)
    rr(d, (50, 110 + oy, 390, 450 + oy), 8, (18, 40, 120))
    sub = alpha_layer(); sd = ImageDraw.Draw(sub)
    mask_face(sd, 220, 200 + oy, lt)
    clip = Image.new("L", im.size, 0); ImageDraw.Draw(clip).rounded_rectangle(P(50, 110 + oy, 390, 450 + oy), radius=8 * S, fill=255)
    sub.putalpha(Image.composite(sub.split()[3], Image.new("L", im.size, 0), clip)); im.alpha_composite(sub)
    d2 = ImageDraw.Draw(im)
    rr(d2, (410, 110 + oy, 550, 235 + oy), 8, (24, 50, 140)); rr(d2, (410, 250 + oy, 550, 360 + oy), 8, (18, 30, 90))
    # você na webcam (hacker piscando) e "recrutador" balançando
    sm = alpha_layer(); hacker(sm, 480, 335 + oy, .3, lt, "idle"); cp = Image.new("L", im.size, 0)
    ImageDraw.Draw(cp).rounded_rectangle(P(410, 250 + oy, 550, 360 + oy), radius=8 * S, fill=255)
    sm.putalpha(Image.composite(sm.split()[3], Image.new("L", im.size, 0), cp)); im.alpha_composite(sm)
    d3 = ImageDraw.Draw(im)
    # balão de salário que estoura
    bs = bk((lt - 1.3) / .4)
    if bs > 0:
        rr(d3, (420 - 10 * bs, 135 + oy - 8 * bs, 540 + 10 * bs, 180 + oy + 8 * bs), 12, WHITE)
        txt(d3, (480, 158 + oy), "R$ 28 MIL", int(22 * bs) + 1, DARK)
    pu = 1 + .06 * math.sin(gt * 8)
    rr(d3, (410, 375 + oy, 550, 430 + oy), 10, YEL); txt(d3, (480, 402 + oy), "CONTRATADO!", int(19 * pu), DARK)
    for i, c in enumerate((BLUE2, BLUE2, RED)): circ(d3, 246 + i * 50, 480 + oy, 16, fill=c)
    if long:  # pop-up pedindo para instalar
        pk = bk((lt - 3.6) / .45)
        if pk > 0:
            py = 150 + (1 - pk) * 420
            rr(d3, (80, py, 520, py + 210), 18, WHITE, BLUE, 5); rr(d3, (80, py, 520, py + 50), 18, BLUE); d3.rectangle(P(80, py + 30, 520, py + 50), fill=BLUE)
            txt(d3, (300, py + 25), "INSTALAR PARA O TESTE", 20, WHITE)
            txt(d3, (300, py + 98), "teste_entrevista.exe", 26, DARK, mono=True)
            press = ep(lt, 6.2, 6.35) * (1 - ep(lt, 6.35, 6.6))
            rr(d3, (330 - 6 * press, py + 135 + press * 3, 490 + 6 * press, py + 190 + press * 3), 14, YEL); txt(d3, (410, py + 162 + press * 3), "INSTALAR", 24, DARK)
            rr(d3, (110, py + 135, 290, py + 190), 14, (200, 210, 235)); txt(d3, (200, py + 162), "AGORA NÃO", 20, DARK)
            c = eo(ep(lt, 4.4, 6.1)); cursor(d3, 560 - 150 * c, 520 - 330 * c + (1 - pk) * 0, press)
            if lt > 6.3: circ(d3, 410, py + 162, (lt - 6.3) * 300, outline=YEL + (int(255 * max(0, 1 - (lt - 6.3) * 2.2)),), w=3)

def sc_entrev2(im, d, lt, gt, fx): sc_entrev(im, d, lt, gt, fx, long=True)

def sc_malic(im, d, lt, gt, fx):
    sk = math.sin(lt * 50) * 6 * max(0, 1 - lt * 1.5)
    open_ = eo(ep(lt, .4, 1.2))
    cxb = 300 + sk
    poly(d, [(cxb, 70), (cxb + 200, 180), (cxb + 200, 400), (cxb, 510), (cxb - 200, 400), (cxb - 200, 180)], (14, 24, 70), BLUE2, 6)
    top = [(cxb, 70 - 50 * open_), (cxb + 200, 180 - 50 * open_), (cxb, 290 - 50 * open_), (cxb - 200, 180 - 50 * open_)]
    poly(d, top, (24, 44, 130), BLUE2, 4)
    line(d, [(cxb, 290), (cxb, 510)], BLUE2, 3)
    if open_ > 0:   # vazamento vermelho
        rnd = random.Random(8)
        for i in range(16):
            t_ = ((lt - .4) * .9 + i * .071) % 1; ang = math.radians(-90 + rnd.uniform(-70, 70))
            x = cxb + math.cos(ang) * 260 * t_; y = 200 + math.sin(ang) * 330 * t_
            w = 10 + rnd.randint(0, 22); a = int(255 * (1 - t_))
            d.rectangle(P(x, y, x + w, y + 8), fill=(RED if i % 3 else YEL) + (a,))
    sk_ = bk((lt - .5) / .3)
    if sk_ > 0:
        st = alpha_layer(); sd = ImageDraw.Draw(st); sc_ = 1 + (1 - sk_) * 1.6
        rr(sd, (90, 255, 510, 365), 12, RED + (240,), WHITE, 7); txt(sd, (300, 310), "MALICIOSO", 66, WHITE)
        st = st.rotate(-12, resample=Image.BICUBIC, center=(300 * S, 310 * S))
        if sc_ != 1:
            ns = int(600 * S * sc_); st2 = st.resize((ns, ns), Image.BICUBIC); o = (ns - 600 * S) // 2
            st = st2.crop((o, o, o + 600 * S, o + 600 * S))
        im.alpha_composite(st)
    circ(d, 465, 85, 38 + 4 * pulse(gt, 3), fill=RED, outline=WHITE, w=4); txt(d, (465, 85), "X", 44, WHITE)
    if .5 <= lt < .9: fx["flash"] = (RED, int(170 * (1 - ep(lt, .5, .9))))
    if .5 <= lt < 1.3: fx["bolts"].append((tf(120, 0)[0], 0, *tf(300, 310), int(gt * 15) + 11, RED)); fx["bolts"].append((tf(480, 0)[0], 0, *tf(300, 310), int(gt * 15) + 31, RED))

def sc_codigo(im, d, lt, gt, fx):
    k = bk(lt / .4); oy = (1 - k) * 160
    rr(d, (60, 80 + oy, 540, 370 + oy), 14, (6, 12, 40), BLUE2, 4); rr(d, (60, 80 + oy, 540, 112 + oy), 14, (14, 28, 80))
    txt(d, (300, 96 + oy), "meu-projeto / app.js", 14, BLUE2, mono=True)
    rnd = random.Random(3); cols = [BLUE2, YEL, WHITE, BLUE2, WHITE]
    for i in range(9):
        w = rnd.randint(110, 330); ind = rnd.choice((0, 0, 26, 52)); cur = w * cl((lt - .3 - i * .25) / .6)
        if cur > 0: line(d, [(90 + ind, 140 + oy + i * 24), (90 + ind + cur, 140 + oy + i * 24)], cols[i % 5], 9)
    # teclas CTRL+V
    p1 = ep(lt, 2.8, 2.95) * (1 - ep(lt, 3.35, 3.5)); p2 = ep(lt, 3.1, 3.25) * (1 - ep(lt, 3.4, 3.55))
    rr(d, (150, 430 + p1 * 8, 270, 500 + p1 * 8), 12, WHITE); txt(d, (210, 465 + p1 * 8), "CTRL", 30, DARK)
    txt(d, (300, 465), "+", 40, WHITE)
    rr(d, (330, 430 + p2 * 8, 410, 500 + p2 * 8), 12, YEL); txt(d, (370, 465 + p2 * 8), "V", 40, DARK)
    # linha maliciosa colada com glitch
    pk = ep(lt, 3.4, 3.8)
    if pk > 0:
        gx = int(math.sin(gt * 70) * 8) if lt < 4.4 else 0
        ww = 330 * eo(pk); y = 140 + oy + 9 * 24 + 4
        rr(d, (90 + gx, y, 90 + gx + ww, y + 20), 6, RED)
        if lt < 4.0: txt(d, (300, y + 10), "exec(base64.decode(...))", 14, WHITE, mono=True)
        # alerta
        sz = bk((lt - 3.7) / .35) * (1 + .1 * math.sin(gt * 10))
        poly(d, [(480, 40 + 90 * (1 - sz)), (480 + 82 * sz, 190), (480 - 82 * sz, 190)], RED, WHITE, 4); txt(d, (480, 150), "!", int(60 * sz), WHITE)
    # porta dos fundos
    dk = ep(lt, 6.2, 7.0)
    if dk > 0:
        bx, by = 300, 410
        rr(d, (bx - 70, by - 20, bx + 70, by + 150), 8, (30, 8, 20)) if False else None
        glow_w = 140 * eo(dk)
        poly(d, [(bx - 50, by + 150), (bx - 50 - glow_w * .5, by + 160), (bx + 50 + glow_w * .5, by + 160), (bx + 50, by + 150)], RED + (120,))
        rr(d, (bx - 50, by - 10, bx + 50, by + 150), 6, (60, 10, 25), RED, 4)
        ow = 100 * eo(dk)
        poly(d, [(bx - 50, by - 10), (bx - 50 + ow * .6, by + 8), (bx - 50 + ow * .6, by + 135), (bx - 50, by + 150)], (110, 18, 40), WHITE, 3)
        if dk > .6: txt(d, (bx + 10, by + 70), "BACKDOOR", 18, YEL, mono=True)
        if 6.6 < lt < 7.4: fx["flash"] = (RED, int(110 * (1 - ep(lt, 6.6, 7.4))))

def sc_arquivos(im, d, lt, gt, fx):
    # folders voando até o hacker
    cols = (YEL, BLUE2, WHITE, RED, YEL, BLUE2)
    starts = [(40, 80), (260, 20), (480, 90), (30, 300), (500, 280), (150, 150)]
    for i, (x, y) in enumerate(starts):
        t_ = ep(lt, .6 + i * .4, 1.8 + i * .4)
        if t_ <= 0: continue
        e = t_ ** 2; fxx, fyy = x + (300 - 50 - x) * e, y + (330 - y) * e; sc_ = 1 - .75 * e
        c = cols[i % len(cols)]
        if t_ < 1:
            line(d, [(x + 50, y + 30), (fxx + 50 * sc_, fyy + 30 * sc_)], c + (90,), 2)
            rr(d, (fxx, fyy - 12 * sc_, fxx + 50 * sc_, fyy + 6 * sc_), 5, c); rr(d, (fxx, fyy, fxx + 100 * sc_, fyy + 70 * sc_), 8, c)
    sm = alpha_layer(); hacker(sm, 300, 390, 1.1, lt, "type", eyes=RED if lt > 1 else YEL); im.alpha_composite(sm)
    d2 = ImageDraw.Draw(im)
    for i, (lab, c) in enumerate((("ARQUIVOS", YEL), ("SENHAS", RED), ("CLIENTES", BLUE2))):
        on = lt > 1.6 + i * 1.1
        rr(d2, (40 + i * 175, 535, 190 + i * 175, 585), 14, c if on else (20, 30, 80)); txt(d2, (115 + i * 175, 560), lab, 20, DARK if (on and c != BLUE2) else WHITE)
    fx["bolts"] += [(tf(40, 0)[0], 0, *tf(300, 250), int(gt * 15) + 5, RED)] if lt < .9 else []
    if lt < .6: fx["flash"] = (BLUE2, int(120 * (1 - lt / .6)))

def sc_relogio(im, d, lt, gt, fx):
    k = bk(lt / .4); sc_ = .7 + .3 * k
    cx, cy, R = 300, 310, 220 * sc_
    for i in range(14):
        a = math.radians(i * 25.7 + gt * 90)
        line(d, [(cx + (R + 25) * math.cos(a), cy + (R + 25) * math.sin(a)), (cx + (R + 25 + 28 * pulse(gt * 3 + i, 2)) * math.cos(a), cy + (R + 25 + 28 * pulse(gt * 3 + i, 2)) * math.sin(a))], RED + (200,), 5)
    circ(d, cx, cy, R, fill=WHITE, outline=BLUE, w=22)
    sweep = (lt * 210) % 360
    d.pieslice(P(cx - R + 30, cy - R + 30, cx + R - 30, cy + R - 30), -90, -90 + sweep, fill=RED)
    for i in range(60):
        a = math.radians(i * 6 - 90); r1, r2 = R - 35, R - 50 if i % 5 else R - 65
        line(d, [(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a))], DARK, 3 if i % 5 else 6)
    a = math.radians(-90 + sweep)
    line(d, [(cx, cy), (cx + (R - 45) * math.cos(a), cy + (R - 45) * math.sin(a))], DARK, 8)
    circ(d, cx, cy, 15, fill=YEL, outline=DARK, w=4)
    rr(d, (270, 48, 330, 86), 8, BLUE2); rr(d, (285, 30, 315, 52), 4, BLUE2)
    secs = int(lt * 130); txt(d, (300, 410), f"00:{secs // 60 % 60:02d}:{secs % 60:02d}", 28, YEL, mono=True)
    rr(d, (240, 380, 360, 440), 8, DARK + (0,)) if False else None

def sc_calend(im, d, lt, gt, fx):
    k = bk(lt / .4); oy = (1 - k) * 200
    rr(d, (110, 70 + oy, 490, 510 + oy), 24, WHITE); rr(d, (110, 70 + oy, 490, 170 + oy), 24, RED); d.rectangle(P(110, 130 + oy, 490, 170 + oy), fill=RED)
    txt(d, (300, 120 + oy), "DEPOIS", 48, WHITE)
    n = int(1 + 20 * eo(ep(lt, .35, 1.9))); frac = ((1 + 20 * eo(ep(lt, .35, 1.9))) % 1) if lt < 1.9 else 0
    sq = 1 - .35 * abs(math.sin(frac * math.pi)) if lt < 1.9 else 1
    big = int(190 * sq) + 1
    txt(d, (300, 305 + oy), str(n), big, RED if lt >= 1.9 else DARK)
    txt(d, (300, 440 + oy), "DIAS", 48, BLUE)
    for x in (170, 430): rr(d, (x - 14, 48 + oy, x + 14, 100 + oy), 8, BLUE2)
    if lt >= 1.9:
        r = (lt - 1.9) * 500; circ(d, 300, 300, r, outline=RED + (int(255 * max(0, 1 - r / 300)),), w=6)
        if lt < 2.3: fx["flash"] = (RED, int(120 * (1 - ep(lt, 1.9, 2.3))))

def sc_escudo(im, d, lt, gt, fx):
    sz = bk(lt / .5)
    cx, cy = 300, 300
    f = lambda x, y: (cx + (x - cx) * sz, cy + (y - cy) * sz)
    for j in range(3):
        r = ((gt * .5 + j / 3) % 1) * 300
        circ(d, cx, cy, r + 60, outline=BLUE2 + (int(200 * (1 - r / 300)),), w=3)
    sh = [(300, 40), (500, 110), (490, 330), (300, 550), (110, 330), (100, 110)]
    poly(d, [f(*p) for p in sh], BLUE, YEL, 10)
    poly(d, [f(*p) for p in [(300, 90), (455, 145), (448, 320), (300, 495), (152, 320), (145, 145)]], (18, 60, 200), WHITE, 4)
    ck = ep(lt, .6, 1.3)
    p1, p2, p3 = (210, 300), (275, 365), (400, 220)
    if ck > 0:
        if ck < .4: pts = [p1, (p1[0] + (p2[0] - p1[0]) * ck / .4, p1[1] + (p2[1] - p1[1]) * ck / .4)]
        else: u = (ck - .4) / .6; pts = [p1, p2, (p2[0] + (p3[0] - p2[0]) * u, p2[1] + (p3[1] - p2[1]) * u)]
        line(d, pts, WHITE, 36)
    for i in range(4):  # cadeados orbitando
        a = gt * 1.8 + i * math.pi / 2; x, y = 300 + 255 * math.cos(a), 300 + 215 * math.sin(a)
        circ(d, x, y, 26, fill=YEL); rr(d, (x - 11, y - 3, x + 11, y + 14), 3, DARK); d.arc(P(x - 9, y - 18, x + 9, y + 4), 180, 360, fill=DARK, width=4 * S)
    if lt < .9: fx["flash"] = (BLUE2, int(140 * (1 - ep(lt, .5, .9))) if lt > .5 else 0)

def sc_celular(im, d, lt, gt, fx):
    vib = math.sin(lt * 70) * 5 * (1 if (.3 < lt < 1.0) else 0)
    k = bk(lt / .4); oy = (1 - k) * 160
    rr(d, (170 + vib, 40 + oy, 430 + vib, 560 + oy), 40, DARK, BLUE2, 8); rr(d, (190 + vib, 85 + oy, 410 + vib, 520 + oy), 22, (14, 30, 90))
    txt(d, (300 + vib, 130 + oy), "CÓDIGO", 30, BLUE2)
    if .3 < lt < 1.0:  # ondas de notificação
        for j in range(3):
            r = ((lt - .3) * 1.5 + j * .3) % 1 * 90 + 20; circ(d, 300 + vib, 300 + oy, 170 + r, outline=YEL + (int(200 * (1 - r / 110)),), w=3)
    code = "482916"
    for i, c in enumerate(code):
        sh = lt > 1.0 + i * .22
        rr(d, (196 + i * 36 + vib, 170 + oy, 226 + i * 36 + vib, 235 + oy), 6, WHITE if sh else (30, 50, 120))
        if sh: txt(d, (211 + i * 36 + vib, 202 + oy), c, 34, DARK)
    # barra de tempo
    rr(d, (200 + vib, 255 + oy, 400 + vib, 267 + oy), 6, (8, 14, 44)); rr(d, (200 + vib, 255 + oy, 200 + vib + 200 * (1 - ep(lt, 1.0, 3.9)), 267 + oy), 6, YEL)
    press = ep(lt, 2.5, 2.65) * (1 - ep(lt, 2.65, 2.9))
    rr(d, (210 + press * 6 + vib, 300 + press * 4 + oy, 390 - press * 6 + vib, 360 + press * 4 + oy), 28, YEL); txt(d, (300 + vib, 330 + press * 4 + oy), "CONFIRMAR", 26, DARK)
    ck = bk((lt - 2.8) / .35)
    if ck > 0:
        circ(d, 300 + vib, 440 + oy, 44 * ck, fill=BLUE);
        line(d, [(277 + vib, 440 + oy), (293 + vib, 456 + oy), (325 + vib, 420 + oy)], WHITE, int(10 * ck) + 1)
        r = (lt - 2.8) * 300; circ(d, 300 + vib, 440 + oy, r, outline=BLUE2 + (int(255 * max(0, 1 - r / 150)),), w=3)
    c = eo(ep(lt, 1.7, 2.45)); cursor(d, 500 - 190 * c, 560 - 230 * c, press) if lt > 1.7 and lt < 3.2 else None

def sc_download(im, d, lt, gt, fx):
    k = bk(lt / .4)
    circ(d, 300, 300, 220 * k, fill=(14, 28, 90), outline=BLUE2, w=8)
    bounce = abs(math.sin(gt * 5)) * 28 * (1 - ep(lt, 1.2, 1.4))
    poly(d, [(255, 150 + bounce), (345, 150 + bounce), (345, 260 + bounce), (410, 260 + bounce), (300, 380 + bounce), (190, 260 + bounce), (255, 260 + bounce)], WHITE)
    line(d, [(200, 420), (400, 420)], WHITE, 14)
    xk = bk((lt - 1.2) / .3)
    if xk > 0:
        sc_ = 1 + (1 - xk) * 1.2; w = 36
        a = 190 * sc_; line(d, [(300 - a * .9, 300 - a * .9), (300 + a * .9, 300 + a * .9)], RED, w * sc_ ** .5); line(d, [(300 + a * .9, 300 - a * .9), (300 - a * .9, 300 + a * .9)], RED, w * sc_ ** .5)
        circ(d, 300, 300, 220, outline=RED, w=14)
        r = (lt - 1.2) * 520; circ(d, 300, 300, r, outline=RED + (int(255 * max(0, 1 - r / 330)),), w=5)
        if lt < 1.6: fx["flash"] = (RED, int(150 * (1 - ep(lt, 1.2, 1.6))))

def sc_lupa(im, d, lt, gt, fx):
    k = bk(lt / .4); oy = (1 - k) * 160
    rr(d, (50, 100 + oy, 430, 440 + oy), 16, (10, 18, 54), BLUE2, 4)
    rnd = random.Random(5)
    for i in range(10):
        a = rnd.randint(100, 280); line(d, [(80, 135 + oy + i * 30), (80 + a, 135 + oy + i * 30)], rnd.choice([BLUE2, WHITE, BLUE2]), 9)
    hit = ep(lt, 1.9, 2.1)
    line(d, [(80, 285 + oy), (360, 285 + oy)], RED, 12)
    # lupa percorre o código
    if lt < 1.9: u = eo(ep(lt, .4, 1.9)); mx, my = 140 + 130 * u + 25 * math.sin(lt * 6), 190 + 95 * u
    else: mx, my = 270, 285
    my += oy
    circ(d, mx, my, 100, fill=(255, 255, 255, 30), outline=YEL, w=18)
    line(d, [(mx + 71, my + 71), (mx + 150, my + 150)], YEL, 34)
    if hit > 0:
        sz = bk((lt - 1.9) / .35)
        poly(d, [(mx, my - 55 * sz), (mx + 50 * sz, my + 40 * sz), (mx - 50 * sz, my + 40 * sz)], RED, WHITE, 3); txt(d, (mx, my + 14), "!", int(44 * sz) + 1, WHITE)
        txt(d, (300, 540), "CÓDIGO ESCONDIDO" if fx.get('dur', 0) > 6 else "CÓDIGO SUSPEITO", 32, RED if int(gt * 4) % 2 == 0 else WHITE)
        if lt < 2.4: fx["flash"] = (YEL, int(90 * (1 - ep(lt, 1.9, 2.4))))

def sc_cta(im, d, lt, gt, fx):
    k = bk(lt / .5); oy = (1 - k) * 200
    rr(d, (60, 60 + oy, 540, 420 + oy), 30, (12, 22, 66), BLUE2, 5)
    sm = alpha_layer(); hacker(sm, 300, 150 + oy, .62, lt, "wave", eyes=YEL)
    cp = Image.new("L", im.size, 0); ImageDraw.Draw(cp).rounded_rectangle(P(62, 62 + oy, 538, 418 + oy), radius=28 * S, fill=255)
    sm.putalpha(Image.composite(sm.split()[3], Image.new("L", im.size, 0), cp)); im.alpha_composite(sm)
    d2 = ImageDraw.Draw(im)
    txt(d2, (300, 262 + oy), "OPERAÇÃO SIGILO", 36, WHITE); txt(d2, (300, 297 + oy), "NOTÍCIAS • ALERTAS • SEGURANÇA", 15, BLUE2, mono=True)
    press = ep(lt, 4.3, 4.45) * (1 - ep(lt, 4.45, 4.7)); done = lt > 4.45
    bw = 130 - 10 * press
    rr(d2, (300 - bw, 335 + oy + press * 3, 300 + bw, 400 + oy + press * 3), 32, WHITE if done else YEL)
    txt(d2, (300, 367 + oy + press * 3), "SEGUINDO ✓" if done else "SEGUIR", 34, BLUE if done else DARK)
    for i, (lab, c) in enumerate((("ALERTAS", RED), ("DICAS", BLUE), ("DEFESA", YEL))):
        pk = bk((lt - 1.0 - i * .2) / .4)
        if pk > 0:
            rr(d2, (60 + i * 165, 450 + (1 - pk) * 120, 215 + i * 165, 540 + (1 - pk) * 120), 16, c)
            txt(d2, (137 + i * 165, 495 + (1 - pk) * 120), lab, 24, DARK if c == YEL else WHITE)
    # sino balançando
    ang = math.sin(gt * 14) * 18 * (1 if done else .4)
    bx, by = 500, 120 + oy
    pts = [(bx + (x * math.cos(math.radians(ang)) - y * math.sin(math.radians(ang))), by + (x * math.sin(math.radians(ang)) + y * math.cos(math.radians(ang)))) for x, y in [(-20, 22), (-14, -10), (0, -26), (14, -10), (20, 22)]]
    poly(d2, pts, YEL); circ(d2, bx, by + 30, 6, fill=YEL)
    if done:  # confete
        rnd = random.Random(12); t_ = lt - 4.45
        for i in range(34):
            a = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(120, 320)
            x = 300 + math.cos(a) * v * t_; y = 367 + oy + math.sin(a) * v * t_ + 380 * t_ * t_
            c = (YEL, RED, BLUE2, WHITE)[i % 4]; s = 6 + rnd.randint(0, 6)
            if t_ < 1.6: d2.rectangle(P(x, y, x + s, y + s * .6), fill=c)
        r = t_ * 350; circ(d2, 300, 367 + oy, r, outline=YEL + (int(255 * max(0, 1 - r / 200)),), w=4)
    c = eo(ep(lt, 2.8, 4.25)); cursor(d2, 540 - 200 * c, 560 - 190 * c, press) if lt > 2.8 and lt < 5.2 else None

# ================================================================ CENAS DO V5 (caso XZ Utils)
def appear(lt, t0=0.0, d_=.4): return bk((lt - t0) / d_)
def heart(d, x, y, r, col):
    circ(d, x - r * .5, y, r * .55, fill=col); circ(d, x + r * .5, y, r * .55, fill=col)
    poly(d, [(x - r * 1.0, y + r * .15), (x + r * 1.0, y + r * .15), (x, y + r * 1.15)], col)
def tired_face(d, cx, cy, r, gt, slump=0):
    cy += math.sin(gt * 1.6) * 5 + slump
    circ(d, cx, cy, r, fill=SKIN, outline=BLUE2, w=4)
    for ex in (-r * .36, r * .36):
        ell(d, (cx + ex - r * .2, cy + r * .12, cx + ex + r * .2, cy + r * .3), fill=(120, 140, 200))
        line(d, [(cx + ex - r * .18, cy - r * .05), (cx + ex + r * .18, cy - r * .02)], DARK, max(3, r * .06))
    line(d, [(cx - r * .25, cy + r * .5), (cx + r * .25, cy + r * .46)], DARK, max(3, r * .06))
    d.pieslice(P(cx - r, cy - r, cx + r, cy + r * .1), 180, 360, fill=(30, 40, 90))
def stamp(im, text, size, cx, cy, k, rot=-10, col=RED, w=420, h=100):
    st = alpha_layer(); sd = ImageDraw.Draw(st); sc_ = 1 + (1 - k) * 1.5
    rr(sd, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 12, col + (240,), WHITE, 6); txt(sd, (cx, cy), text, size, WHITE)
    st = st.rotate(rot, resample=Image.BICUBIC, center=(cx * S, cy * S))
    if sc_ != 1:
        ns = int(600 * S * sc_); st2 = st.resize((ns, ns), Image.BICUBIC); o = (ns - 600 * S) // 2
        st = st2.crop((o, o, o + 600 * S, o + 600 * S))
    im.alpha_composite(st)

def sc_calmar(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 220
    rr(d, (110, 70 + oy, 490, 510 + oy), 24, WHITE); rr(d, (110, 70 + oy, 490, 170 + oy), 24, RED); d.rectangle(P(110, 130 + oy, 490, 170 + oy), fill=RED)
    txt(d, (300, 120 + oy), "MARÇO", 48, WHITE)
    pr = ep(lt, .2, 1.2); yr = 2020 + int(4 * eo(pr)) if pr < 1 else 2024
    sq = 1 - .3 * abs(math.sin(pr * 4 * math.pi)) if 0 < pr < 1 else 1
    txt(d, (300, 330 + oy), str(yr), int(150 * sq) + 1, DARK if pr < 1 else RED)
    for x in (170, 430): rr(d, (x - 14, 48 + oy, x + 14, 100 + oy), 8, BLUE2)
    if lt > 1.2: r = (lt - 1.2) * 450; circ(d, 300, 300, r, outline=RED + (int(255 * max(0, 1 - r / 300)),), w=5)

def sc_login(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 200
    rr(d, (60, 60 + oy, 540, 400 + oy), 18, (14, 22, 60), BLUE2, 4); rr(d, (80, 80 + oy, 520, 380 + oy), 8, (10, 26, 90))
    poly(d, [(30, 400 + oy), (570, 400 + oy), (550, 425 + oy), (50, 425 + oy)], (24, 36, 90), BLUE2, 2)
    circ(d, 300, 150 + oy, 34, fill=SKIN); circ(d, 300, 142 + oy, 12, fill=DARK); d.pieslice(P(262, 168 + oy, 338, 240 + oy), 180, 360, fill=SKIN)
    rr(d, (190, 235 + oy, 410, 270 + oy), 10, (6, 12, 40), BLUE2, 2)
    n = min(8, max(0, int((lt - .6) * 6)))
    for i in range(n): circ(d, 215 + i * 24, 252 + oy, 6, fill=WHITE)
    if lt < 1.8: rr(d, (225, 295 + oy, 375, 345 + oy), 22, YEL); txt(d, (300, 320 + oy), "ENTRAR", 24, DARK)
    else:
        a = (gt * 420) % 360; d.arc(P(272, 292 + oy, 328, 348 + oy), a, a + 250, fill=YEL, width=8 * S)
    v = min(.5, max(0.0, (lt - 1.8) * .25)) if lt > 1.8 else 0.0
    txt(d, (300, 490 + oy), f"{v:.1f} s".replace(".", ","), 84, RED if v >= .45 else YEL)
    if v >= .5 and int(gt * 3) % 2 == 0: txt(d, (300, 555 + oy), "MAIS LENTO QUE O NORMAL", 20, RED, mono=True)

def sc_ataque(im, d, lt, gt, fx):
    rnd = random.Random(6); nodes = [(300 + rnd.uniform(-240, 240), 300 + rnd.uniform(-240, 240)) for _ in range(30)]
    R = min(lt * 120, 380) if lt < 2.8 else max(0, 380 - (lt - 2.8) * 520)
    inf = [math.hypot(x - 300, y - 300) < R for x, y in nodes]
    for i, (x, y) in enumerate(nodes):
        for j in (i + 1, i + 2, i + 5):
            if j < len(nodes): line(d, [(x, y), nodes[j]], (RED if inf[i] and inf[j] else BLUE) + (110,), 2)
    for i, (x, y) in enumerate(nodes): circ(d, x, y, 10 + 3 * pulse(gt * 2 + i, 1.2), fill=RED if inf[i] else BLUE2)
    if lt > 2.8:
        sz = appear(lt, 2.8, .45)
        poly(d, [(300, 90 + 210 * (1 - sz)), (450, 150), (440, 330), (300, 490 - 0), (160, 330), (150, 150)] if sz > .99 else
             [(300 + (x - 300) * sz, 300 + (y - 300) * sz) for x, y in [(300, 90), (450, 150), (440, 330), (300, 490), (160, 330), (150, 150)]], BLUE, YEL, 8)
        line(d, [(240 * sz + 300 * (1 - sz), 300), (285 * sz + 300 * (1 - sz), 350 * sz + 300 * (1 - sz) * 0 + 0), (365 * sz + 300 * (1 - sz), 250)], WHITE, 26) if False else None
        line(d, [(300 + (-70) * sz, 300 + 10 * sz), (300 + (-20) * sz, 300 + 60 * sz), (300 + 75 * sz, 300 - 45 * sz)], WHITE, 26 * sz)
    else: circ(d, 300, 300, 20 + 6 * pulse(gt, 3), fill=RED)

def sc_engenh(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 220
    poly(d, [(110, 560 + oy), (150, 400 + oy), (450, 400 + oy), (490, 560 + oy)], BLUE, WHITE, 3)
    poly(d, [(270, 400 + oy), (330, 400 + oy), (300, 450 + oy)], WHITE)
    circ(d, 300, 290 + oy, 100, fill=SKIN, outline=BLUE2, w=4)
    d.pieslice(P(200, 190 + oy, 400, 330 + oy), 180, 360, fill=(40, 28, 20))
    blink = (lt % 2.5) < .12
    for ex in (-38, 38):
        circ(d, 300 + ex, 285 + oy, 26, outline=WHITE, w=4)
        if blink: line(d, [(300 + ex - 12, 285 + oy), (300 + ex + 12, 285 + oy)], DARK, 4)
        else: circ(d, 300 + ex + math.sin(gt) * 4, 285 + oy, 7, fill=DARK)
    line(d, [(326, 285 + oy), (274, 285 + oy)], WHITE, 4)
    d.arc(P(260, 310 + oy, 340, 360 + oy), 20, 160, fill=DARK, width=5 * S)
    rr(d, (190, 440 + oy, 410, 540 + oy), 10, (12, 22, 64), BLUE2, 3); circ(d, 300, 490 + oy, 14, fill=YEL + (int(180 + 70 * pulse(gt, 2)),))
    b1 = appear(lt, .8); rr(d, (330 - (1 - b1) * 300, 40, 570 - (1 - b1) * 300, 100), 12, WHITE); txt(d, (450 - (1 - b1) * 300, 70), "ANDRES FREUND", 22, DARK)
    b2 = appear(lt, 2.2)
    if b2 > 0: rr(d, (30 - (1 - b2) * 300, 110, 270 - (1 - b2) * 300, 168), 12, BLUE, WHITE, 3); txt(d, (150 - (1 - b2) * 300, 139), "MICROSOFT", 24, WHITE)

def sc_cpu(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 160
    rr(d, (40, 60 + oy, 560, 270 + oy), 14, (6, 12, 40), BLUE2, 3); rr(d, (40, 60 + oy, 560, 90 + oy), 14, (14, 28, 80)); txt(d, (300, 75 + oy), "terminal — ssh", 14, BLUE2, mono=True)
    lines_ = ["$ ssh servidor", "autenticando...", "conectado.", "$ _"]
    for i, l in enumerate(lines_):
        n = int(len(l) * cl((lt - .4 - i * .6) / .5))
        if n > 0: txt(d, (62, 112 + oy + i * 34), l[:n], 22, YEL if i in (0, 3) else WHITE, mono=True, anchor="lm")
    rr(d, (40, 300 + oy, 560, 540 + oy), 14, (8, 14, 44), BLUE2, 3); txt(d, (300, 322 + oy), "USO DE PROCESSADOR", 18, BLUE2, mono=True)
    rnd = random.Random(9)
    for i in range(12):
        base = 30 + rnd.randint(0, 25); grow = ep(lt, 1.0 + (i - 5) * .25, 1.6 + (i - 5) * .25) if i >= 5 else 0
        h_ = base + 150 * eo(grow); col = RED if grow > .3 else BLUE2
        rr(d, (70 + i * 40, 520 + oy - h_, 98 + i * 40, 520 + oy), 4, col)
    for x in range(60, 540, 24): line(d, [(x, 440 + oy), (x + 12, 440 + oy)], YEL + (200,), 2)
    txt(d, (520, 428 + oy), "normal", 14, YEL, mono=True, anchor="rm")

def sc_compacta(im, d, lt, gt, fx):
    ph = []
    for i in range(3):
        t_ = (lt * .7 + i / 3) % 1; x0, y0 = (90, 300, 510)[i], 70 + 40 * (i % 2)
        e = t_ ** 2; x = x0 + (300 - x0) * e; y = y0 + (330 - y0) * e; sc_ = 1 - .8 * e
        c = (YEL, BLUE2, WHITE)[i]
        rr(d, (x - 45 * sc_, y - 55 * sc_, x + 45 * sc_, y + 55 * sc_), 8, c); line(d, [(x - 25 * sc_, y - 20 * sc_), (x + 25 * sc_, y - 20 * sc_)], DARK, 6 * sc_); line(d, [(x - 25 * sc_, y + 5 * sc_), (x + 25 * sc_, y + 5 * sc_)], DARK, 6 * sc_)
    sq = 1 + .06 * math.sin(lt * 9)
    rr(d, (300 - 120 * sq, 340, 300 + 120 * sq, 520), 14, YEL, WHITE, 5); rr(d, (300 - 120 * sq, 340, 300 + 120 * sq, 380), 14, (255, 235, 120))
    for y in range(350, 520, 22): rr(d, (292, y, 308, y + 11), 3, DARK)
    txt(d, (300 + 70, 450), "XZ", 52, DARK) if False else txt(d, (300, 455), "XZ", 60, DARK)

def sc_servidor(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 160
    for r_, x0 in enumerate((50, 220, 390)):
        hl = r_ == 1
        rr(d, (x0, 60 + oy, x0 + 160, 400 + oy), 12, (12, 20, 56), YEL if hl else BLUE2, 5 if hl else 3)
        for i in range(6):
            y = 78 + oy + i * 53; rr(d, (x0 + 12, y, x0 + 148, y + 42), 6, (22, 36, 96))
            on = random.Random(int(gt * 4) + r_ * 7 + i).random() > .45
            circ(d, x0 + 28, y + 21, 6, fill=(BLUE2 if on else (40, 60, 120)))
            if hl and i == 2: rr(d, (x0 + 50, y + 6, x0 + 138, y + 36), 6, YEL); txt(d, (x0 + 94, y + 21), "XZ", 22, DARK)
    for i, (lab, c) in enumerate((("BANCOS", BLUE), ("EMPRESAS", RED), ("GOVERNOS", YEL))):
        b = appear(lt, 1.2 + i * .8)
        if b > 0: rr(d, (50 + i * 175, 450 + (1 - b) * 100, 215 + i * 175, 520 + (1 - b) * 100), 16, c); txt(d, (132 + i * 175, 485 + (1 - b) * 100), lab, 24, DARK if c == YEL else WHITE)

def sc_porta(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 120
    rr(d, (140, 50 + oy, 460, 530 + oy), 10, (8, 14, 44), BLUE2, 6)
    o = eo(ep(lt, 3.0, 3.9))
    if o > 0:
        for j in range(5): rr(d, (160 - j * 0, 70 + oy + j * 4, 440, 510 + oy - j * 4), 6, RED + (int(40 + 30 * pulse(gt * 3, 1)),)) if j == 0 else None
        poly(d, [(170, 80 + oy), (430, 80 + oy), (470, 560 + oy), (130, 560 + oy)], RED + (90,))
    x1 = 170 + 260 * (1 - .78 * o)
    poly(d, [(170, 75 + oy), (x1, 75 + oy + 40 * o), (x1, 505 + oy - 40 * o), (170, 505 + oy)], (30, 52, 130), WHITE, 4)
    if o < .6:
        kx = 80 + 300 * eo(ep(lt, .4, 1.8)); ky = 300 + oy
        rot = ep(lt, 2.0, 2.8) * 70
        circ(d, kx, ky, 26, outline=YEL, w=10); line(d, [(kx + 26, ky), (kx + 130, ky)], YEL, 10); line(d, [(kx + 100, ky), (kx + 100, ky + 22)], YEL, 9); line(d, [(kx + 120, ky), (kx + 120, ky + 16)], YEL, 9)
    rr(d, (360, 290 + oy, 400, 330 + oy), 8, (14, 22, 60), YEL, 3) if o < .6 else None
    if o > 0:
        txt(d, (300, 560), "SEM SENHA", 38, YEL if int(gt * 4) % 2 == 0 else WHITE)
        if lt < 4.2: fx["flash"] = (RED, int(110 * (1 - ep(lt, 3.0, 4.2))))

def sc_ampulh(im, d, lt, gt, fx):
    k = appear(lt); sc_ = .8 + .2 * k
    f = lambda x, y: (300 + (x - 300) * sc_, 300 + (y - 300) * sc_)
    fr = (lt * .16) % 1
    poly(d, [f(170, 90), f(430, 90), f(300, 300)], (255, 255, 255, 40), WHITE, 4); poly(d, [f(300, 300), f(170, 510), f(430, 510)], (255, 255, 255, 40), WHITE, 4)
    yt = 90 + 205 * fr; wt = 130 * (300 - yt) / 210
    poly(d, [f(300 - wt, yt), f(300 + wt, yt), f(300, 298)], YEL)
    hb = 205 * fr; yb = 510 - hb; wb = 130 * (yb - 300) / 210
    if hb > 2: poly(d, [f(300 - wb, yb), f(300 + wb, yb), f(430, 510), f(170, 510)], YEL)
    line(d, [f(300, 300), f(300, max(305, yb))], YEL, 4)
    rr(d, (*f(150, 66), *f(450, 94)), 8, BLUE2); rr(d, (*f(150, 506), *f(450, 534)), 8, BLUE2)
    for i in range(6): txt(d, (300, 580), "• " * (1 + int(lt * 1.5) % 6), 28, BLUE2, mono=True)

def sc_commits(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 160
    rr(d, (50, 40 + oy, 550, 200 + oy), 20, (12, 22, 66), BLUE2, 4)
    circ(d, 130, 120 + oy, 44, fill=WHITE, outline=YEL, w=4); circ(d, 114, 112 + oy, 6, fill=DARK); circ(d, 146, 112 + oy, 6, fill=DARK); d.arc(P(110, 118 + oy, 150, 148 + oy), 20, 160, fill=DARK, width=4 * S)
    txt(d, (330, 98 + oy), "Jia Tan", 38, WHITE); txt(d, (330, 140 + oy), "contribuidor do projeto", 15, BLUE2, mono=True); rr(d, (230, 160 + oy, 440, 188 + oy), 14, YEL); txt(d, (335, 174 + oy), "AJUDANDO ✓" if False else "AJUDANDO", 16, DARK)
    msgs = ["corrige erro de digitação", "atualiza a documentação", "melhora o desempenho", "ajusta pequenos testes", "corrige um detalhe"]
    for i, m in enumerate(msgs):
        b = appear(lt, .7 + i * .75, .35)
        if b > 0:
            y = 240 + oy + i * 62
            rr(d, (60 + (1 - b) * 260, y, 540 + (1 - b) * 260, y + 50), 12, (18, 30, 86), BLUE2, 2)
            circ(d, 92 + (1 - b) * 260, y + 25, 15, fill=YEL); line(d, [(84 + (1 - b) * 260, y + 25), (90 + (1 - b) * 260, y + 32), (101 + (1 - b) * 260, y + 18)], DARK, 4)
            txt(d, (122 + (1 - b) * 260, y + 25), m, 20, WHITE, mono=True, anchor="lm")
    yr = 2021 + int(2 * ep(lt, .5, fx["dur"] * .9))
    txt(d, (500, 100 + oy), str(yr), 30, YEL, mono=True) if False else None

def sc_confianca(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 160
    txt(d, (300, 90 + oy), "CONFIANÇA", 50, WHITE)
    p_ = eo(ep(lt, .4, fx["dur"] * .9))
    rr(d, (60, 180 + oy, 540, 260 + oy), 40, (8, 14, 44), BLUE2, 4)
    w_ = 468 * p_; col = tuple(int(RED[i] * (1 - p_) + YEL[i] * p_) for i in range(3))
    if w_ > 12: rr(d, (66, 186 + oy, 66 + w_, 254 + oy), 34, col)
    txt(d, (300, 350 + oy), f"{int(p_ * 100)}%", 110, WHITE)
    for i, y in enumerate((2021, 2022, 2023)):
        x = 90 + i * 210; circ(d, x, 450 + oy, 10, fill=YEL if p_ > i / 2.5 else (40, 60, 130)); txt(d, (x, 485 + oy), str(y), 22, BLUE2, mono=True)
    line(d, [(90, 450 + oy), (510, 450 + oy)], BLUE2, 3)
    for i in range(6):
        t_ = (lt * .6 + i / 6) % 1; heart(d, 70 + 468 * p_ * ((i * 0.37) % 1), 175 + oy - t_ * 120, 14, RED + (int(255 * (1 - t_)),))

def sc_esgotado(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 200
    tired_face(d, 300, 220 + oy, 110, gt, slump=4 * math.sin(gt))
    for i in range(3):
        t_ = (lt * .5 + i / 3) % 1; txt(d, (450 + i * 25, 150 + oy - t_ * 90), "Z", int(26 + i * 10), YEL + (int(255 * (1 - t_)),))
    rr(d, (130, 390 + oy, 440, 470 + oy), 12, (8, 14, 44), WHITE, 5); rr(d, (440, 415 + oy, 462, 445 + oy), 4, WHITE)
    lv = max(.08, .6 - lt * .08); blink = int(gt * 3) % 2 == 0
    rr(d, (140, 400 + oy, 140 + 290 * lv, 460 + oy), 8, RED if blink or lv > .2 else (120, 20, 30))
    for i, (lab, c) in enumerate((("SOZINHO", BLUE), ("SEM PAGAMENTO", RED))):
        b = appear(lt, 1.0 + i * .9)
        if b > 0: rr(d, (60 + i * 250, 510 + (1 - b) * 90, 290 + i * 250 - (30 if i else 0), 570 + (1 - b) * 90), 14, c); txt(d, (175 + i * 250 - (15 if i else 0), 540 + (1 - b) * 90), lab, 22, WHITE)

def sc_pressao(im, d, lt, gt, fx):
    tired_face(d, 300, 300, 62, gt)
    bub = [("CADÊ A ATUALIZAÇÃO?", (30, 40, 360, 105), RED, WHITE, .5), ("ANDA LOGO!", (300, 140, 560, 205), WHITE, DARK, 1.7), ("PRECISA DE NOVO RESPONSÁVEL", (20, 410, 470, 475), YEL, DARK, 3.0), ("ALGUÉM ASSUME!", (260, 500, 580, 565), BLUE, WHITE, 4.3)]
    for lab, (x0, y0, x1, y1), c, tc, t0 in bub:
        b = appear(lt, t0, .35)
        if b > 0:
            sh = math.sin(lt * 50) * 4 * max(0, 1 - (lt - t0) * 3)
            cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2; w_, h_ = (x1 - x0) / 2 * b, (y1 - y0) / 2 * b
            rr(d, (cxm - w_ + sh, cym - h_, cxm + w_ + sh, cym + h_), 22, c); txt(d, (cxm + sh, cym), lab, int(19 * b) + 1, tc)
            circ(d, x0 + 4 if x0 > 100 else x1 - 4, y1 + 6, 14, fill=DARK, outline=RED, w=3)

def sc_chave(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 120
    tired_face(d, 110, 330 + oy, 80, gt)
    sm = alpha_layer(); done = lt > 3.0
    hacker(sm, 490, 400 + oy, .55, lt, "idle", eyes=RED if done else YEL); im.alpha_composite(sm); d2 = ImageDraw.Draw(im)
    t_ = eo(ep(lt, 1.0, 3.0)); x = 190 + 230 * t_; y = 330 + oy - 90 * math.sin(t_ * math.pi)
    ang = t_ * 360 * 1.0
    circ(d2, x, y, 24, outline=YEL, w=9); line(d2, [(x + 24, y), (x + 100, y)], YEL, 9); line(d2, [(x + 82, y), (x + 82, y + 18)], YEL, 8); line(d2, [(x + 98, y), (x + 98, y + 14)], YEL, 8)
    if done:
        b = appear(lt, 3.0, .4); rr(d2, (150, 40 + oy, 450, 110 + oy), 16, YEL if int(gt * 3) % 2 else WHITE); txt(d2, (300, 75 + oy), "PODE PUBLICAR", int(30 * b) + 1, DARK)
        r = (lt - 3.0) * 400; circ(d2, 490, 400 + oy, r, outline=RED + (int(255 * max(0, 1 - r / 250)),), w=5)

def sc_testes(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 120
    for i, x0 in enumerate((40, 220, 400)):
        rr(d, (x0, 70 + oy, x0 + 160, 280 + oy), 12, (14, 24, 70), BLUE2, 3); txt(d, (x0 + 80, 96 + oy), f"teste{i+1}.xz", 18, BLUE2, mono=True)
        rnd = random.Random(i + int(gt * 5) * 0)
        for r_ in range(6): txt(d, (x0 + 14, 132 + oy + r_ * 22), "".join(rnd.choice("01") for _ in range(11)), 15, (110, 140, 220), mono=True, anchor="lm")
    sy = 70 + oy + 210 * ep(lt, 1.0, 2.8)
    if 1.0 < lt < 2.9: d.rectangle(P(30, sy - 3, 570, sy + 3), fill=YEL)
    if lt > 2.0:
        b = appear(lt, 2.0 + .01); rr(d, (230, 150 + oy, 370, 190 + oy), 6, RED); txt(d, (300, 170 + oy), "01100101", 16, WHITE, mono=True)
    if lt > 3.0: txt(d, (300, 320 + oy), "CÓDIGO ESCONDIDO", 26, RED if int(gt * 4) % 2 == 0 else WHITE)
    for i, (lab, t0) in enumerate((("5.6.0", 4.2), ("5.6.1", 5.0))):
        b = appear(lt, t0, .3)
        if b > 0: rr(d, (80 + i * 240, 360 + oy, 260 + i * 240, 430 + oy), 14, RED if b > .9 else YEL); txt(d, (170 + i * 240, 395 + oy), lab, int(40 * b) + 1, WHITE)
    for i in range(4):
        b = appear(lt, 6.4 + i * .35, .3)
        if b > 0:
            x0 = 70 + i * 125; rr(d, (x0, 470 + oy, x0 + 100, 560 + oy), 10, (14, 24, 70), RED if int(gt * 3) % 2 else BLUE2, 3); txt(d, (x0 + 50, 515 + oy), "TESTE", int(16 * b) + 1, WHITE, mono=True); circ(d, x0 + 14, 484 + oy, 5, fill=RED)

def sc_mapa(im, d, lt, gt, fx):
    cx, cy, Rg = 300, 300, 240
    circ(d, cx, cy, Rg + 6, outline=BLUE2, w=3)
    for r_ in (80, 160): d.arc(P(cx - Rg, cy - r_ * .5, cx + Rg, cy + r_ * .5), 0, 360, fill=BLUE + (120,), width=2 * S)
    org = [(250, 300), (380, 250), (310, 380)]
    R = lt * 38
    for gx in range(-13, 14):
        for gy in range(-13, 14):
            x, y = cx + gx * 18, cy + gy * 18
            if math.hypot(x - cx, y - cy) > Rg: continue
            inf = any(math.hypot(x - ox, y - oy_) < R for ox, oy_ in org)
            circ(d, x, y, 4 if not inf else 5 + 1.5 * pulse(gt * 3 + gx, 1), fill=RED if inf else BLUE2 + (150,))
    for ox, oy_ in org:
        r = (lt * 150) % 160; circ(d, ox, oy_, r, outline=RED + (int(220 * (1 - r / 160)),), w=3)
    txt(d, (300, 570), "MILHÕES DE SERVIDORES", 26, RED if int(gt * 3) % 2 == 0 else WHITE)

def sc_relogio2(im, d, lt, gt, fx):
    sc_relogio(im, d, lt, gt, fx)
    rr(d, (210, 384, 390, 442), 10, DARK); txt(d, (300, 413), "0,5 s", 34, YEL if int(gt * 4) % 2 == 0 else RED)

def sc_misterio(im, d, lt, gt, fx):
    sm = alpha_layer(); hacker(sm, 300, 420, 1.15, lt, "idle", eyes=(40, 40, 60)); im.alpha_composite(sm); d2 = ImageDraw.Draw(im)
    for i in range(7):
        t_ = (lt * .35 + i / 7) % 1; x = 90 + (i * 83) % 420; txt(d2, (x, 460 - t_ * 440), "?", int(40 + (i * 13) % 40), BLUE2 + (int(200 * (1 - t_)),))
    txt(d2, (300, 150), "?", int(150 + 20 * math.sin(gt * 3)), YEL + (200,))
    b = appear(lt, .8, .5)
    if b > 0: rr(d2, (30, 60, 200, 190), 10, WHITE); rr(d2, (45, 75, 105, 135), 6, (200, 205, 220)); txt(d2, (75, 105), "?", 46, DARK); txt(d2, (150, 160), "JIA TAN", 18, DARK); line(d2, [(115, 90), (185, 90)], DARK, 4); line(d2, [(115, 110), (170, 110)], DARK, 4)
    k_ = appear(lt, fx["dur"] * .78, .3)
    if k_ > 0: stamp(im, "NADA PROVADO", 48, 300, 520, k_, rot=-8, col=RED, w=480, h=96)

def sc_pastas(im, d, lt, gt, fx):
    for i, (x0, c) in enumerate(((40, BLUE), (210, YEL), (380, RED))):
        b = appear(lt, .1 + i * .25); oy = (1 - b) * 220
        rr(d, (x0, 240 + oy, x0 + 90, 262 + oy), 6, c); rr(d, (x0, 252 + oy, x0 + 180, 420 + oy), 12, c)
        op = ep(lt, 1.0 + i * .3, 1.5 + i * .3)
        for j in range(3):
            t_ = (lt * .8 + j / 3 + i * .2) % 1
            if op > 0: rr(d, (x0 + 30 + j * 25, 230 + oy - t_ * 160, x0 + 90 + j * 25, 290 + oy - t_ * 160), 4, WHITE + (int(255 * (1 - t_)),))
        txt(d, (x0 + 90, 336 + oy), "SIGILO", 22, DARK if c == YEL else WHITE)
    sk = appear(lt, 1.8, .3)
    if sk > 0: stamp(im, "CONFIDENCIAL", 54, 300, 140, sk, rot=-9, col=RED, w=500, h=100)
    txt(d, (300, 520), "ARQUIVOS ABERTOS", 32, YEL if int(gt * 3) % 2 == 0 else WHITE)


# ================================================================ CENAS: "BRASIL SOB ATAQUE"
LB = (214, 228, 252)  # azul-claro de apoio (estilo claro)
BR = [(-60.0, 5.2), (-51.6, 4.2), (-50.0, 1.8), (-50.7, 0.0), (-48.0, -1.0), (-44.5, -2.3), (-40.0, -2.9), (-37.0, -4.9), (-34.9, -6.5), (-35.2, -9.0), (-37.0, -11.0), (-38.8, -13.0), (-39.2, -17.7), (-40.0, -20.0), (-41.0, -22.0), (-44.0, -23.0), (-48.0, -26.0), (-48.7, -28.5), (-50.5, -30.5), (-53.4, -33.7), (-57.6, -30.2), (-55.5, -28.0), (-54.5, -26.0), (-57.8, -22.0), (-58.2, -20.1), (-57.9, -17.5), (-60.2, -16.3), (-60.0, -13.5), (-65.4, -10.0), (-68.6, -11.2), (-72.5, -9.5), (-73.5, -7.5), (-70.0, -4.2), (-69.9, -1.0), (-67.0, 2.0), (-65.0, 1.5), (-63.8, 4.0)]
def ll(lon, lat): return (300 + (lon + 54) * 11.5, 300 - (lat + 14) * 11.5)
def cs_(fx, i, default): 
    c = fx.get("cs", [])
    return c[i] if i < len(c) else default
def rotated(im, fn, ang, cx, cy):
    lay = alpha_layer(); fn(ImageDraw.Draw(lay))
    lay = lay.rotate(ang, resample=Image.BICUBIC, center=(cx * S, cy * S)); im.alpha_composite(lay)

def sc_contador5(im, d, lt, gt, fx):
    n = min(5, 1 + int(lt * 2.0)); u = lt - (n - 1) / 2.0
    pop = bk(u / .3)
    for r_, a in ((250, 38), (190, 62), (130, 100)): circ(d, 300, 290, r_ * (0.95 + .08 * pulse(gt, 2)), fill=RED + (a,))
    txt(d, (300, 290), str(n), int(400 * (.55 + .45 * pop)) + 1, WHITE)
    for i in range(5): circ(d, 110 + i * 95, 55, 20, fill=RED if i < n else None, outline=WHITE, w=4)
    txt(d, (300, 520), "ATAQUES", 64, YEL)
    if n == 5 and u > .3:
        r = (u - .3) * 400; circ(d, 300, 290, r, outline=YEL + (int(255 * max(0, 1 - r / 280)),), w=6)
    if u < .25: fx["flash"] = (WHITE, int(90 * (1 - u / .25)))

def sc_calnov(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 220
    rr(d, (60, 40 + oy, 540, 550 + oy), 24, WHITE, DARK, 5); rr(d, (60, 40 + oy, 540, 150 + oy), 24, RED, DARK, 5); d.rectangle(P(62, 110 + oy, 538, 150 + oy), fill=RED)
    txt(d, (300, 95 + oy), "NOVEMBRO 2026", 44, WHITE)
    hl = {4: 1.0, 11: 1.7, 15: 2.4, 21: 3.1, 27: 3.8}
    for idx in range(35):
        r_, c_ = divmod(idx, 7); x, y = 85 + c_ * 62, 180 + oy + r_ * 70
        on = idx in hl and lt > hl[idx]
        if on:
            b = bk((lt - hl[idx]) / .3); rr(d, (x - 3 * b, y - 3 * b, x + 52 + 3 * b, y + 52 + 3 * b), 10, RED, DARK, 3)
            circ(d, x + 26, y + 26, 14, outline=WHITE, w=3); line(d, [(x + 26, y + 6), (x + 26, y + 46)], WHITE, 2); line(d, [(x + 6, y + 26), (x + 46, y + 26)], WHITE, 2)
        else: rr(d, (x, y, x + 52, y + 52), 10, LB)

def sc_mapabr(im, d, lt, gt, fx):
    k = appear(lt); sc_ = .85 + .15 * k
    f = lambda x, y: (300 + (x - 300) * sc_, 300 + (y - 300) * sc_)
    pts = [f(*ll(*p)) for p in BR]
    poly(d, pts, (22, 52, 150), BLUE2, 4)
    for gx in range(-8, 9):
        for gy in range(-8, 9):
            x, y = 300 + gx * 26, 310 + gy * 26
            if x < 70 or x > 530: continue
            # pontos dentro do polígono (teste simples)
            inside = False; px_, py_ = x, y
            for i in range(len(pts)):
                x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
                if (y1 > py_) != (y2 > py_) and px_ < (x2 - x1) * (py_ - y1) / (y2 - y1 + 1e-9) + x1: inside = not inside
            if inside: circ(d, x, y, 2.5, fill=BLUE2 + (150,))
    pins = [("TESOURO", (-47.9, -15.8), (10, -34), cs_(fx, 0, 1.0) + .1), ("CAIXA VIDA", (-48.6, -17.2), (-120, 6), cs_(fx, 0, 1.0) + 1.5), ("PETROBRAS", (-43.2, -22.9), (40, 8), cs_(fx, 1, 2.0) + .2), ("INEP", (-47.0, -14.8), (30, -52), cs_(fx, 1, 2.0) + 1.0), ("PORTO DE SANTOS", (-46.3, -24.0), (-190, 14), cs_(fx, 1, 2.0) + 2.0)]
    for lab, (lo, la), (dx, dy), t0 in pins:
        x, y = f(*ll(lo, la)); b = bk((lt - t0) / .35)
        if b <= 0: continue
        r = (lt - t0) * 90 % 70; circ(d, x, y, r, outline=RED + (int(220 * (1 - r / 70)),), w=3)
        circ(d, x, y, 11 * b, fill=RED, outline=WHITE, w=3)
        w_ = len(lab) * 11 + 24
        bx = x + dx; by = y + dy
        rr(d, (bx, by - 17, bx + w_, by + 17), 10, DARK + (230,), RED, 2); txt(d, (bx + w_ / 2, by), lab, 17, WHITE)

def _icon(d, kind, x, y, col):
    if kind == 0: txt(d, (x, y), "$", 54, col)
    elif kind == 1: d.pieslice(P(x - 30, y - 28, x + 30, y + 24), 180, 360, fill=col); line(d, [(x, y - 2), (x, y + 30)], col, 5); d.arc(P(x - 12, y + 22, x + 2, y + 36), 0, 180, fill=col, width=5 * S)
    elif kind == 2: poly(d, [(x + 6, y - 32), (x - 20, y + 4), (x - 2, y + 4), (x - 8, y + 32), (x + 22, y - 6), (x + 2, y - 6)], col)
    elif kind == 3: rr(d, (x - 30, y - 22, x - 2, y + 24), 3, col); rr(d, (x + 2, y - 22, x + 30, y + 24), 3, col)
    else: rr(d, (x - 28, y - 20, x + 28, y + 24), 4, col); line(d, [(x - 28, y - 4), (x + 28, y - 4)], DARK, 4); line(d, [(x, y - 20), (x, y + 24)], DARK, 4)

def sc_mira(im, d, lt, gt, fx):
    labs = ["DINHEIRO PÚBLICO", "PREVIDÊNCIA", "ENERGIA", "EDUCAÇÃO", "COMÉRCIO EXTERIOR"]
    step = fx["dur"] * .7 / 5
    for i, lab in enumerate(labs):
        t0 = .2 + i * step; b = bk((lt - t0) / .35)
        if b <= 0: continue
        y = 40 + i * 106; off = (1 - b) * 400
        rr(d, (40 + off, y, 560 + off, y + 90), 16, (70, 8, 24), RED, 3)
        circ(d, 100 + off, y + 45, 34, fill=WHITE); _icon(d, i, 100 + off, y + 45, DARK)
        txt(d, (176 + off, y + 45), lab, 26, WHITE, anchor="lm")
        lk = ep(lt, t0 + .3, t0 + .8)
        if lk > 0:
            r = 26 * (2 - lk); cx_, cy_ = 522 + off, y + 45
            circ(d, cx_, cy_, r, outline=RED, w=4); line(d, [(cx_ - r - 8, cy_), (cx_ + r + 8, cy_)], RED, 3); line(d, [(cx_, cy_ - r - 8), (cx_, cy_ + r + 8)], RED, 3)

def sc_videos(im, d, lt, gt, fx):
    def card(dd, lab, col, x0):
        rr(dd, (x0, 90, x0 + 240, 480), 22, (10, 16, 46), BLUE2, 4); rr(dd, (x0 + 14, 104, x0 + 226, 340), 14, col)
        poly(dd, [(x0 + 100, 190), (x0 + 100, 260), (x0 + 160, 225)], WHITE)
        txt(dd, (x0 + 120, 380), lab, 26, WHITE); rr(dd, (x0 + 14, 410, x0 + 226, 424), 7, (30, 44, 110)); rr(dd, (x0 + 14, 410, x0 + 14 + 212 * ((lt * .2) % 1), 424), 7, YEL)
        rr(dd, (x0 + 14, 440, x0 + 120, 452), 6, (30, 44, 110))
    a = eo(ep(lt, 0, .5)); b = eo(ep(lt, .4, .9)); bob = math.sin(gt * 2) * 6
    rotated(im, lambda dd: card(dd, "O CASO DA CAIXA", BLUE, 30 - (1 - a) * 400), -7, 150, 300 + bob)
    rotated(im, lambda dd: card(dd, "O CASO DO PORTO", RED, 330 + (1 - b) * 400), 7, 450, 300 - bob)
    d2 = ImageDraw.Draw(im); txt(d2, (300, 555), "NO CANAL", 30, YEL)

def sc_padrao(im, d, lt, gt, fx):
    pts = [(300 + 200 * math.cos(math.radians(-90 + 72 * i)), 300 + 200 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    circ(d, 300, 300, 16 + 4 * pulse(gt, 3), fill=DARK)
    for i, p in enumerate(pts):
        b = bk((lt - .6 - i * .25) / .3)
        if b > 0:
            circ(d, p[0], p[1], 24 * b, fill=RED, outline=DARK, w=5)
            line(d, [(300, 300), (300 + (p[0] - 300) * eo(ep(lt, .6 + i * .25, 1.1 + i * .25)), 300 + (p[1] - 300) * eo(ep(lt, .6 + i * .25, 1.1 + i * .25)))], DARK, 4)
    for i in range(5):
        t0 = 1.9 + i * .2; q = eo(ep(lt, t0, t0 + .4)); a_, b_ = pts[i], pts[(i + 1) % 5]
        if q > 0: line(d, [a_, (a_[0] + (b_[0] - a_[0]) * q, a_[1] + (b_[1] - a_[1]) * q)], RED, 7)
    k_ = appear(lt, fx["dur"] * .55, .3)
    if k_ > 0: stamp(im, "PADRÃO", 70, 300, 300, k_, rot=-8, col=DARK, w=360, h=120)

def sc_tesouro(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 200
    poly(d, [(300, 40 + oy), (500, 130 + oy), (100, 130 + oy)], WHITE, BLUE2, 4)
    rr(d, (100, 130 + oy, 500, 160 + oy), 4, WHITE); txt(d, (300, 146 + oy), "TESOURO NACIONAL", 18, DARK)
    br = ep(lt, 1.0, 2.2)
    for i in range(5):
        x = 120 + i * 72; sh = math.sin(lt * 60 + i) * 5 * br
        rr(d, (x + sh, 170 + oy, x + 44 + sh, 340 + oy), 6, WHITE if br < .3 or i % 2 else (190, 200, 230))
    rr(d, (90, 340 + oy, 510, 370 + oy), 4, WHITE); rr(d, (70, 370 + oy, 530, 395 + oy), 4, (190, 200, 230))
    if br > 0:
        for j in range(4):
            y = 180 + oy + j * 45; w_ = 100 + (j * 77 + int(gt * 20) * 31) % 300
            d.rectangle(P(80 + (j * 61) % 200, y, 80 + (j * 61) % 200 + w_ * br, y + 14), fill=RED + (210,))
    t0 = cs_(fx, 1, 3.0); n = int(30000 * eo(ep(lt, t0, t0 + 2.0)))
    rr(d, (60, 430 + oy, 540, 560 + oy), 18, (6, 12, 40), RED, 4)
    txt(d, (300, 485 + oy), f"{n:,}".replace(",", "."), 70, YEL if n < 30000 or int(gt * 4) % 2 == 0 else WHITE); txt(d, (300, 535 + oy), "CADASTROS ATINGIDOS", 22, WHITE)
    if br > 0 and br < .15: fx["flash"] = (RED, 90)

def sc_pix(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 220
    rr(d, (50, 70 + oy, 550, 380 + oy), 26, WHITE, DARK, 5)
    # logo losango + chave
    cx, cy = 150, 170 + oy; poly(d, [(cx, cy - 55), (cx + 55, cy), (cx, cy + 55), (cx - 55, cy)], BLUE, DARK, 4); poly(d, [(cx, cy - 25), (cx + 25, cy), (cx, cy + 25), (cx - 25, cy)], WHITE)
    txt(d, (350, 150 + oy), "CHAVE PIX", 40, DARK); txt(d, (350, 200 + oy), "seu.dinheiro@pix", 20, BLUE, mono=True)
    for i in range(3): rr(d, (230, 240 + oy + i * 36, 520 - i * 70, 262 + oy + i * 36), 8, LB)
    cr = ep(lt, 1.0, 1.6)
    if cr > 0:
        ys = [70 + oy, 140 + oy, 190 + oy, 250 + oy, 320 + oy, 380 + oy]; xs = [300, 280, 330, 290, 320, 300]
        for i in range(5): d.line([(xs[i] * S, ys[i] * S), (xs[i + 1] * S, ys[i + 1] * S) if i + 1 <= 5 and cr * 5 > i else (xs[i] * S, ys[i] * S)], fill=RED, width=8 * S)
    for i in range(10):
        t_ = (lt * .8 + i / 10) % 1
        if lt > 1.2: circ(d, 300 + (i - 5) * 50 * t_ * 1.5, 380 + oy + t_ * 160, 10, fill=RED + (int(255 * (1 - t_)),))
    t0 = cs_(fx, 0, 0.2); n = int(4000 * eo(ep(lt, t0, t0 + 1.4)))
    txt(d, (300, 470 + oy), f"{n:,}".replace(",", "."), 90, RED); txt(d, (300, 540 + oy), "CHAVES PIX", 30, DARK)

def sc_caixa(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 200
    # guarda-chuva (previdência) sobre prédio
    d.pieslice(P(120, 40 + oy, 480, 300 + oy), 180, 360, fill=BLUE, outline=DARK, width=5 * S)
    for i in range(1, 4): line(d, [(300, 170 + oy), (120 + i * 90, 170 + oy)], DARK, 3)
    line(d, [(300, 170 + oy), (300, 330 + oy)], DARK, 8); d.arc(P(270, 310 + oy, 300, 350 + oy), 0, 180, fill=DARK, width=8 * S)
    rr(d, (130, 340 + oy, 470, 480 + oy), 8, WHITE, DARK, 5)
    for i in range(4):
        for j in range(2): rr(d, (155 + i * 80, 360 + oy + j * 55, 195 + i * 80, 395 + oy + j * 55), 4, BLUE if (i + j) % 2 else YEL)
    rr(d, (80, 500 + oy, 520, 560 + oy), 12, DARK); txt(d, (300, 530 + oy), "CAIXA VIDA E PREVIDÊNCIA", 24, WHITE)
    lk = ep(lt, .8, 1.6); r = 150 * (1.8 - .8 * eo(lk)) if lk > 0 else 0
    if lk > 0:
        circ(d, 300, 330 + oy, r, outline=RED, w=7); line(d, [(300 - r - 25, 330 + oy), (300 + r + 25, 330 + oy)], RED, 5); line(d, [(300, 330 + oy - r - 25), (300, 330 + oy + r + 25)], RED, 5)
    if lt > 1.6: circ(d, 300, 330 + oy, 150, outline=RED + (int(120 + 100 * pulse(gt, 3)),), w=3)

def sc_petrobras(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 200
    rr(d, (60, 500 + oy, 540, 540 + oy), 6, (50, 6, 20), RED, 3)
    poly(d, [(230, 500 + oy), (330, 500 + oy), (300, 330 + oy), (260, 330 + oy)], (90, 12, 34), WHITE, 4)
    ang = math.radians(math.sin(gt * 2.2) * 14); px, py = 280, 330 + oy
    def rot(x, y): dx, dy = x - px, y - py; return (px + dx * math.cos(ang) - dy * math.sin(ang), py + dx * math.sin(ang) + dy * math.cos(ang))
    beam = [rot(80, 322 + oy), rot(480, 322 + oy), rot(480, 346 + oy), rot(80, 346 + oy)]; poly(d, beam, YEL, WHITE, 3)
    hx, hy = rot(80, 334 + oy); line(d, [(hx, hy), (hx, 500 + oy)], WHITE, 6); poly(d, [rot(40, 360 + oy), rot(100, 300 + oy), rot(100, 372 + oy)], YEL, WHITE, 3)
    cx_, cy_ = rot(470, 346 + oy); circ(d, cx_, cy_ + 20, 38, fill=WHITE, outline=RED, w=5)
    circ(d, px, py, 18, fill=RED, outline=WHITE, w=4)
    for i in range(7):  # chama
        t_ = ((gt * 1.7) + i / 7) % 1; fx_ = 450 + math.sin(gt * 8 + i) * 12; fy_ = 470 + oy - t_ * 190
        circ(d, fx_, fy_, 26 * (1 - t_) + 4, fill=(YEL if i % 2 else RED) + (int(230 * (1 - t_)),))
    rr(d, (430, 470 + oy, 470, 500 + oy), 4, (90, 12, 34))
    lk = ep(lt, 1.0, 1.8)
    if lk > 0:
        r = 120 * (1.8 - .8 * eo(lk)); circ(d, 300, 330 + oy, r, outline=WHITE, w=5); line(d, [(300 - r - 20, 330 + oy), (300 + r + 20, 330 + oy)], WHITE, 4); line(d, [(300, 330 + oy - r - 20), (300, 330 + oy + r + 20)], WHITE, 4)

def sc_enem(im, d, lt, gt, fx):
    k = appear(lt); oy = (1 - k) * 220; shk = math.sin(gt * 40) * 3 * (1 if lt > 3.0 else 0)
    rr(d, (50 + shk, 50 + oy, 420 + shk, 560 + oy), 16, WHITE, DARK, 5); rr(d, (50 + shk, 50 + oy, 420 + shk, 120 + oy), 16, BLUE, DARK, 5); d.rectangle(P(52 + shk, 90 + oy, 418 + shk, 120 + oy), fill=BLUE)
    txt(d, (235 + shk, 85 + oy), "ENEM", 40, WHITE)
    rr(d, (440, 70 + oy, 565, 130 + oy), 12, YEL, DARK, 4); txt(d, (502, 100 + oy), "2º DIA", 28, DARK)
    for r_ in range(8):
        txt(d, (80 + shk, 160 + oy + r_ * 50), str(r_ + 1), 18, DARK, mono=True)
        for c_ in range(4):
            x, y = 130 + c_ * 70 + shk, 160 + oy + r_ * 50; fill = ((r_ * 7 + c_ * 3) % 4 == 0) and lt > .3 + r_ * .35
            circ(d, x + 20, y, 17, fill=DARK if fill else None, outline=DARK, w=3); txt(d, (x + 20, y), "ABCD"[c_], 14, WHITE if fill else DARK)
    # relógio
    circ(d, 502, 230 + oy, 52, fill=WHITE, outline=DARK, w=5); a_ = math.radians(-90 + gt * 40); line(d, [(502, 230 + oy), (502 + 36 * math.cos(a_), 230 + oy + 36 * math.sin(a_))], RED, 5); line(d, [(502, 230 + oy), (502, 200 + oy)], DARK, 5)
    # setas de ataque
    if lt > 2.2:
        for i in range(3):
            t_ = ((lt - 2.2) * .9 + i / 3) % 1; x = 600 - 230 * t_ - (i * 5); y = 330 + oy + i * 70 - 30 * t_
            line(d, [(x, y), (x + 70, y - 12)], RED, 7); poly(d, [(x - 4, y + 1), (x + 20, y - 14), (x + 18, y + 14)], RED)
        txt(d, (490, 520 + oy), "TENTATIVAS", 24, RED if int(gt * 4) % 2 == 0 else DARK)

def sc_porto(im, d, lt, gt, fx):
    k = appear(lt)
    for i in range(6): line(d, [(x_, 470 + 14 * math.sin(gt * 2 + x_ / 40 + i) + i * 18) for x_ in range(0, 1)] if False else [(0, 0), (0, 0)], BLUE2, 1)
    # água
    for i in range(5):
        pts = [(x_, 470 + i * 24 + 8 * math.sin(gt * 2.2 + x_ / 50 + i)) for x_ in range(0, 601, 20)]
        line(d, pts, (BLUE2, BLUE, BLUE2, BLUE, BLUE2)[i], 6)
    sx = 40 + math.sin(gt * .6) * 14
    poly(d, [(sx, 400), (sx + 520, 400), (sx + 470, 470), (sx + 40, 470)], DARK, WHITE, 4); rr(d, (sx + 400, 330, sx + 500, 400), 6, WHITE, BLUE2, 3)
    cols = [BLUE, YEL, RED, WHITE, BLUE2]
    for r_ in range(3):
        for c_ in range(6):
            if (r_, c_) == (0, 2) and ep(lt, 1.0, 2.6) > 0: continue
            rr(d, (sx + 20 + c_ * 62, 340 - r_ * 36, sx + 78 + c_ * 62, 374 - r_ * 36), 3, cols[(r_ * 2 + c_) % 5], DARK, 2)
    # guindaste
    line(d, [(520, 470), (520, 90)], YEL, 12); line(d, [(120, 90), (580, 90)], YEL, 14); line(d, [(520, 90), (440, 20)], YEL, 6)
    cl_ = eo(ep(lt, 1.0, 2.6)); cxc = sx + 20 + 2 * 62 + 29 + (480 - (sx + 20 + 2 * 62 + 29)) * 0
    px_ = cxc + (240 - cxc) * eo(ep(lt, 2.6, 4.0)) if lt > 2.6 else cxc; py_ = 340 - 36 * 2 - 260 * cl_ * (1 if lt < 2.6 else 1) + 60 * (0)
    line(d, [(px_, 90), (px_, py_ - 10)], WHITE, 3); rr(d, (px_ - 29, py_ - 10, px_ + 29, py_ + 24), 3, BLUE, DARK, 2)
    for i in range(3): txt(d, (300, 570), "• " * (1 + int(lt * 2) % 3), 26, YEL, mono=True)

def sc_cinco(im, d, lt, gt, fx):
    rows = [("5", "ALVOS", cs_(fx, 0, .1)), ("5", "SETORES", cs_(fx, 1, 1.1)), ("30", "DIAS", cs_(fx, 2, 2.2))]
    for i, (num, lab, t0) in enumerate(rows):
        b = bk((lt - t0) / .35)
        if b <= 0: continue
        y = 40 + i * 180; sh = math.sin(lt * 50) * 6 * max(0, 1 - (lt - t0) * 4)
        rr(d, (30 + sh, y, 570 + sh, y + 160), 22, DARK, WHITE, 5)
        txt(d, (170 + sh, y + 82), num, int(150 * (.5 + .5 * b)) + 1, YEL); txt(d, (400 + sh, y + 82), lab, 54, WHITE)
        if lt - t0 < .25: fx["flash"] = (WHITE, int(70 * (1 - (lt - t0) / .25)))

def sc_investig(im, d, lt, gt, fx):
    pts = [(300 + 190 * math.cos(math.radians(-90 + 72 * i)), 290 + 190 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    for i in range(5):
        for j in range(i + 1, 5):
            a_, b_ = pts[i], pts[j]; n_ = 14
            for s_ in range(n_):
                if (s_ + int(gt * 6)) % 2: continue
                p1 = (a_[0] + (b_[0] - a_[0]) * s_ / n_, a_[1] + (b_[1] - a_[1]) * s_ / n_); p2 = (a_[0] + (b_[0] - a_[0]) * (s_ + 1) / n_, a_[1] + (b_[1] - a_[1]) * (s_ + 1) / n_)
                line(d, [p1, p2], BLUE2 + (170,), 3)
    labs = ["TESOURO", "CAIXA", "PETROBRAS", "INEP", "PORTO"]
    for i, p in enumerate(pts):
        circ(d, p[0], p[1], 30, fill=RED, outline=WHITE, w=4); txt(d, (p[0], p[1] + 52), labs[i], 16, WHITE, mono=True)
    txt(d, (300, 290), "?", int(190 + 14 * math.sin(gt * 3)), YEL)
    a_ = gt * 1.1; mx, my = 300 + 190 * math.cos(a_), 290 + 190 * math.sin(a_) * .9
    circ(d, mx, my, 56, outline=WHITE, w=9); line(d, [(mx + 40, my + 40), (mx + 90, my + 90)], WHITE, 14)
    k_ = appear(lt, cs_(fx, 4, fx["dur"] * .8), .3)
    if k_ > 0: stamp(im, "A INVESTIGAR", 52, 300, 545, k_, rot=-6, col=RED, w=420, h=90)

def sc_trio(im, d, lt, gt, fx):
    t = [cs_(fx, 0, .1), cs_(fx, 1, 1.4), cs_(fx, 2, 2.8)]
    for i in range(3):
        b = bk((lt - t[i]) / .4)
        if b <= 0: continue
        y = 30 + i * 190; off = (1 - b) * 600 * (-1 if i % 2 else 1)
        rr(d, (30 + off, y, 570 + off, y + 170), 22, WHITE, DARK, 5)
        if i == 0:
            rr(d, (60 + off, y + 30, 330 + off, y + 80), 10, LB, DARK, 3); txt(d, (195 + off, y + 55), "123456", 30, DARK, mono=True)
            for j in range(4): rr(d, (60 + off + j * 70, y + 100, 120 + off + j * 70, y + 118), 6, RED if j == 0 else LB)
            txt(d, (450 + off, y + 55), "SENHA", 28, RED); txt(d, (450 + off, y + 95), "FRACA", 28, RED)
        elif i == 1:
            rr(d, (60 + off, y + 40, 360 + off, y + 80), 20, LB, DARK, 3); rr(d, (64 + off, y + 44, 64 + off + 110, y + 76), 16, YEL)
            txt(d, (210 + off, y + 120), "ATUALIZAÇÃO PENDENTE", 18, DARK, mono=True)
            poly(d, [(470 + off, y + 30), (520 + off, y + 120), (420 + off, y + 120)], RED, DARK, 4); txt(d, (470 + off, y + 98), "!", 44, WHITE)
        else:
            circ(d, 120 + off, y + 70, 36, fill=SKIN, outline=DARK, w=4); poly(d, [(70 + off, y + 160), (80 + off, y + 118), (160 + off, y + 118), (170 + off, y + 160)], BLUE, DARK, 3)
            rr(d, (200 + off, y + 50, 260 + off, y + 130), 8, DARK); rr(d, (206 + off, y + 58, 254 + off, y + 118), 4, (60, 100, 220))
            sw = math.sin(gt * 3) * 6; circ(d, 120 + off + sw, y + 62, 6, fill=DARK)
            bb = bk((lt - t[2] - .5) / .3)
            if bb > 0: rr(d, (300 + off, y + 40, 540 + off, y + 100), 18, YEL, DARK, 3); txt(d, (420 + off, y + 70), "DISTRAÍDO...", int(24 * bb) + 1, DARK)


SCENE_FN = dict(alvo=sc_alvo, app=sc_app, app2=sc_app2, cadeado=sc_cadeado, entrev=sc_entrev, entrev2=sc_entrev2, malic=sc_malic,
                codigo=sc_codigo, arquivos=sc_arquivos, relogio=sc_relogio, calend=sc_calend, escudo=sc_escudo, celular=sc_celular,
                download=sc_download, lupa=sc_lupa, cta=sc_cta, calmar=sc_calmar, login=sc_login, ataque=sc_ataque, engenh=sc_engenh,
                cpu=sc_cpu, compacta=sc_compacta, servidor=sc_servidor, porta=sc_porta, ampulh=sc_ampulh, commits=sc_commits,
                confianca=sc_confianca, esgotado=sc_esgotado, pressao=sc_pressao, chave=sc_chave, testes=sc_testes, mapa=sc_mapa,
                relogio2=sc_relogio2, misterio=sc_misterio, pastas=sc_pastas,
                contador5=sc_contador5, calnov=sc_calnov, mapabr=sc_mapabr, mira=sc_mira, videos=sc_videos, padrao=sc_padrao, tesouro=sc_tesouro,
                pix=sc_pix, caixa=sc_caixa, petrobras=sc_petrobras, enem=sc_enem, porto=sc_porto, cinco=sc_cinco, investig=sc_investig, trio=sc_trio)

# ---------------------------------------------------------------- texto cinético (pop por palavra)
FT = bf(52)
_wc = {}
def word_img(w, col, shadow=True):
    key = (w, col, shadow)
    if key not in _wc:
        wl = int(FT.getlength(w)) + 16; im = Image.new("RGBA", (wl, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if shadow: d.text((10, 54), w, font=FT, fill=(0, 0, 0, 160), anchor="lm")
        d.text((8, 50), w, font=FT, fill=col + (255,), anchor="lm")
        _wc[key] = im
    return _wc[key]

def layout(words):
    lines, idx = [[]], 0
    for w, c in words:
        if w == "|": lines.append([]); continue
        lines[-1].append((idx, w.upper(), c, FT.getlength(w.upper()))); idx += 1
    return lines

def draw_text(frame, sc, gt, style="blue"):
    chs = sc["chunks"]; ch = [c for c in chs if c["start"] <= gt + 1e-6][-1] if gt >= chs[0]["start"] else chs[0]
    lt = gt - ch["start"]
    words = [w for w in ch["words"] if w[0] != "|"]; n = max(1, len(words)); span = min(ch["dur"] * .5, 1.0)
    lines = layout(ch["words"]); sp = FT.getlength(" ")
    widths = [sum(x[3] for x in ln) + sp * max(0, len(ln) - 1) for ln in lines]
    fs = min(1.0, 650 / max(widths)); lh = 76 * fs; y0 = 125
    for li, ln in enumerate(lines):
        tw = widths[li] * fs; x = (W - tw) / 2
        for (i, w, c, wl) in ln:
            k = (lt - (.04 + span * i / n)) / .16
            if k > 0:
                light = style in ("light", "yellow")
                if light: c = {WHITE: DARK, YEL: BLUE}.get(c, c)
                im = word_img(w, c, not light); s_ = (.45 + .55 * bk(k) if k < 1 else 1.0) * fs
                if s_ != 1: im = im.resize((max(1, int(im.width * s_)), max(1, int(im.height * s_))), Image.BILINEAR)
                else: im = im.copy()
                im.putalpha(im.split()[3].point(lambda v: int(v * min(1, k * 1.8))))
                frame.alpha_composite(im, (int(x + wl * fs / 2 + 8 * fs - im.width / 2), int(y0 + li * lh + 36 * fs - im.height / 2 + (1 - cl(k)) * -18)))
            x += (wl + sp) * fs

# ---------------------------------------------------------------- HUD e pós-processamento
HF = mf(17)
def hud(frame, sc, gt, style="blue"):
    d = ImageDraw.Draw(frame); lg = style in ("light", "yellow")
    d.text((24, 26), "// OPERAÇÃO SIGILO", font=HF, fill=(DARK if lg else BLUE2) + (255,))
    d.text((W - 24, 26), "● AO VIVO" if int(gt * 2) % 2 == 0 else "○ AO VIVO", font=HF, fill=RED + (255,), anchor="ra")
    for i, c in enumerate((BLUE, YEL, RED, WHITE)): d.rectangle((24 + i * 14, 56, 34 + i * 14, 62), fill=c + (255,), outline=DARK if lg else None)

def camera(img, sc, lt, gt, slt):
    """empurrão lento + tremor nos impactos."""
    zoom = 1 + .035 * lt / sc["dur"]; dx = dy = 0.0
    for ti in IMPACTS.get(sc["kind"], []):
        if slt > ti:
            a = 16 * math.exp(-(slt - ti) * 7 / sc["speed"])
            dx += math.sin((slt - ti) * 95) * a; dy += math.cos((slt - ti) * 83) * a
    if zoom == 1 and dx == 0 and dy == 0: return img
    cx, cy = W / 2, H / 2
    return img.transform((W, H), Image.AFFINE, (1 / zoom, 0, cx - cx / zoom - dx / zoom, 0, 1 / zoom, cy - cy / zoom - dy / zoom), resample=Image.BILINEAR)

def glitch(rgb, lt, gt):
    """divisão de canais RGB + fatias deslocadas nos primeiros 0.3s da cena."""
    k = 1 - lt / .3
    a = np.asarray(rgb).copy(); dx = int(18 * k)
    a[:, :, 0] = np.roll(a[:, :, 0], dx, axis=1); a[:, :, 2] = np.roll(a[:, :, 2], -dx, axis=1)
    rnd = random.Random(int(gt * 30))
    for _ in range(5):
        y = rnd.randrange(0, H - 60); h = rnd.randint(14, 60); a[y:y + h] = np.roll(a[y:y + h], rnd.randint(-70, 70), axis=1)
    return Image.fromarray(a)


# ---------------------------------------------------------------- estilos de fundo (variação visual entre cenas)
def _grad(c0, c1):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(c0[i] * (1 - k) + c1[i] * k) for i in range(3)))
    return im
def _make_styles():
    out = {}
    red = _grad((22, 3, 9), (70, 8, 24)); g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).ellipse((-120, 380, W + 120, 1120), fill=255); g = g.filter(ImageFilter.GaussianBlur(120))
    out["red"] = Image.composite(Image.new("RGB", (W, H), (150, 20, 40)), red, g.point(lambda v: int(v * .5))).convert("RGBA")
    lt_ = _grad((244, 249, 255), (206, 222, 252)).convert("RGBA"); d = ImageDraw.Draw(lt_)
    for x in range(14, W, 28):
        for y in range(14, H, 28): d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=BLUE + (40,))
    out["light"] = lt_
    ye = Image.new("RGBA", (W, H), YEL + (255,)); d = ImageDraw.Draw(ye)
    for cx, cy in ((0, 0), (W, H)):
        for r in range(40, 700, 36): d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(235, 180, 0, 255), width=10)
    out["yellow"] = ye
    return out
BGS = _make_styles()
def stripes(t, col, alpha):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l); off = (t * 40) % 80
    for x in range(-H, W, 80): d.polygon([(x + off, 0), (x + off + 28, 0), (x + off + 28 + H, H), (x + off + H, H)], fill=col + (alpha,))
    return l
STYLE = {}
if "ataque" in CENAS:
    STYLE = dict(contador5="red", calnov="light", mapabr="blue", mira="red", videos="blue", padrao="yellow", tesouro="blue", pix="light", caixa="light",
                 petrobras="red", enem="light", porto="blue", cinco="yellow", investig="blue", porta="blue", trio="light", pastas="blue", cta="blue")

def render_frame(f):
    gt = f / FPS
    si = 0
    while si < len(timeline) - 1 and gt >= timeline[si + 1]["start"]: si += 1
    sc = timeline[si]; lt = gt - sc["start"]; slt = lt * sc["speed"]
    style = STYLE.get(sc["kind"], "blue")
    if style == "blue": frame = BG.copy(); frame.alpha_composite(grid_layer(gt)); frame.alpha_composite(particles(gt))
    else:
        frame = BGS[style].copy()
        if style == "red": frame.alpha_composite(stripes(gt, RED, 26)); frame.alpha_composite(particles(gt))
        elif style == "yellow": frame.alpha_composite(stripes(gt, (235, 180, 0), 70))
    fx = dict(bolts=[], flash=None, dur=sc["dur"], cs=[c["start"] - sc["start"] for c in sc["chunks"]])
    stage = alpha_layer(); sd = ImageDraw.Draw(stage)
    SCENE_FN[sc["kind"]](stage, sd, slt, gt, fx)
    ent = .9 + .1 * bk(lt / .35)
    size = int(SSZ * ent); stg = stage.resize((size, size), Image.BILINEAR)
    frame.alpha_composite(stg, (SX + (SSZ - size) // 2, SY + (SSZ - size) // 2))
    draw_bolts(frame, fx["bolts"])
    draw_text(frame, sc, gt, style)
    frame = camera(frame, sc, lt, gt, slt)
    if style in ("blue", "red"): frame.alpha_composite(VIGL); frame.alpha_composite(SCAN)
    if fx["flash"] and fx["flash"][1] > 0:
        c, a = fx["flash"]; frame.alpha_composite(Image.new("RGBA", (W, H), c + (min(255, int(a)),)))
    hud(frame, sc, gt, style)
    out = frame.convert("RGB")
    if lt < .2: out = glitch(out, lt * 1.5, gt)
    if lt < .1: out = Image.blend(out, Image.new("RGB", (W, H), WHITE), .35 * (1 - lt / .1))
    if gt > TOTAL - .4: out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), (gt - (TOTAL - .4)) / .4)
    return out.tobytes()

def main():
    nframes = int(TOTAL * FPS)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           os.path.join(OUT, PREFIX + "-SEM-AUDIO.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(render_frame, range(nframes), chunksize=6): p.stdin.write(b)
    p.stdin.close(); p.wait()
    aud = os.environ.get("AUDIO")
    if aud:  # junta o áudio (voz da Elena) ao vídeo
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(OUT, PREFIX + "-SEM-AUDIO.mp4"), "-i", aud,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        os.path.join(OUT, PREFIX + "-COM-AUDIO.mp4")], check=True)
    print("ok", round(TOTAL, 1), "s")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        td = os.environ.get("TESTDIR", OUT)
        for t in sys.argv[2:]:
            Image.frombytes("RGB", (W, H), render_frame(int(float(t) * FPS))).save(os.path.join(td, f"t_{t}.png"))
    else:
        main()
