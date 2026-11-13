#!/usr/bin/env python3
"""Operação Sigilo – gera o vídeo 9:16 (720x1280, 30fps) + roteiro com tempos.
Uso: python3 build.py   (precisa de Pillow, numpy e ffmpeg)"""
import math, random, subprocess, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 30
OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, NAVY2 = (4, 9, 28), (8, 20, 60)
BLUE, BLUE2 = (30, 90, 255), (90, 150, 255)
YEL, RED, WHITE = (255, 210, 31), (255, 52, 72), (255, 255, 255)
DARK = (10, 14, 34)
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
if not os.path.exists(FB): FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
font = lambda s: ImageFont.truetype(FB, s)
mono = lambda s: ImageFont.truetype(FM, s)

# ---------------------------------------------------------------- ROTEIRO
# *palavra* = destaque amarelo ; _palavra_ = destaque vermelho
SCENES = [
 ("alvo",    "Esse é o novo jeito de um *hacker* entrar na sua empresa... e você nem vai perceber.", "ALERTA"),
 ("app",     "Primeiro: o _app_ feito na pressa.", "01 / 03"),
 ("app",     "Muita gente cria app com inteligência artificial, publica no mesmo dia... e esquece de proteger o básico.", "01 / 03"),
 ("cadeado", "Resultado: *senha exposta*, banco de dados aberto, e _qualquer um_ entra.", "01 / 03"),
 ("entrev",  "Segundo golpe: a _entrevista de emprego_ perfeita.", "02 / 03"),
 ("entrev",  "O recrutador sorri, a vaga paga muito bem... e pede só uma coisa: que você *instale um programinha* pra teste.", "02 / 03"),
 ("malic",   "Esse programa é o _vírus_.", "02 / 03"),
 ("codigo",  "Terceiro: o *pacote malicioso*. Você copia um código da internet, cola no projeto... e ele leva junto uma _porta dos fundos_.", "03 / 03"),
 ("arquivos","Em minutos, o hacker enxerga seus *arquivos*, suas *senhas* e seus *clientes*.", "03 / 03"),
 ("relogio", "Tudo isso pode acontecer em _poucos minutos_.", "TEMPO"),
 ("calend",  "Já a empresa... leva *semanas* pra perceber.", "TEMPO"),
 ("escudo",  "E como se proteger? *Três regras* simples.", "DEFESA"),
 ("celular", "Um: ative a _verificação em duas etapas_ em tudo.", "REGRA 1"),
 ("download","Dois: *nunca instale* nada que um desconhecido te mandar.", "REGRA 2"),
 ("lupa",    "Três: *revise* todo código antes de colar.", "REGRA 3"),
 ("cta",     "Quer ficar um passo à frente? Segue a *Operação Sigilo*, que a gente te conta o que _ninguém_ conta.", "SEGUE"),
]
WPS = 2.55  # palavras por segundo da narração (ritmo Elena)

def parse(t):
    out = []
    for tok in t.split():
        col = WHITE
        if tok.startswith("*") : col = YEL
        elif tok.startswith("_"): col = RED
        # destaque pode abranger várias palavras
        out.append([tok, col])
    # propaga cor entre marcadores de abertura/fechamento
    res, cur = [], WHITE
    for tok, _ in out:
        o = tok[0] in "*_"
        if o: cur = YEL if tok[0] == "*" else RED
        clean = tok.replace("*", "").replace("_", "")
        res.append((clean, cur))
        if tok[-1] in "*_" or (tok.rstrip(".,:!?")[-1:] in "*_"): cur = WHITE
    return res

timeline, t0 = [], 0.0
for kind, text, tag in SCENES:
    words = parse(text)
    dur = max(2.4, len(words) / WPS + 0.55)
    timeline.append(dict(kind=kind, text=text, tag=tag, words=words, start=t0, dur=dur))
    t0 += dur
TOTAL = t0

# ---------------------------------------------------------------- FUNDO
def make_bg():
    bg = Image.new("RGB", (W, H), NAVY)
    px = ImageDraw.Draw(bg)
    for y in range(H):  # degradê vertical
        k = y / H
        c = tuple(int(NAVY[i] * (1 - k) + NAVY2[i] * k) for i in range(3))
        px.line([(0, y), (W, y)], fill=c)
    return bg
