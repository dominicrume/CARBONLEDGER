#!/usr/bin/env python3
"""Record every scene's voice line, store its length in script.json and a 30 fps loudness envelope in audio/env.json.
The avatar moves with that envelope, so it reacts to the real voice rather than a fake mouth loop.
VOICE_PROVIDER=say (default, macOS, British draft) | elevenlabs | openai
  say:        SAY_VOICE (default Daniel, en_GB), SAY_RATE (default 162 words a minute; Rume speaks at about 140 to 150)
  elevenlabs: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (Rume's cloned voice, made from media/brand/voice-samples)
  openai:     OPENAI_API_KEY, optional OPENAI_TTS_MODEL (default gpt-4o-mini-tts), OPENAI_TTS_VOICE (default ash)
Keys come from the environment only, never from this folder. After changing the voice, re-run ./build.sh."""
import json, os, subprocess, sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "script.json")))
provider = os.environ.get("VOICE_PROVIDER", "say")
os.makedirs(os.path.join(HERE, "audio"), exist_ok=True)
FPS = 30

def envelope(path):
    """Loudness per frame, 0 to 1, from the decoded audio (RMS over each 1/30 s, normalised to the line's loudest frame)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "24000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    pcm = array("h"); pcm.frombytes(raw)
    step = 24000 // FPS
    rms = [(sum(x * x for x in pcm[i:i + step]) / step) ** 0.5 for i in range(0, len(pcm) - step + 1, step)]
    peak = max(rms) or 1
    return [round(min(1.0, r / peak) ** 0.7, 2) for r in rms], len(pcm) / 24000

def post(url, headers, body):
    import httpx
    r = httpx.post(url, headers=headers, json=body, timeout=120)
    r.raise_for_status()
    return r.content

ENV = {}
for sc in S["scenes"]:
    sc.pop("env", None)
    if provider == "say":
        path = os.path.join(HERE, "audio", f"{sc['id']}.aiff")
        subprocess.run(["say", "-v", os.environ.get("SAY_VOICE", "Daniel"), "-r", os.environ.get("SAY_RATE", "162"), "-o", path, sc["line"]], check=True)
    elif provider == "elevenlabs":
        path = os.path.join(HERE, "audio", f"{sc['id']}.mp3")
        open(path, "wb").write(post(f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ['ELEVENLABS_VOICE_ID']}",
                                    {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                                    {"text": sc["line"], "model_id": "eleven_multilingual_v2",
                                     "voice_settings": {"stability": 0.45, "similarity_boost": 0.85, "style": 0.25}}))
    elif provider == "openai":
        path = os.path.join(HERE, "audio", f"{sc['id']}.mp3")
        open(path, "wb").write(post("https://api.openai.com/v1/audio/speech",
                                    {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                                    {"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"), "voice": os.environ.get("OPENAI_TTS_VOICE", "ash"),
                                     "input": sc["line"],
                                     "instructions": "Educated British English accent, London. Warm, confident founder speaking straight to camera. "
                                                     "Unhurried, about 145 words a minute. Lean on the key word of each sentence."}))
    else:
        sys.exit(f"unknown VOICE_PROVIDER {provider}")
    sc["audio"] = os.path.relpath(path, HERE)
    ENV[sc["id"]], secs = envelope(path)
    sc["voice_s"] = round(secs, 2)
    print(f"{sc['id']:9} {sc['voice_s']:5.2f}s")
S["voice_provider"] = provider
json.dump(S, open(os.path.join(HERE, "script.json"), "w"), indent=2)
json.dump(ENV, open(os.path.join(HERE, "audio", "env.json"), "w"), separators=(",", ":"))
