#!/usr/bin/env python3
"""Trilha + efeitos sonoros sincronizados com as cenas, misturados sob a narração (com ducking).
Uso: python3 sfx.py   -> operacao-sigilo-FINAL.mp4"""
import os, subprocess, wave, math
import numpy as np
import build as B

SR = 44100
OUT = B.OUT
dur = B.TOTAL + .6
N = int(dur * SR)
rng = np.random.default_rng(3)
fx = np.zeros(N); bed = np.zeros(N)

def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0: s = s[-i:]; i = 0
    j = min(N, i + len(s))
    if j > i: buf[i:j] += s[:j - i] * g

def lowpass(x, a):  # filtro de um polo; a pode ser array (varredura)
    y = np.empty_like(x); acc = 0.0
    if np.isscalar(a): a = np.full(len(x), a)
    for n in range(len(x)): acc += a[n] * (x[n] - acc); y[n] = acc
    return y

def whoosh(d_=.35):
    n = int(d_ * SR); x = rng.standard_normal(n); t = np.linspace(0, 1, n)
    a = .02 + .5 * np.sin(np.pi * t) ** 2
    y = lowpass(x, a); y -= lowpass(y, .01)
    return y * np.sin(np.pi * t) ** 1.5 * 2.2

def boom(d_=.9, f0=70):
    n = int(d_ * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (f0 * np.exp(-t * 3) + 28) * t) * np.exp(-t * 4.5)
    nz = lowpass(rng.standard_normal(n), .08) * np.exp(-t * 9) * 1.5
    return (s + nz) * 1.4

def click(d_=.03, f=1800):
    n = int(d_ * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180)

def glitch(d_=.14):
    n = int(d_ * SR); x = rng.standard_normal(n)
    gate = (np.sin(np.arange(n) / SR * 2 * np.pi * 60) > 0).astype(float)
    return x * gate * np.linspace(1, 0, n) * .6

def crack(d_=.5):
    n = int(d_ * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-t * 14); x -= lowpass(x, .05)
    return x * 1.4 + boom(d_, 55)[:n] * .5

def tick(f=900):
    n = int(.05 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90)

# --- eventos sincronizados com o vídeo
for i, sc in enumerate(B.timeline):
    s0 = sc["start"]
    if i > 0:
        add(fx, s0 - .28, whoosh(), .55); add(fx, s0, boom(.5, 90), .5); add(fx, s0, glitch(), .4)
    for ch in sc["chunks"][1:]: add(fx, ch["start"], click(), .22)
    for ti in B.IMPACTS.get(sc["kind"], []):
        t_ = s0 + ti / sc["speed"]
        add(fx, t_, boom(1.0, 75), .85)
        if sc["kind"] in ("ataque",): add(fx, t_, crack(), .9)
    if sc["kind"] == "relogio2":
        for k in range(int(sc["dur"] * 4)): add(fx, s0 + k * .25, tick(900 if k % 2 else 700), .35)
    if sc["kind"] == "cta": add(fx, s0 + 4.3 / sc["speed"], click(.06, 1200), .6)
    if sc["kind"] == "login":
        for k in range(8): add(fx, s0 + .6 + k / 6, click(.025, 2400), .25)
    if sc["kind"] == "porta": add(fx, s0 + 3.0, boom(1.2, 60), .6)

# --- trilha: drone grave + pulso + textura
t = np.arange(N) / SR
drone = (np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.4 * t + np.sin(t * .3)) * .3 + np.sin(2 * np.pi * 110.5 * t) * .15) * (.75 + .25 * np.sin(2 * np.pi * t / 7.0))
pad = np.sin(2 * np.pi * 220 * t) * .06 * (.5 + .5 * np.sin(2 * np.pi * t / 11)) + np.sin(2 * np.pi * 329.6 * t) * .035 * (.5 + .5 * np.sin(2 * np.pi * t / 13 + 1))
rumble = lowpass(rng.standard_normal(N), .01) * 3
beat = np.zeros(N)
for k in range(int(dur * 1.0)):  # pulso de 60 bpm
    add(beat, k * 1.0, boom(.45, 55)[:int(.45 * SR)], .35); add(beat, k * 1.0 + .5, boom(.3, 45)[:int(.3 * SR)], .15)
bed = drone * .6 + pad + rumble * .5 + beat * .6
fade = np.minimum(1, np.minimum(t / 1.5, (dur - t) / 2.0)); bed *= fade

def norm(x, peak): return x / (np.abs(x).max() + 1e-9) * peak
mix = norm(bed, .30) + norm(fx, .55) * 1.0
mix = np.clip(mix, -1, 1)
st = np.stack([mix, np.roll(mix, 40)], 1)  # leve largura estéreo
pcm = (st * 32767).astype(np.int16)
wp = os.path.join(OUT, "audio", "trilha-sfx.wav")
with wave.open(wp, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

voice = os.path.join(OUT, "audio", "narracao-v5.mp3")
vid = os.path.join(OUT, "operacao-sigilo-COM-AUDIO.mp4")
final = os.path.join(OUT, "operacao-sigilo-FINAL.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", voice, "-i", wp, "-filter_complex",
    "[1:a]loudnorm=I=-16:TP=-1.5:LRA=7,aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[v1][v2];"
    "[2:a]volume=0.55[m];[m][v2]sidechaincompress=threshold=0.015:ratio=8:attack=15:release=350:makeup=1[md];"
    "[v1]volume=1.0[vv];[vv][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final], check=True)
print("ok", final)
