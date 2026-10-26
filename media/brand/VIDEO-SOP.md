# Video standard operating procedure (the VOREM style and our other house styles)

How we make videos that clear the bar, from a raw phone take to a 7-minute academic film in the presenter's own
cloned voice. Read with `media/brand/BRAND-VOICE.md` (what CarbonLedger says) and `rules/HARDENING-PRODUCT.md` (what we
may claim). The engine is `media/video-kit/`; its README has the commands. Section 9 is a prompt you can paste into
another system so it produces the same quality.

## 1. The bar
The benchmark is the "Smart Campus, Zero Waste" film (October 2026). It is a 7:24 academic presentation in the
VOREM motion style, narrated in a clone of the presenter's own voice, and the client called it "perfect".

The version before it was rejected for one reason: it was slides in a frame read by a flat voice. It was correct but
not engaging. Everything below exists to stop that happening again.

| Measure | Target |
|---|---|
| Hard cuts | 0 in the VOREM style: every change is a wipe, a camera move or a card arriving (0 cuts in all three VOREM references). Style E is the exception: a hard cut every 3 to 5 s. |
| Loudness | -14 LUFS integrated, true peak -1 dB, loudness range about 3 LU (the VOREM references measure 2.7 to 4) |
| Sound bed | Never silent: music under the whole film, ducked under the voice |
| Voice | The presenter's own voice (with consent), or a calm and measured AI voice at 130 to 150 wpm, with a breath after every sentence |
| Captions | 2 or 3 words at a time, timed to each spoken word, with the key word underlined. Plus an .srt file. |
| Sync | Every on-screen element appears on the word that names it |
| Claims | Every number has a source on screen and on the references screen. Anything else is labelled "illustration". |

## 2. The five house styles
Pick one per film. Styles B, C and D render on the engine (section 4). A and E edit real footage.