BG = make_bg()
GLOW = Image.new("RGB", (W, H), (0, 0, 0))
g = ImageDraw.Draw(GLOW); g.ellipse((-100, 380, W + 100, 1100), fill=(18, 50, 160))
GLOW = GLOW.filter(ImageFilter.GaussianBlur(120))
BG = Image.blend(BG, Image.composite(GLOW, BG, GLOW.convert("L")), 0.55)

def grid_layer(t):
    """chão em perspectiva que 'corre' + vinheta."""
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    hz = 1010
    for i in range(-14, 15):
        d.line([(W / 2 + i * 22, hz), (W / 2 + i * 190, H)], fill=BLUE + (70,), width=1)
    ph = (t * 0.6) % 1
    for j in range(9):
        k = (j + ph) / 9; y = hz + (H - hz) * (k ** 2)
        d.line([(0, y), (W, y)], fill=BLUE + (int(30 + 70 * k),), width=1)
    d.line([(0, hz), (W, hz)], fill=BLUE2 + (120,), width=2)
    return l

random.seed(7)
PARTS = [(random.random() * W, random.random() * H, random.random() * .5 + .2, random.choice("01{}<>/#$"), random.choice([BLUE2, YEL, WHITE])) for _ in range(34)]
def particles(t):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l); f = mono(16)
    for x, y, sp, ch, col in PARTS:
        yy = (y - t * 60 * sp) % H
        d.text((x, yy), ch, font=f, fill=col + (70,))
    return l

# ---------------------------------------------------------------- ILUSTRAÇÕES (coordenadas 600x600, render 2x)
S = 2
def canvas():
    im = Image.new("RGBA", (600 * S, 600 * S), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def P(*a): return [v * S for v in a]
def rr(d, box, r, fill, outline=None, w=0): d.rounded_rectangle(P(*box), radius=r * S, fill=fill, outline=outline, width=w * S)
def poly(d, pts, fill, outline=None, w=0): d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=outline, width=w * S) if outline else d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
def ell(d, box, fill=None, outline=None, w=0): d.ellipse(P(*box), fill=fill, outline=outline, width=w * S)
def line(d, pts, fill, w): d.line([(x * S, y * S) for x, y in pts], fill=fill, width=w * S, joint="curve")
def txt(d, xy, s, f, fill, anchor="mm"): d.text((xy[0] * S, xy[1] * S), s, font=ImageFont.truetype(f.path, int(f.size * S)), fill=fill, anchor=anchor)
def bigfont(s): return ImageFont.truetype(FB, s)
def monof(s): return ImageFont.truetype(FM, s)

def hood(d, cx, cy, sc=1.0, eyes=WHITE):
    """hacker de capuz."""
    def q(x, y): return (cx + x * sc, cy + y * sc)
    poly(d, [q(-120, 140), q(-100, 20), q(-60, -60), q(0, -100), q(60, -60), q(100, 20), q(120, 140)], (6, 10, 28), BLUE2, 3)
    ell(d, (q(-58, -50)[0], q(-58, -50)[1], q(58, 70)[0], q(58, 70)[1]), fill=(0, 2, 10), outline=(30, 60, 160), w=2)
    ell(d, (q(-34, -2)[0], q(-34, -2)[1], q(-12, 14)[0], q(-12, 14)[1]), fill=eyes)
    ell(d, (q(12, -2)[0], q(12, -2)[1], q(34, 14)[0], q(34, 14)[1]), fill=eyes)

def laptop(d, x, y, w=300, h=190, screen=BLUE):
    rr(d, (x, y, x + w, y + h), 10, (14, 22, 60), BLUE2, 3)
    rr(d, (x + 12, y + 12, x + w - 12, y + h - 12), 4, screen)
    poly(d, [(x - 30, y + h), (x + w + 30, y + h), (x + w + 14, y + h + 20), (x - 14, y + h + 20)], (24, 36, 90), BLUE2, 2)

def ill_alvo():
    im, d = canvas()
    for r, a in ((260, 40), (190, 70), (120, 110)): ell(d, (300 - r, 300 - r, 300 + r, 300 + r), outline=RED + (a + 60,), w=3)
    for i in range(-250, 251, 50):
        line(d, [(300 + i, 40), (300 + i, 560)], BLUE + (40,), 1); line(d, [(40, 300 + i), (560, 300 + i)], BLUE + (40,), 1)
    line(d, [(300, 20), (300, 580)], RED + (160,), 2); line(d, [(20, 300), (580, 300)], RED + (160,), 2)
    ell(d, (270, 270, 330, 330), fill=RED); ell(d, (285, 285, 315, 315), fill=WHITE)
    txt(d, (300, 90), "ALVO TRAVADO", bigfont(30), YEL); txt(d, (300, 520), "LAT 23.55  LON 46.63", monof(20), BLUE2)
    return im

