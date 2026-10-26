#!/usr/bin/env python3
"""The timeline and the sound bed. Sets each beat's start, speaking time and end in film.json, then writes
audio/bed.wav: a slow A-minor pad with a soft pluck pattern underneath the whole film (VOREM never drops to silence),
an air whoosh at each change of visual and a low swell at each new chapter."""
import json, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(HERE, "film.json")))
LEAD, TAIL, END, REFS, SR = 0.4, 0.45, 5.0, 8.0, 48000
t = 0.6
for i, b in enumerate(F["beats"]):
    b["start"], b["speak"] = round(t, 3), round(t + LEAD, 3)
    t += LEAD + b["voice_s"] + TAIL
    b["end"] = round(t, 3)
F["end_at"], F["refs_at"], F["total"] = round(t, 3), round(t + END, 3), round(t + END + REFS, 3)
json.dump(F, open(os.path.join(HERE, "film.json"), "w"), indent=1, ensure_ascii=False)

n = int(F["total"] * SR); x = np.arange(n) / SR; out = np.zeros(n)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
CHORDS = [[45, 57, 60, 64, 71], [41, 53, 57, 60, 67], [48, 55, 60, 64, 74], [43, 55, 59, 62, 69]]   # Am9 Fmaj9 Cadd9 G6
BAR = 8.0
rng = np.random.default_rng(7)
for k in range(int(F["total"] / BAR) + 2):
    a, z = int(max(0, (k * BAR - 2) * SR)), int(min(n, (k * BAR + BAR + 2) * SR))
    if a >= n: break
    seg = x[a:z] - k * BAR
    envl = np.clip((seg + 2) / 3, 0, 1) * np.clip((BAR + 2 - seg) / 3, 0, 1)
    for m in CHORDS[k % 4]:
        f = hz(m)
        for det in (-0.12, 0.12):
            v = np.sin(2 * np.pi * (f + det) * x[a:z]) + 0.25 * np.sin(4 * np.pi * (f + det) * x[a:z])
            out[a:z] += 0.022 * envl * v * (0.6 if m < 50 else 1)
    for s in range(16):                                       # quiet plucks, two per second
        p0 = k * BAR + s * 0.5
        m = CHORDS[k % 4][1 + (s * 3) % 4] + 12
        a2, z2 = int(p0 * SR), int(min(n, (p0 + 1.6) * SR))
        if a2 >= n: break
        tt = x[a2:z2] - p0
        out[a2:z2] += 0.010 * (0.55 + 0.45 * (s % 4 == 0)) * np.exp(-tt * 3.2) * np.sin(2 * np.pi * hz(m) * tt)
def whoosh(at, length=0.9, g=0.05):
    a, z = int(at * SR), int(min(n, (at + length) * SR))
    if a >= n or a < 0: return
    w = rng.standard_normal(z - a); tt = np.arange(z - a) / SR
    w = np.convolve(w, np.ones(24) / 24, "same")                # soft, airy noise
    out[a:z] += g * w * np.sin(np.pi * tt / length) ** 2
def swell(at, g=0.07):
    a, z = int(at * SR), int(min(n, (at + 2.4) * SR))
    if a >= n: return
    tt = np.arange(z - a) / SR
    out[a:z] += g * np.sin(2 * np.pi * 55 * tt) * np.minimum(tt / 0.05, 1) * np.exp(-tt * 1.6)
prev = None
for b in F["beats"]:
    if prev and b["group"] != prev["group"]: whoosh(b["start"] - 0.35)
    if prev and b["chapter"] != prev["chapter"]: swell(b["start"])
    prev = b
whoosh(F["end_at"] - 0.3); swell(F["end_at"], 0.09)
fade = np.clip((F["total"] - x) / 4, 0, 1) * np.clip(x / 1.5, 0, 1)
out = np.tanh(out * fade * 1.4) * 0.8
pcm = (np.stack([out, np.roll(out, 240)], 1) * 32767).astype(np.int16)    # 5 ms offset: a little width
with wave.open(os.path.join(HERE, "audio", "bed.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
MAX = float(os.environ.get("MAX_S", 0))
print(f"total {F['total']:.1f}s = {int(F['total'] // 60)}:{int(F['total'] % 60):02d}" + (f"  OVER THE {MAX:.0f}s LIMIT: cut words" if MAX and F["total"] > MAX else ""))