| Style | Made | Use it for | Look |
|---|---|---|---|
| **A. Raw talking head, enhanced** | `ORIGINAL CARBON LEDGER VIDEO.mp4` becomes `media/original-enhanced` | Real footage of a real person: founders, testimonials | A single vertical phone take (480x854, 163 s, no cuts, -28.5 LUFS) re-framed to 16:9: sharp subject centred over a blurred, scaled copy of itself. A vertical cut too. Loudness lifted to -14 LUFS. Content untouched. |
| **B. Chalkboard explainer** | `media/short-01` (71 s, 9:16) | Social shorts that explain one idea | A wood-framed board, chalk diagrams that draw themselves, one big caption with an orange keyword, word subtitles, and a pixel mascot made from the brand mark |
| **C. Presenter kinetic** | `media/landscape-01` (102 s, 16:9) | Founder-led brand films | The presenter's cut-out full body to open and close, a round portrait with a voice ring in between, an italic serif lead-in over a bold keyword, an orange diagonal wipe per scene, halftone texture (see BRAND-VOICE.md section 3) |
| **D. VOREM style** (the gold standard; VOREM's own house style, keep the name) | Learned from the three VOREM references (Digital OTC Desk, Master AI in 9 Days, the 9:16 brand film); first applied in the October 2026 academic film, on `media/video-kit` | Presentations, pitches, explainers over 1 minute | See below |
| **E. Rume social promo** | Rume's MCKI Solution (68 s) and YTube Booster Pro (43 s) videos, 1080x1920 | Founder ads and offers on Reels, TikTok, Shorts | A hard cut every 3 to 5 s (14 and 12 cuts). Real talking-head footage alternates with cut-out B-roll on cream halftone paper (a stamped "visa scam" note, a plane over a map, a graduate). Kinetic captions: a small italic serif lead-in over a bold orange keyword. A "RUME DOMINIC" logo bug top left, the product logo on its own beat, a phone-number or link pill to close. He speaks 139 to 152 wpm (162 to 174 while speaking), median 125 to 130 Hz. Script: call out the audience, a flip ("isn't content, it is blindness"), a personal story, the product named plainly, "click the link below and get started today". Loudness -15 to -24 LUFS as delivered; master to -14. |

**Style D, the VOREM style, in detail** (learned from the three VOREM references):
- **Background:** navy-black (#080B13) with one slow-drifting amber glow (#F2A93B), a faint dot grid and a vignette.
- **Headlines:** uppercase Manrope 800, two lines, one of them amber. They wipe in through a mask, line by line, and wipe out upward. A small mono eyebrow sits above (JetBrains Mono, letter-spaced).
- **Visuals:** floating UI cards in 3D, tilted about 9 degrees, drifting and bobbing. Cards are things the audience recognises: an invoice, a phone app, a camera view, a map with a route, a gauge.
- **Timelines:** a gold numbered timeline for any sequence (agenda, causes, phases, roles). A node turns amber on the word that names it, and the spine fills down to it. Status chips explain each node.
- **Numbers:** they count up on the word, with the source chip beside them.
- **Presenter:** a large cut-out with a name card in the first and last beat. A small card with a live voice meter in between.
- **Furniture:** a chapter counter top right ("02 / 05"), and a large outlined chapter number that flares as each chapter starts. An end lockup (ring mark, title, amber rule, tagline), then the references, silent.
- **Engagement without gimmicks:**
  - one "Quick question" quiz card with options and a countdown ring;
  - rhetorical questions as headlines ("Is it worth it?");
  - three-beat lines ("No guessing. No error.").
  For academic work, every element still maps to a marking-rubric section.

## 3. The script
- **Structure for a talk or presentation:**
  1. the hook;
  2. the question or problem;
  3. the agenda;
  4. the problem as three causes;
  5. the solutions;
  6. the plan, with phases and roles;
  7. the impact, on three pillars, measured;
  8. the conclusion;
  9. the ask.
  Academic work follows the brief's marking rubric exactly, one chapter per rubric section.
- **Structure for CarbonLedger brand videos:** Rume's structure (BRAND-VOICE.md section 2) and the claims checklist (section 7).
- **Beats:** write `film.json` as beats of 1 to 4 sentences. Each beat has a two-line headline (one amber line), a visual group, and words the visual will react to. Consecutive beats with the same group are steps of one visual, which keeps continuity.
- **Use the presenter's own words when you have them.** If they recorded their version, transcribe it (section 5) and keep their keywords and signposting ("So our first solution…", "And the second one is…"). Replace any claim in it that has no source.
- **Budget the length before recording.** the academic film's numbers are in brackets:

  `total ≈ words ÷ speaking_wpm × 60 + sentences × pause + beats × 0.85 + 0.6 + end card + references`

  (831 words, 79 sentences, 39 beats: 397 s of speech, 444 s in all, against a 449 s cap). If it's over, cut words, never pace: keep the voice at the speaker's own speed.

## 4. The pipeline (media/video-kit)
Every frame is `render(t)` of one web page, so a render is exact and repeatable. A fix is a code change and a re-render,
never a manual re-edit.
```
film.json            → the script as beats, plus meta (names, end card, references, pronunciations)
voice/measure.py     → learn the speaker: pace, characters a second, pauses, pitch, a timed transcript
voice/clone_tts.py   → narrate in their cloned voice, one sentence at a time (or voice/draft_tts.py for a stock voice)
voice/qc.py          → transcribe each take, reject dropped or invented phrases, join with the speaker's pauses
voice_finish.py      → a close-mic finish: low cut, presence, gentle compression, no added room
words.py             → word timings (faster-whisper aligned to the script) and the voice meter's loudness envelope
bed.py               → the timeline, the music bed (A-minor pad, soft plucks, whooshes, chapter swells), the length check
stage.html           → the visual groups, driven by data attributes, so a new visual is markup only
render.mjs, build.sh → stills or every frame (8 parallel parts), the mix (bed ducked under voice, -14 LUFS), mp4 and .srt
make_all.sh          → all of the above in one resumable command
```

## 5. The voice
1. **Learn it.**
   - Run `voice/measure.py recording.m4a`. It reports pace overall and while speaking, characters a second, the pause after a full stop and after a comma, median pitch, and a timed transcript.
   - The academic film's speaker: 105 wpm overall, 114 while speaking, 0.65 s after a full stop, 0.28 s after a comma, median pitch 170 Hz.
   - The VOREM voice: 128 to 152 wpm, about one pause per sentence, median pitch 157 to 180 Hz.
2. **Clone it, only with the speaker's consent and a disclosure.**
   - Cut two clean phrases of 5 to 8 seconds each, with no music, at 24 kHz mono, and write their exact words into `voice/refs.json`.
   - F5-TTS on MLX runs on the Mac with no account and no upload. ElevenLabs is the hosted alternative.
3. **Generate one sentence at a time.**
   - Give each sentence the length the speaker's own pace gives it: characters ÷ CPS.
   - Join the sentences with their measured pauses.
   - Spell out numbers and acronyms for the voice (`meta.pronounce`). Captions keep the digits.
4. **Check every take.** qc.py transcribes each one and regenerates any take that drops or invents a phrase. Number words count the same as digits, and short lines get more slack. Expect about 10% of takes redone in round 1 and none left by round 2.
5. **Listen end to end before handing over.** A clone can still mispronounce a name.

## 6. Quality control (every film, in this order)
1. **Stills per beat** (`node render.mjs stills`), tiled into a contact sheet. Check every one for overflow, clipping, overlaps, and anything appearing before its word.
2. **Hero frames at full size:** the face, the edges of the cut-out, and caption legibility.
3. **Length and loudness of the mp4:** `ffprobe` for length; `ffmpeg -af ebur128` should give I -14, LRA about 3.
4. **Frames from the finished file:** the opening, three middle points, the end lockup and the references.
5. **A human watches the whole film with sound** before it ships.

## 7. Claims, privacy and disclosure
- **CarbonLedger:**
  - say "pilot units, not yet verified credits"; never "offset", "carbon neutral", "net zero" or "verified credits" for them;
  - say "recorded on Solana devnet, a test network";
  - take live facts from carbonledger.world on the day you record;
  - no figure without a source in `docs/PITCH-FACTS.md`.
- **Academic work:**
  - every figure on screen has a reference;
  - vendor and self-reported figures are labelled as such;
  - illustrative visuals say "Illustration";
  - an AI-use statement says exactly how the narration was made, and a label stays on screen ("Narration · AI clone of X's own voice").
- **This repository is public.** Never commit:
  - a person's photo, voice recording or cloned takes;
  - a student's unsubmitted work (a public copy can trip their own plagiarism check);
  - keys.
  Client projects stay in git-ignored folders. Only the kit and this SOP are committed.

## 8. Lessons that cost us time
- **Rejected:** slides in a frame plus a stock voice. **Accepted:** VOREM motion plus the person's own voice. Engagement comes from motion that follows the words, not from more slides.
- **Never use `Math.random()` in a stage.** Parallel render parts must agree frame for frame. Seed everything from the index.
- **f5-tts-mlx 0.2.6 with MLX 0.32:** `mx.random.normal` needs `int(dur)` in `cfm.py` line 373.
- **A checker that compares words** must treat "one" and "1" as the same, or it rejects good takes.
- **The venv that runs qc.py needs `soundfile`.**
- **Long jobs:** run them with `nohup … &` and make every step resumable (only missing takes regenerate). Sessions drop.
- **Background-clip text:** a gradient on a parent with `background-clip: text` disappears when its children animate. Put it on each word.
- **Overflow:** size headline type to the longest line.
- **Live facts change:** landscape-01 says Kiribati and the app now says Tuvalu. Read live facts on the day.

## 9. The prompt
Paste this into Claude Code, or any agent with a shell, ffmpeg, Node with Playwright and Python, in this repository.
Fill the brackets.

> Make a [length, e.g. "7:00 maximum"] [landscape 1920x1080] video: **[title]**, for **[audience and venue]**,
> presented by **[name, role]**.
>
> **Brief and content**
> - Script: [paste it, or "from the recording at <path>"].
> - Marking rubric or brief: [paste it].
> - Sources: [paste them].
>
> **Production**
> - Follow `media/brand/VIDEO-SOP.md` exactly. Use style **D (the VOREM style)** on the engine in `media/video-kit` (or style [A/B/C/E] if I say so).
> - Copy the kit into a new git-ignored folder.
> - Write `film.json` as beats, one chapter per rubric section. Each beat has a two-line headline with one amber line and a visual group whose elements appear on the words that name them.
> - Add one quiz card and at least two rhetorical-question headlines, keeping it professional.
> - Budget the length with the SOP formula before recording, and cut words, not pace, if it is over.
>
> **Voice**
> - Run `voice/measure.py` on [recording]. Report the person's pace, pauses and pitch.
> - Clone the voice with `voice/clone_tts.py` only if I confirm they consented. Otherwise use `voice/draft_tts.py`.
> - Narrate every sentence at their measured pace and pauses, and check every take with `voice/qc.py`.
>
> **Accuracy and disclosure**
> - Every number on screen has a source chip and appears on the references screen. Label illustrations.
> - Write an AI-use statement that says exactly how the narration was made.
> - Never commit the person's photo, voice, takes or unsubmitted work.
>
> **Before and after the render**
> - Before rendering, show me a contact sheet of one still per beat and fix any overflow or early reveals.
> - Then run `make_all.sh` detached and report: the mp4 path, its length (under the cap), its loudness (-14 LUFS), and frames from the finished file.
> - Tell me what you changed from my script and why, and what I must check by listening.