def ill_app():
    im, d = canvas()
    rr(d, (50, 100, 550, 500), 18, (12, 20, 56), BLUE2, 4); rr(d, (50, 100, 550, 150), 18, BLUE)
    for i, c in enumerate((RED, YEL, WHITE)): ell(d, (72 + i * 28, 118, 90 + i * 28, 136), fill=c)
    rr(d, (170, 114, 520, 138), 10, (8, 14, 44)); txt(d, (345, 126), "meu-app.vercel.app", monof(16), BLUE2)
    txt(d, (300, 230), "MEU APP", bigfont(56), WHITE); txt(d, (300, 290), "FEITO COM IA • NO AR", monof(18), YEL)
    rr(d, (200, 340, 400, 400), 30, YEL); txt(d, (300, 370), "COMEÇAR", bigfont(28), DARK)
    for i in range(3): rr(d, (90 + i * 150, 430, 220 + i * 150, 470), 8, (20, 36, 96))
    return im

def ill_cadeado():
    im, d = canvas()
    line(d, [(210, 270), (210, 170), (240, 110), (300, 90), (360, 110), (385, 170)], WHITE, 26)  # haste aberta
    rr(d, (150, 260, 450, 480), 26, BLUE, WHITE, 6)
    ell(d, (270, 320, 330, 380), fill=DARK); rr(d, (290, 360, 310, 430), 6, DARK)
    poly(d, [(470, 150), (570, 330), (370, 330)], RED, WHITE, 5); txt(d, (470, 285), "!", bigfont(100), WHITE)
    txt(d, (300, 535), "DADOS EXPOSTOS", bigfont(34), YEL)
    return im

def ill_entrev():
    im, d = canvas()
    rr(d, (30, 90, 570, 510), 16, (12, 20, 56), BLUE2, 4)
    rr(d, (50, 110, 390, 440), 8, (18, 40, 120))
    ell(d, (160, 190, 280, 310), fill=WHITE); ell(d, (190, 235, 205, 250), fill=DARK); ell(d, (235, 235, 250, 250), fill=DARK)
    d.arc(P(185, 250, 255, 295), 20, 160, fill=DARK, width=5 * S)
    poly(d, [(100, 440), (140, 330), (300, 330), (340, 440)], DARK, WHITE, 3); poly(d, [(205, 330), (235, 330), (225, 420), (215, 420)], RED)
    rr(d, (410, 110, 550, 220), 8, (24, 50, 140)); rr(d, (410, 235, 550, 345), 8, (18, 30, 90)); hood(d, 480, 300, .35)
    rr(d, (410, 360, 550, 425), 10, YEL); txt(d, (480, 392), "CONTRATADO!", bigfont(20), DARK)
    for i, c in enumerate((BLUE2, BLUE2, RED)): ell(d, (230 + i * 50, 462, 262 + i * 50, 494), fill=c)
    txt(d, (480, 165), "R$ 28 MIL", bigfont(24), WHITE)
    return im

