#!/usr/bin/env python3
"""Draft voice (no clone): records each beat of film.json in the VOREM delivery: calm, measured, a breath after every sentence.

Default: the macOS voice Samantha (female). With ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in the environment it uses
ElevenLabs instead, which is how the VOREM reference voice was most likely made. The raw take is then finished like a
studio read: low cut, a little warmth, gentle compression, a short room. Writes audio/<id>.wav and the length."""
import json, os, re, subprocess, urllib.request
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(HERE, "film.json")))
VOICE, RATE = os.environ.get("VOICE", "Samantha"), os.environ.get("RATE", "150")
SAY = [(r"\bMSc\b", "M.S.c."), (r"\bPET\b", "P.E.T."), (r"\bESG\b", "E.S.G."), (r"\bLED\b", "L.E.D."), (r"\bUS\b", "U.S."),
       (r"’", "'"), (r"[“”]", "")]
FINISH = ("highpass=f=75,equalizer=f=220:t=q:w=1.1:g=2.5,equalizer=f=3200:t=q:w=1.4:g=1.5,equalizer=f=7500:t=q:w=2:g=-3,"
          "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,aecho=0.85:0.5:28|47:0.10|0.06")

def spoken(text):
    for a, b in SAY:
        text = re.sub(a, b, text)
    parts = re.split(r"(?<=[.?!])\s+", text.strip())            # one breath per sentence, as VOREM does
    return " [[slnc 430]] ".join(parts) + " [[slnc 120]]"

def eleven(text, path):
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ['ELEVENLABS_VOICE_ID']}",
        data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                         "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15}}).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json", "Accept": "audio/mpeg"})
    open(path, "wb").write(urllib.request.urlopen(req).read())

use_eleven = bool(os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("ELEVENLABS_VOICE_ID"))
for b in F["beats"]:
    raw, out = os.path.join(HERE, "audio", f"{b['id']}.raw" + (".mp3" if use_eleven else ".aiff")), os.path.join(HERE, "audio", f"{b['id']}.wav")
    if use_eleven:
        eleven(re.sub(r"[“”]", "", b["text"]), raw)
    else:
        subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", raw, spoken(b["text"])], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", FINISH, "-ar", "48000", "-ac", "1", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout
    b["audio"], b["voice_s"] = f"audio/{b['id']}.wav", round(float(dur), 2)
    print(f"{b['id']} {b['group']:9} {b['voice_s']:6.2f}s")
F["voice"] = "elevenlabs" if use_eleven else VOICE
json.dump(F, open(os.path.join(HERE, "film.json"), "w"), indent=1, ensure_ascii=False)
print("speech", round(sum(b["voice_s"] for b in F["beats"]) / 60, 2), "min")
