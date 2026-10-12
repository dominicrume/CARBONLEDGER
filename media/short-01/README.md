# Short 01: "Being smart is not the hard part. Keeping score is."

A 71 second vertical YouTube Short (1080x1920, 30 fps) in the chalkboard-explainer grammar: a wood-framed board,
thin chalk diagrams that draw themselves, one big caption with an orange keyword, live word-by-word subtitles, and
Leaf, our own pixel presenter made from the CarbonLedger mark. Scene 4 draws the repo's real folder architecture.

| File | Job |
|---|---|
| script.json | the seven scenes: caption, keyword, voice line, and the measured voice length |
| index.html | the stage. Every frame is a pure function of time, so renders are exact and repeatable. `?play` previews it |
| voice.py | records the voice lines (macOS say by default; OpenAI or ElevenLabs with a key in the environment) |
| render.mjs | renders stills or every frame with headless Chromium |
| build.sh | renders, lays each line at its scene, adds room tone, muxes `out/carbonledger-short-01.mp4` |

```
python3 voice.py                                 # draft voice
VOICE_PROVIDER=elevenlabs ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=... python3 voice.py   # final voice
./build.sh                                       # frames + mix + mp4 (needs ffmpeg and the web app's Playwright)
```
Claims on screen follow rules/HARDENING-PRODUCT.md: "simulated pilot units" stays on screen the whole time, no
"offset", and "26 registries" is the sourced figure in docs/PITCH-FACTS.md.