def ill_malic():
    im, d = canvas()
    poly(d, [(300, 70), (500, 180), (500, 400), (300, 510), (100, 400), (100, 180)], (14, 24, 70), BLUE2, 6)
    poly(d, [(300, 70), (500, 180), (300, 290), (100, 180)], (24, 44, 130), BLUE2, 3)
    line(d, [(300, 290), (300, 510)], BLUE2, 3)
    st = Image.new("RGBA", (600 * S, 600 * S), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    rr(sd, (90, 255, 510, 365), 12, RED + (235,), WHITE, 7); txt(sd, (300, 310), "MALICIOSO", bigfont(66), WHITE)
    st = st.rotate(-12, resample=Image.BICUBIC, center=(300 * S, 310 * S)); im.alpha_composite(st)
    ell(d, (430, 50, 500, 120), fill=RED, outline=WHITE, w=4); txt(d, (465, 85), "X", bigfont(44), WHITE)
    return im

def ill_codigo():
    im, d = canvas()
    laptop(d, 90, 140, 420, 270, (6, 12, 40))
    cols = [BLUE2, YEL, WHITE, RED, BLUE2]
    random.seed(3)
    for i in range(9):
        x = 118 + random.choice((0, 0, 26, 52)); a = 0
        while a < random.randint(120, 300):
            w = random.randint(30, 80); line(d, [(x + a, 175 + i * 22), (x + a + w, 175 + i * 22)], cols[random.randrange(5)], 8); a += w + 10
    line(d, [(118, 336), (330, 336)], RED, 10)  # linha maliciosa
    rr(d, (150, 450, 270, 520), 12, WHITE); txt(d, (210, 485), "CTRL", bigfont(30), DARK); txt(d, (300, 485), "+", bigfont(40), WHITE)
    rr(d, (330, 450, 410, 520), 12, YEL); txt(d, (370, 485), "V", bigfont(40), DARK)
    poly(d, [(480, 80), (560, 210), (400, 210)], RED, WHITE, 4); txt(d, (480, 175), "!", bigfont(70), WHITE)
    return im

def folder(d, x, y, c):
    rr(d, (x, y - 14, x + 50, y + 8), 5, c); rr(d, (x, y, x + 100, y + 70), 8, c)
def ill_arquivos():
    im, d = canvas()
    hood(d, 300, 360, 1.15)
    laptop(d, 220, 450, 160, 90, (14, 40, 130))
    for i, (x, y, c) in enumerate(((40, 100, YEL), (250, 40, BLUE2), (450, 110, WHITE), (60, 250, RED), (460, 260, YEL))):
        folder(d, x, y, c); line(d, [(x + 50, y + 70), (300, 300)], c + (90,), 2)
    txt(d, (300, 560), "ARQUIVOS • SENHAS • CLIENTES", bigfont(26), YEL)
    return im

def ill_relogio():
    im, d = canvas()
    ell(d, (80, 90, 520, 530), fill=WHITE, outline=BLUE, w=22)
    d.pieslice(P(110, 120, 490, 500), -90, -30, fill=RED)
    for i in range(60):
        a = math.radians(i * 6 - 90); r1, r2 = 185, 170 if i % 5 else 155
        line(d, [(300 + r1 * math.cos(a), 310 + r1 * math.sin(a)), (300 + r2 * math.cos(a), 310 + r2 * math.sin(a))], DARK, 3 if i % 5 else 6)
    line(d, [(300, 310), (300 + 130 * math.cos(math.radians(-30)), 310 + 130 * math.sin(math.radians(-30)))], DARK, 8)
    ell(d, (285, 295, 315, 325), fill=YEL, outline=DARK, w=4); rr(d, (270, 48, 330, 86), 8, BLUE2); rr(d, (285, 30, 315, 52), 4, BLUE2)
    rr(d, (240, 380, 360, 420), 8, DARK); txt(d, (300, 400), "00:07:12", monof(26), YEL)
    return im

def ill_calend():
    im, d = canvas()
    rr(d, (110, 70, 490, 510), 24, WHITE); rr(d, (110, 70, 490, 170), 24, RED); d.rectangle(P(110, 130, 490, 170), fill=RED)
    txt(d, (300, 120), "DEPOIS", bigfont(48), WHITE)
    txt(d, (300, 305), "21", bigfont(190), DARK); txt(d, (300, 440), "DIAS", bigfont(48), BLUE)
    for x in (170, 430): rr(d, (x - 14, 48, x + 14, 100), 8, BLUE2)
    return im

def ill_escudo():
    im, d = canvas()
    sh = [(300, 40), (500, 110), (490, 330), (300, 550), (110, 330), (100, 110)]
    poly(d, sh, BLUE, YEL, 10)
    poly(d, [(300, 90), (455, 145), (448, 320), (300, 495), (152, 320), (145, 145)], (18, 60, 200), WHITE, 4)
    line(d, [(210, 300), (275, 365), (400, 220)], WHITE, 36)
    for (x, y) in ((70, 120), (530, 120)): ell(d, (x - 30, y - 30, x + 30, y + 30), fill=YEL); rr(d, (x - 10, y - 2, x + 10, y + 14), 3, DARK)
    return im

def ill_celular():
    im, d = canvas()
    rr(d, (170, 40, 430, 560), 40, DARK, BLUE2, 8); rr(d, (190, 85, 410, 520), 22, (14, 30, 90))
    txt(d, (300, 140), "CÓDIGO", bigfont(30), BLUE2)
    for i, c in enumerate("482916"): rr(d, (196 + i * 36, 180, 226 + i * 36, 240), 6, WHITE); txt(d, (211 + i * 36, 210), c, bigfont(34), DARK)
    rr(d, (210, 300, 390, 360), 28, YEL); txt(d, (300, 330), "CONFIRMAR", bigfont(26), DARK)
    ell(d, (260, 400, 340, 480), fill=BLUE); line(d, [(277, 440), (293, 456), (325, 420)], WHITE, 10)
    return im

def ill_download():
    im, d = canvas()
    ell(d, (80, 80, 520, 520), fill=(14, 28, 90), outline=BLUE2, w=8)
    poly(d, [(255, 150), (345, 150), (345, 260), (410, 260), (300, 380), (190, 260), (255, 260)], WHITE)
    line(d, [(200, 420), (400, 420)], WHITE, 14)
    line(d, [(110, 110), (490, 490)], RED, 36); line(d, [(490, 110), (110, 490)], RED, 36)
    ell(d, (80, 80, 520, 520), outline=RED, w=14)
    return im

def ill_lupa():
    im, d = canvas()
    rr(d, (50, 100, 430, 440), 16, (10, 18, 54), BLUE2, 4)
    random.seed(5)
    for i in range(10):
        a = random.randint(100, 280); c = random.choice([BLUE2, WHITE, BLUE2])
        line(d, [(80, 135 + i * 30), (80 + a, 135 + i * 30)], c, 9)
    line(d, [(80, 285), (360, 285)], RED, 12)
    ell(d, (210, 170, 480, 440), fill=(255, 255, 255, 30), outline=YEL, w=18)
    line(d, [(450, 410), (550, 520)], YEL, 34)
    txt(d, (345, 305), "OK", bigfont(70), YEL)
    return im

def ill_cta():
    im, d = canvas()
    rr(d, (60, 70, 540, 420), 30, (12, 22, 66), BLUE2, 5)
    ell(d, (240, 100, 360, 220), fill=DARK, outline=YEL, w=6); hood(d, 300, 200, .3)
    txt(d, (300, 255), "OPERAÇÃO SIGILO", bigfont(36), WHITE); txt(d, (300, 292), "NOTÍCIAS • ALERTAS • SEGURANÇA", monof(15), BLUE2)
    rr(d, (170, 330, 430, 395), 32, YEL); txt(d, (300, 362), "SEGUIR", bigfont(36), DARK)
    for i, (lab, c) in enumerate((("ALERTAS", RED), ("DICAS", BLUE), ("DEFESA", YEL))):
        rr(d, (60 + i * 165, 450, 215 + i * 165, 540), 16, c); txt(d, (137 + i * 165, 495), lab, bigfont(24), DARK if c == YEL else WHITE)
    return im

ILL = dict(alvo=ill_alvo, app=ill_app, cadeado=ill_cadeado, entrev=ill_entrev, malic=ill_malic, codigo=ill_codigo,
           arquivos=ill_arquivos, relogio=ill_relogio, calend=ill_calend, escudo=ill_escudo, celular=ill_celular,
           download=ill_download, lupa=ill_lupa, cta=ill_cta)
CACHE = {}
def illus(kind):
    if kind not in CACHE:
        CACHE[kind] = ILL[kind]().resize((620, 620), Image.LANCZOS)
    return CACHE[kind]

# ---------------------------------------------------------------- TEXTO CINÉTICO
FT = font(58)
def layout(words, maxw=640):
    lines, cur, cw = [], [], 0
    sp = FT.getlength(" ")
    for i, (w, c) in enumerate(words):
        wl = FT.getlength(w.upper())
        if cur and cw + sp + wl > maxw: lines.append(cur); cur, cw = [], 0
        cur.append((i, w.upper(), c, wl)); cw += wl + (sp if len(cur) > 1 else 0)
    lines.append(cur)
    return lines

def ease_out(k): k = max(0, min(1, k)); return 1 - (1 - k) ** 3
def back(k): k = max(0, min(1, k)); c = 1.70158; return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2

def draw_text(frame, sc, lt):
    words = sc["words"]; n = len(words)
    reveal_span = sc["dur"] - 0.7
    lines = layout(words); nl = len(lines)
    lh = 72; y0 = 110 if nl <= 4 else 90
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    sp = FT.getlength(" ")
    for li, ln in enumerate(lines):
        tw = sum(x[3] for x in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for (i, w, c, wl) in ln:
            at = 0.15 + reveal_span * (i / n)
            k = (lt - at) / 0.18
            if k > 0:
                a = int(255 * ease_out(k)); off = (1 - back(k)) * -22
                y = y0 + li * lh + off
                d.text((x + 3, y + 4), w, font=FT, fill=(0, 0, 0, int(a * .6)))
                d.text((x, y), w, font=FT, fill=c + (a,))
            x += wl + sp
    frame.alpha_composite(layer)

# ---------------------------------------------------------------- HUD / QUADRO
HF = mono(17)
def hud(frame, sc, lt, gt):
    d = ImageDraw.Draw(frame)
    d.text((24, 26), "// OPERAÇÃO SIGILO", font=HF, fill=BLUE2 + (255,))
    d.text((W - 24, 26), "● AO VIVO" if int(gt * 2) % 2 == 0 else "○ AO VIVO", font=HF, fill=RED + (255,), anchor="ra")
    d.text((24, H - 40), f"// {sc['tag']}", font=HF, fill=YEL + (255,))
    d.text((W - 24, H - 40), f"{int(gt) // 60:02d}:{int(gt) % 60:02d}", font=HF, fill=WHITE + (200,), anchor="ra")
    # barra de progresso
    d.rectangle((0, H - 8, W, H - 4), fill=(20, 30, 80, 255)); d.rectangle((0, H - 8, W * gt / TOTAL, H - 4), fill=YEL + (255,))

def logo_badge(frame):
    d = ImageDraw.Draw(frame)
    for i, c in enumerate((BLUE, YEL, RED, WHITE)): d.rectangle((24 + i * 14, 56, 34 + i * 14, 62), fill=c + (255,))

def render_frame(gt, idx, sc):
    lt = gt - sc["start"]
    frame = BG.convert("RGBA")
    frame.alpha_composite(grid_layer(gt)); frame.alpha_composite(particles(gt))
    # ilustração: entra com "pop", flutua, e dá leve zoom ao longo da cena
    ill = illus(sc["kind"])
    k = back(lt / 0.45); zoom = (0.85 + 0.15 * k) * (1 + 0.04 * lt / sc["dur"])
    size = int(620 * zoom)
    im2 = ill.resize((size, size), Image.BICUBIC)
    bob = math.sin(gt * 2.2) * 8
    ex = max(0, 1 - lt / 0.25)
    frame.alpha_composite(im2, ((W - size) // 2, int(520 + (560 - size) / 2 + bob + ex * 30)))
    draw_text(frame, sc, lt)
    hud(frame, sc, lt, gt); logo_badge(frame)
    # flash de transição na troca de cena
    if lt < 0.12:
        ov = Image.new("RGBA", (W, H), WHITE + (int(110 * (1 - lt / 0.12)),)); frame.alpha_composite(ov)
    if gt > TOTAL - 0.4:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (gt - (TOTAL - 0.4)) / 0.4))); frame.alpha_composite(ov)
    return frame.convert("RGB")

def main():
    nframes = int(TOTAL * FPS)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           os.path.join(OUT, "operacao-sigilo-SEM-AUDIO.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    si = 0
    for f in range(nframes):
        gt = f / FPS
        while si < len(timeline) - 1 and gt >= timeline[si + 1]["start"]: si += 1
        p.stdin.write(render_frame(gt, f, timeline[si]).tobytes())
    p.stdin.close(); p.wait()
    # roteiro
    L = ["# ROTEIRO DE ÁUDIO – OPERAÇÃO SIGILO (voz: Elena)", "",
         f"Duração alvo: {int(TOTAL//60)}min{int(TOTAL%60):02d}s  |  Ritmo: ~{WPS} palavras/s, tom firme, ritmo de notícia urgente", "",
         "Leia cada bloco dentro da janela de tempo indicada. Pausas (...) = respiro de ~0,4 s.", ""]
    for i, s in enumerate(timeline, 1):
        clean = s["text"].replace("*", "").replace("_", "")
        L += [f"## Cena {i}  [{int(s['start']//60):02d}:{s['start']%60:04.1f} → {int((s['start']+s['dur'])//60):02d}:{(s['start']+s['dur'])%60:04.1f}]  ({s['tag']})", clean, ""]
    open(os.path.join(OUT, "roteiro-elena.md"), "w", encoding="utf-8").write("\n".join(L))
    json.dump([dict(cena=i + 1, inicio=round(s["start"], 2), fim=round(s["start"] + s["dur"], 2), texto=s["text"].replace("*", "").replace("_", "")) for i, s in enumerate(timeline)],
              open(os.path.join(OUT, "tempos.json"), "w"), ensure_ascii=False, indent=1)
    print("ok", round(TOTAL, 1), "s")

if __name__ == "__main__":
    main()
