#!/usr/bin/env python3
"""Finishes the cloned narration (audio/<beat>.raw.wav from voice/qc.py) like a clean close-mic read of the speaker's own
voice: low cut, a touch of presence, gentle compression, no added room. Writes audio/<beat>.wav and each length."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(HERE, "film.json")))
FINISH = "highpass=f=70,equalizer=f=180:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.4:g=2,acompressor=threshold=-20dB:ratio=2.2:attack=10:release=150:makeup=2"
for b in F["beats"]:
    raw, out = os.path.join(HERE, "audio", f"{b['id']}.raw.wav"), os.path.join(HERE, "audio", f"{b['id']}.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", FINISH, "-ar", "48000", "-ac", "1", out], check=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout
    b["audio"], b["voice_s"] = f"audio/{b['id']}.wav", round(float(d), 2)
F["voice"] = "F5-TTS clone (voice/refs.json)"
json.dump(F, open(os.path.join(HERE, "film.json"), "w"), indent=1, ensure_ascii=False)
print("speech", round(sum(b["voice_s"] for b in F["beats"]), 1), "s")
