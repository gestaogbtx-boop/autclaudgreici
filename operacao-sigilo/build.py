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
SCENES = [  # (cena, texto [| = quebra de linha], tag, duração s, velocidade da animação)
 ("alvo",    "Esse é o novo jeito | de um *hacker* invadir", "", 2.4, 1.9),
 ("app",     "Começa com um | _app_ feito na pressa", "", 1.9, 1.5),
 ("app2",    "Publicado em | *minutos* com IA", "", 1.9, 2.4),
 ("cadeado", "E *sem proteção*... | _qualquer um_ entra", "", 2.0, 1.3),
 ("entrev",  "Ou numa _entrevista_ | de emprego *falsa*", "", 1.8, 1.2),
]
WPS = 2.55
IMPACTS = dict(alvo=[3.3], cadeado=[1.1], entrev=[1.3], entrev2=[1.3], malic=[.5], codigo=[3.4, 6.6], arquivos=[.4],
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

timeline, t0 = [], 0.0
for kind, text, tag, dur, speed in SCENES:
    words = parse(text)
    timeline.append(dict(kind=kind, text=text, tag=tag, words=words, start=t0, dur=dur, speed=speed))
    t0 += dur
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
        txt(d, (300, 540), "CÓDIGO SUSPEITO", 32, RED if int(gt * 4) % 2 == 0 else WHITE)
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

SCENE_FN = dict(alvo=sc_alvo, app=sc_app, app2=sc_app2, cadeado=sc_cadeado, entrev=sc_entrev, entrev2=sc_entrev2, malic=sc_malic,
                codigo=sc_codigo, arquivos=sc_arquivos, relogio=sc_relogio, calend=sc_calend, escudo=sc_escudo, celular=sc_celular,
                download=sc_download, lupa=sc_lupa, cta=sc_cta)

# ---------------------------------------------------------------- texto cinético (pop por palavra)
FT = bf(52)
_wc = {}
def word_img(w, col):
    key = (w, col)
    if key not in _wc:
        wl = int(FT.getlength(w)) + 16; im = Image.new("RGBA", (wl, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((10, 54), w, font=FT, fill=(0, 0, 0, 160), anchor="lm"); d.text((8, 50), w, font=FT, fill=col + (255,), anchor="lm")
        _wc[key] = im
    return _wc[key]

def layout(words):
    lines, cur, idx = [[]], 0, 0
    for w, c in words:
        if w == "|": lines.append([]); continue
        lines[-1].append((idx, w.upper(), c, FT.getlength(w.upper()))); idx += 1
    return lines

def draw_text(frame, sc, lt):
    words = [w for w in sc["words"] if w[0] != "|"]; n = len(words); span = sc["dur"] * .55
    lines = layout(sc["words"]); y0 = 120; lh = 76; sp = FT.getlength(" ")
    for li, ln in enumerate(lines):
        tw = sum(x[3] for x in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for (i, w, c, wl) in ln:
            k = (lt - (.08 + span * i / n)) / .16
            if k > 0:
                im = word_img(w, c); s = .45 + .55 * bk(k) if k < 1 else 1.0
                if k < 1 and s != 1:
                    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
                im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * min(1, k * 1.8))))
                frame.alpha_composite(im, (int(x + wl / 2 + 8 - im.width / 2), int(y0 + li * lh + 36 - im.height / 2 + (1 - cl(k)) * -18)))
            x += wl + sp

# ---------------------------------------------------------------- HUD e pós-processamento
HF = mf(17)
def hud(frame, sc, gt):
    d = ImageDraw.Draw(frame)
    d.text((24, 26), "// OPERAÇÃO SIGILO", font=HF, fill=BLUE2 + (255,))
    d.text((W - 24, 26), "● AO VIVO" if int(gt * 2) % 2 == 0 else "○ AO VIVO", font=HF, fill=RED + (255,), anchor="ra")
    for i, c in enumerate((BLUE, YEL, RED, WHITE)): d.rectangle((24 + i * 14, 56, 34 + i * 14, 62), fill=c + (255,))

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

def render_frame(f):
    gt = f / FPS
    si = 0
    while si < len(timeline) - 1 and gt >= timeline[si + 1]["start"]: si += 1
    sc = timeline[si]; lt = gt - sc["start"]; slt = lt * sc["speed"]
    frame = BG.copy(); frame.alpha_composite(grid_layer(gt)); frame.alpha_composite(particles(gt))
    fx = dict(bolts=[], flash=None)
    stage = alpha_layer(); sd = ImageDraw.Draw(stage)
    SCENE_FN[sc["kind"]](stage, sd, slt, gt, fx)
    ent = .9 + .1 * bk(lt / .35)
    size = int(SSZ * ent); stg = stage.resize((size, size), Image.BILINEAR)
    frame.alpha_composite(stg, (SX + (SSZ - size) // 2, SY + (SSZ - size) // 2))
    draw_bolts(frame, fx["bolts"])
    draw_text(frame, sc, lt)
    frame = camera(frame, sc, lt, gt, slt)
    frame.alpha_composite(VIGL); frame.alpha_composite(SCAN)
    if fx["flash"] and fx["flash"][1] > 0:
        c, a = fx["flash"]; frame.alpha_composite(Image.new("RGBA", (W, H), c + (min(255, int(a)),)))
    hud(frame, sc, gt)
    out = frame.convert("RGB")
    if lt < .2: out = glitch(out, lt * 1.5, gt)
    if lt < .1: out = Image.blend(out, Image.new("RGB", (W, H), WHITE), .35 * (1 - lt / .1))
    if gt > TOTAL - .4: out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), (gt - (TOTAL - .4)) / .4)
    return out.tobytes()

def main():
    nframes = int(TOTAL * FPS)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           os.path.join(OUT, "operacao-sigilo-SEM-AUDIO.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(render_frame, range(nframes), chunksize=6): p.stdin.write(b)
    p.stdin.close(); p.wait()
    L = ["# ROTEIRO DE ÁUDIO – OPERAÇÃO SIGILO (voz: Elena)", "",
         f"Duração alvo: {int(TOTAL // 60)}min{int(TOTAL % 60):02d}s  |  Tom firme, ritmo de notícia urgente", "",
         "Leia cada bloco dentro da janela de tempo indicada. Pausas (...) = respiro de ~0,4 s.", ""]
    for i, s in enumerate(timeline, 1):
        clean = s["text"].replace("*", "").replace("_", "").replace(" | ", " ")
        L += [f"## Cena {i}  [{s['start']:04.1f}s → {s['start'] + s['dur']:04.1f}s]", clean, ""]
    open(os.path.join(OUT, "roteiro-elena.md"), "w", encoding="utf-8").write("\n".join(L))
    json.dump([dict(cena=i + 1, inicio=round(s["start"], 2), fim=round(s["start"] + s["dur"], 2), texto=s["text"].replace("*", "").replace("_", "").replace(" | ", " ")) for i, s in enumerate(timeline)],
              open(os.path.join(OUT, "tempos.json"), "w"), ensure_ascii=False, indent=1)
    print("ok", round(TOTAL, 1), "s")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        td = os.environ.get("TESTDIR", OUT)
        for t in sys.argv[2:]:
            Image.frombytes("RGB", (W, H), render_frame(int(float(t) * FPS))).save(os.path.join(td, f"t_{t}.png"))
    else:
        main()
