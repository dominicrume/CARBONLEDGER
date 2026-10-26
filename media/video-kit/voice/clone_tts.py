#!/usr/bin/env python3
"""Narrates film.json in a real person's own voice, with their consent: F5-TTS (MLX, runs on an Apple Silicon Mac)
cloned from 2 clean phrases of their recording (voice/refs.json), one sentence at a time. Each sentence gets the length
the speaker's own pace gives it (CPS, measured with voice/measure.py), and only missing takes are generated, so a rerun
after qc.py redoes just the rejected sentences.  Usage: clone_tts.py <film.json>   (runs in the F5 venv)"""
import json, os, re, sys
import mlx.core as mx
import numpy as np
import soundfile as sf
from f5_tts_mlx.cfm import F5TTS
from f5_tts_mlx.utils import convert_char_to_pinyin

HERE = os.path.dirname(os.path.abspath(__file__))
SR, HOP, TARGET_RMS = 24000, 256, 0.1
CPS = float(os.environ.get("CPS", 13.5))   # the speaker's articulation in characters a second (measure.py)
# refs.json: [{"file": "refA.wav", "text": "exactly what is said in it"}, ...], 24 kHz mono, 5 to 8 s each, no music
REFS = [(r["file"], r["text"]) for r in json.load(open(os.path.join(HERE, "refs.json")))]
SAY = [(r"’", "'"), (r"\bMSc\b", "M S C"), (r"\bESG\b", "E S G"),
       (r"\bLED\b", "L E D"), (r"\bAI\b", "A I"), (r"\bUS\b", "U S"), 
       (r"\b650\b", "six hundred and fifty"), (r"\b2011\b", "twenty eleven"), (r"\b200\b", "two hundred"), (r"\b85\b", "eighty-five"),
       (r"\b62\b", "sixty-two"), (r"\b90\b", "ninety"), (r"\b50\b", "fifty"), (r"\b48\b", "forty-eight"), (r"\b40\b", "forty"),
       (r"\b25\b", "twenty-five"), (r"\b12\b", "twelve")]

def spoken(s):
    for a, b in F.get("meta", {}).get("pronounce", []) + SAY:
        s = re.sub(a, b, s)
    return s

def sentences(text):
    return [p for p in re.split(r"(?<=[.?!])\s+", text.strip()) if p]

film = sys.argv[1]
F = json.load(open(film)); film_dir = os.path.dirname(os.path.abspath(film))
TAKES = os.path.join(film_dir, "takes"); os.makedirs(TAKES, exist_ok=True)
SEEDS = os.path.join(TAKES, "seeds.json")
seeds = json.load(open(SEEDS)) if os.path.exists(SEEDS) else {}

ref = np.concatenate([np.concatenate([sf.read(os.path.join(HERE, p))[0], np.zeros(int(.25 * SR))]) for p, _ in REFS])
ref_text = " ".join(t for _, t in REFS)
audio = mx.array(ref.astype(np.float32))
rms = float(mx.sqrt(mx.mean(mx.square(audio))))
if rms < TARGET_RMS: audio = audio * TARGET_RMS / rms
model = None

# Only takes that are missing are generated, so a rerun after qc.py redoes just the rejected sentences.
for b in F["beats"]:
    for k, s in enumerate(sentences(b["text"])):
        key = f"{b['id']}_{k:02d}"; path = os.path.join(TAKES, key + ".wav")
        if os.path.exists(path): continue
        model = model or F5TTS.from_pretrained("lucasnewman/f5-tts-mlx")
        say = spoken(s); seed = seeds.setdefault(key, 11 + k)
        frames = int((audio.shape[0] / SR + len(say) / CPS + .15) * SR / HOP)
        wave, _ = model.sample(mx.expand_dims(audio, 0), text=convert_char_to_pinyin([ref_text + " " + say]), duration=frames,
                               steps=8, method="rk4", cfg_strength=2.0, sway_sampling_coef=-1.0, seed=seed)
        sf.write(path, np.array(wave[audio.shape[0]:]), SR)
        json.dump(seeds, open(SEEDS, "w"), indent=0)
        print(key, flush=True)
