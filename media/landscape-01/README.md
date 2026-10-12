# Landscape 01: "The biggest risk in carbon credits is counting the same tonne twice"

A 95 second landscape film (1920x1080, 30 fps) presented by Rume Dominic. It replaces Leaf, the pixel presenter from short-01,
with Rume: full body for the open and the close, and a round portrait with a voice-driven ring in between. Voice, structure and
type follow media/brand/BRAND-VOICE.md.

| File | Job |
|---|---|
| script.json | nine scenes: lead-in, keyword, presenter mode, voice line, measured voice length |
| voice.py | records the lines and writes audio/env.json, the loudness per frame that moves the presenter |
| index.html | the stage. Every frame is a pure function of time. `?play` previews it silently |
| render.mjs | renders stills or every frame with headless Chromium |
| build.sh | frames, then voice, music bed (ducked under the voice) and a whoosh on each cut, then the mp4 |
| rume.png | Rume's cut-out, made on this Mac with Apple Vision from his suit photo |

```
python3 voice.py                                      # British draft voice (macOS Daniel)
VOICE_PROVIDER=elevenlabs ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=... python3 voice.py   # Rume's cloned voice
./build.sh                                            # out/carbonledger-landscape-01.mp4
```

## Rume's real voice
Make an Instant Voice Clone in ElevenLabs from media/brand/voice-samples/rume-sample-1.wav and rume-sample-2.wav (about 110 s
together; both have some music under them, so a clean 60 s recording of Rume reading this script would clone better).
Put the voice id in your shell, never in this folder, and run voice.py with VOICE_PROVIDER=elevenlabs.

## Claims
"Pilot units, not yet verified credits" stays on screen the whole time and is said aloud in scene 8. No "offset", no price,
no market size. "26 registries" is the sourced figure in docs/PITCH-FACTS.md. The basket figure in scene 6 is an illustration.
