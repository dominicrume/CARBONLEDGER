#!/usr/bin/env python3
"""Record the voice line of every scene and store its length in script.json (the animation times itself from it).
VOICE_PROVIDER=say (default, macOS, free, draft quality) | openai | elevenlabs
  openai:     OPENAI_API_KEY, optional OPENAI_TTS_MODEL (default gpt-4o-mini-tts), OPENAI_TTS_VOICE (default onyx)
  elevenlabs: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
Keys come from the environment only, never from this folder. After changing the voice, re-render the frames."""
import json, os, subprocess, sys
import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "script.json")))
provider = os.environ.get("VOICE_PROVIDER", "say")
os.makedirs(os.path.join(HERE, "audio"), exist_ok=True)

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return float(out.stdout)
    return float(subprocess.run(["afinfo", path], capture_output=True, text=True).stdout.split("estimated duration:")[1].split()[0])

for sc in S["scenes"]:
    if provider == "say":
        path = os.path.join(HERE, "audio", f"{sc['id']}.aiff")
        subprocess.run(["say", "-v", os.environ.get("SAY_VOICE", "Daniel"), "-r", "172", "-o", path, sc["line"]], check=True)
    elif provider == "openai":
        path = os.path.join(HERE, "audio", f"{sc['id']}.mp3")
        r = httpx.post("https://api.openai.com/v1/audio/speech", timeout=120,
                       headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                       json={"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"), "voice": os.environ.get("OPENAI_TTS_VOICE", "onyx"),
                             "input": sc["line"], "instructions": "Calm, warm, confident explainer. British English. Unhurried."})
        r.raise_for_status(); open(path, "wb").write(r.content)
    elif provider == "elevenlabs":
        path = os.path.join(HERE, "audio", f"{sc['id']}.mp3")
        r = httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ['ELEVENLABS_VOICE_ID']}", timeout=120,
                       headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                       json={"text": sc["line"], "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}})
        r.raise_for_status(); open(path, "wb").write(r.content)
    else:
        sys.exit(f"unknown VOICE_PROVIDER {provider}")
    sc["audio"] = os.path.relpath(path, HERE); sc["voice_s"] = round(duration(path), 2)
    print(f"{sc['id']:9} {sc['voice_s']:5.2f}s")
S["voice_provider"] = provider
json.dump(S, open(os.path.join(HERE, "script.json"), "w"), indent=2)
