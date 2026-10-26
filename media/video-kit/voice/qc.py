#!/usr/bin/env python3
"""Checks every take: faster-whisper hears it, and a take whose words differ from the script (a dropped, repeated or
invented phrase) is deleted and given a new seed, so the next clone_tts.py run redoes it. Then joins each beat's takes
with the speaker's pauses into audio/<beat>.raw.wav. Usage: qc.py <film.json>   (runs in the venv with faster-whisper)"""
import difflib, json, os, re, subprocess, sys
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
film = sys.argv[1]; F = json.load(open(film)); film_dir = os.path.dirname(os.path.abspath(film))
TAKES = os.path.join(film_dir, "takes"); SEEDS = os.path.join(TAKES, "seeds.json"); seeds = json.load(open(SEEDS))
SR = 24000
STOP, QUESTION = float(os.environ.get("STOP", .60)), float(os.environ.get("QUESTION", .70))   # measured pause after . and ?
NUM = {"fifty": "50", "two hundred": "200", "eighty-five": "85", "sixty-two": "62", "ninety": "90", "forty-eight": "48", "forty": "40",
       "twenty-five": "25", "twelve": "12", "six hundred and fifty": "650", "twenty eleven": "2011"}
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
def words(t):
    t = t.lower().replace("%", " per cent")
    for a, b in NUM.items(): t = t.replace(a, b)
    small = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "twelve": "12"}
    return [small.get(norm(w), norm(w)) for w in t.replace("-", " ").split() if norm(w)]
model = WhisperModel("small", device="cpu", compute_type="int8")
bad = 0; report = json.load(open(os.path.join(TAKES, "qc.json"))) if os.path.exists(os.path.join(TAKES, "qc.json")) else {}
for b in F["beats"]:
    sents = [p for p in re.split(r"(?<=[.?!])\s+", b["text"].strip()) if p]
    parts, ok_all = [], True
    for k, s in enumerate(sents):
        key = f"{b['id']}_{k:02d}"; path = os.path.join(TAKES, key + ".wav")
        if not os.path.exists(path): ok_all = False; continue
        wav = sf.read(path)[0].astype(np.float32)
        if True:
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
            heard = " ".join(x.text for x in model.transcribe(np.frombuffer(pcm, np.float32), language="en")[0])
            a, h = words(s), words(heard)
            sm = difflib.SequenceMatcher(a=a, b=h, autojunk=False)
            match = sum(n for *_, n in sm.get_matching_blocks())
            report[key] = {"seed": seeds.get(key), "recall": round(match / max(len(a), 1), 2), "extra": len(h) - match, "heard": heard.strip()}
        r = report[key]
        # an accent can fool the recogniser on a word or two, so allow a little; refuse dropped or invented phrases.
        n = len(words(s)); floor = .5 if n <= 4 else .7 if n <= 10 else .8     # one misheard word sinks a short line
        if r["recall"] < floor or r["extra"] > max(3, n * .2):
            print(f"REDO {key} recall {r['recall']} extra {r['extra']}: {r['heard']}"); os.remove(path)
            seeds[key] = seeds.get(key, 11) + 101; bad += 1; ok_all = False; continue
        # trim the silence the model leaves at the ends, then the speaker's pause
        lv = np.abs(wav) > .01; idx = np.where(lv)[0]
        wav = wav[max(0, idx[0] - 1200): idx[-1] + 2400] if len(idx) else wav
        parts += [wav, np.zeros(int((QUESTION if s.endswith("?") else STOP) * SR), np.float32)]
    if ok_all and parts:
        sf.write(os.path.join(film_dir, "audio", f"{b['id']}.raw.wav"), np.concatenate(parts[:-1]), SR)
json.dump(seeds, open(SEEDS, "w"), indent=0); json.dump(report, open(os.path.join(TAKES, "qc.json"), "w"), indent=1)
print("rejected", bad)
