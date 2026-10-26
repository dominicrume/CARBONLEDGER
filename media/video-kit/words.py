#!/usr/bin/env python3
"""Word timings for every beat: faster-whisper hears the take, difflib aligns it to the script's own words (so the
captions keep the script's spelling). Writes beat.words = [[start, end, word], ...] and an amplitude envelope per beat."""
import difflib, json, os, re, subprocess
import numpy as np
from faster_whisper import WhisperModel
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(HERE, "film.json")))
model = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
env = {}
for b in F["beats"]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, b["audio"]), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 16000 // 30                                            # loudness 30 times a second, for the voice meter
    rms = np.array([np.sqrt(np.mean(pcm[i:i + hop] ** 2)) for i in range(0, len(pcm), hop)])
    env[b["id"]] = [round(float(v), 3) for v in np.clip(rms / (np.percentile(rms, 95) + 1e-6), 0, 1)]
    segs, _ = model.transcribe(pcm, language="en", word_timestamps=True)
    heard = [(w.start, w.end, w.word.strip()) for s in segs for w in s.words]
    script = b["text"].split()
    sm = difflib.SequenceMatcher(a=[norm(w) for w in script], b=[norm(h[2]) for h in heard], autojunk=False)
    t = [None] * len(script)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            t[i + k] = heard[j + k][:2]
    known = [i for i, v in enumerate(t) if v]
    for i in range(len(script)):                                # unmatched words share the gap between neighbours
        if t[i] is None:
            lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
            s0 = t[lo][1] if lo is not None else 0.0; s1 = t[hi][0] if hi is not None else b["voice_s"]
            a = lo if lo is not None else -1; z = hi if hi is not None else len(script)
            t[i] = (s0 + (s1 - s0) * (i - a - 0.5) / (z - a), s0 + (s1 - s0) * (i - a + 0.4) / (z - a))
    b["words"] = [[round(s, 2), round(e, 2), w] for (s, e), w in zip(t, script)]
    print(f"{b['id']} matched {sum(n for *_, n in sm.get_matching_blocks()) / len(script):.0%}")
json.dump(F, open(os.path.join(HERE, "film.json"), "w"), indent=1, ensure_ascii=False)
json.dump(env, open(os.path.join(HERE, "audio", "env.json"), "w"))
