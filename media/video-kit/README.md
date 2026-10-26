# Video kit: script to finished film, VOREM motion style

The engine behind style D in `media/brand/VIDEO-SOP.md`. A film is one `film.json` (beats, plus meta) rendered by one
web page, `stage.html`, where every frame is `render(t)`. Read the SOP first.

## Start a film
```
cp -R media/video-kit media/<project>        # projects with a person's photo or voice must be git-ignored (SOP section 7)
cd media/<project> && cp film.example.json film.json
# add presenter.png (a cut-out, transparent background) and presenter-card.png (a square face crop)
```

## One-time setup (Apple Silicon Mac)
```
python3 -m venv .venv && .venv/bin/pip install faster-whisper soundfile numpy        # word timings and checks
python3 -m venv voice/f5env && voice/f5env/bin/pip install f5-tts-mlx                  # voice cloning (first run downloads the model)
# f5-tts-mlx 0.2.6 with mlx 0.32: in voice/f5env/.../f5_tts_mlx/cfm.py line 373, use int(dur)
export PLAYWRIGHT="$PWD/../../apps/web/node_modules/playwright/index.mjs"
```

## Make it
```
.venv/bin/python voice/measure.py recording.m4a measure.json   # the speaker's pace, pauses, pitch, a timed transcript
# cut two clean 5-8 s phrases to voice/refA.wav and voice/refB.wav (24 kHz mono), write voice/refs.json
CPS=13.5 STOP=0.6 MAX_S=449 nohup ./make_all.sh > make_all.log 2>&1 &    # clone, check, finish, time, bed, render
```
For a stock voice instead of a clone, run `python3 voice/draft_tts.py` and then `words.py`, `bed.py` and `build.sh`.

Preview while editing: `python3 -m http.server 8822`, then open `http://127.0.0.1:8822/stage.html?play&t=60`.
For stills: `node render.mjs stills /tmp/stills`.

## Add a visual
A visual group is markup in `G` in `stage.html`. Elements react to the narration through data attributes:

| Attribute | What it does |
|---|---|
| `data-w="word"` | appears when the word is spoken (`word#2` for its second time) |
| `data-aw="word"` | turns amber on the word |
| `data-count="62"` | counts up |
| `data-fill="1"` | fills `var(--f)` |
| class `dl` with `pathLength="1"` | draws an SVG line |
| class `card` | floats in 3D |

Each beat can carry its own data (`items`, `value`, `question`), which the group reads. Five example groups ship with the kit: `hero`, `three`, `steps`, `stat` and `quiz`.

## Output
- `out/film.mp4`: 1920x1080, 30 fps, -14 LUFS
- `out/film.srt`: the captions file
