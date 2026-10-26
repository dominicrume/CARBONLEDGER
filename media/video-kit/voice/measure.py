#!/usr/bin/env python3
"""Learns how a person speaks from a recording: pace (overall and while speaking), characters a second for
clone_tts.py, pause after a full stop and after a comma, median pitch, and a timed transcript to pick clean reference
phrases from.  Usage: measure.py <recording> [out.json]   (runs in the venv with faster-whisper)"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
path = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
segs, info = WhisperModel("small", device="cpu", compute_type="int8").transcribe(a, language="en", word_timestamps=True)
segs = list(segs); words = [w for s in segs for w in s.words]
speech = sum(w.end - w.start for w in words); chars = sum(len(w.word.strip()) + 1 for w in words)
after = {}
for x, y in zip(words, words[1:]):
    k = x.word.strip()[-1] if x.word.strip()[-1:] in (".", ",", "?") else None
    if k: after.setdefault(k, []).append(y.start - x.end)
f0 = []
for i in range(0, len(a) - 640, 320):
    fr = a[i:i + 640]
    if np.sqrt(np.mean(fr ** 2)) < .02: continue
    ac = np.correlate(fr, fr, "full")[639:]; k = 40 + int(np.argmax(ac[40:228]))
    if ac[k] > .3 * ac[0]: f0.append(16000 / k)
M = {"seconds": round(info.duration, 1), "words": len(words), "wpm_overall": round(len(words) / info.duration * 60),
     "wpm_speaking": round(len(words) / speech * 60), "CPS": round(chars / speech, 1),
     "pause_after": {k: round(float(np.median(v)), 2) for k, v in after.items()},
     "pitch_hz": {"median": round(float(np.median(f0))), "p10": round(float(np.percentile(f0, 10))), "p90": round(float(np.percentile(f0, 90)))}}
print(json.dumps(M, indent=1))
for s in segs: print(f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}")
if len(sys.argv) > 2:
    json.dump({**M, "segments": [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs]}, open(sys.argv[2], "w"), indent=1)
