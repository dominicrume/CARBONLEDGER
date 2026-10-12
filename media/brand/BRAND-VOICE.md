# CarbonLedger brand voice: what we say, how Rume says it

Read this before writing any video, post, page or pitch. Sources: the original CarbonLedger video (the product message),
Rume Dominic's two talking-head videos (the voice and the style), rules/HARDENING-PRODUCT.md and docs/PITCH-FACTS.md
(the claim limits). Where they disagree, the claim rules win.

## 1. The core message (from the original CarbonLedger video)
One idea, five beats:
1. **The problem is the design, not a few bad actors.** Credits can be resold and counted twice, and nobody can see what they bought.
2. **The rules have to be in the code.** Not better auditing, not more promises.
3. **So CO2 itself becomes the ledger.** One register, every gram has a serial number, every gram is retired once.
4. **Anyone can join, one gram at a time.** Scan your shopping or add a journey, see the footprint, retire pilot units on the spot, no crypto wallet. Clearing a country's pilot target together is a shared game: the smallest first, or any country you choose.
5. **What comes next is evidence you can watch.** Each batch will link to its field video and satellite imagery, and a named verifier signs it off. Always say this as the plan ("what comes next"), never as true today.

Closing line to reuse: *"Imagine a ledger where the world pays down its carbon debt, one gram at a time."*

### Claims from the original video we can no longer say as recorded
The original video was made before the claim rules. Say it like this instead:

| The original said | Say instead | Why |
|---|---|---|
| "offset it on the spot" | "retire pilot units on the spot" | No "offset" for pilot units |
| "10p a kilo", "£100 a tonne" | say no price | No real-money step exists yet; no price without a source |
| "every purchase links to a real removal project" | "the backing comes when a named verifier attests a real project" | Today the demo project is simulated |
| "biochar locks carbon away for centuries" | only as the plan: "we intend to source from biochar" | Not true of today's units |
| "fewer than 1 in 6 credits delivered real cuts" | leave out until the study is cited in PITCH-FACTS | No source on file |
| "MSCI forecasts $10 to $40 billion by 2030" | leave out until cited in PITCH-FACTS | No market size without a source |
| "built so it can't be cheated" | "the same rules run in three places, and anyone can check a receipt" | Say what the code proves, not a guarantee |

Always on screen and in every caption set: **"Pilot units, not yet verified credits."** Say "Recorded on Solana devnet, a test network",
never "permanently on the blockchain".

## 2. How Rume speaks (from his own videos)
Measured from the transcripts: about **140 to 150 words a minute**, short sentences, first person, straight to camera.

**Structure, every time:**
1. **Call out the audience, then flip the expected answer.** "YouTube creators, the biggest risk to your channel isn't content. It is blindness."
2. **Name the problem in a list of three.** "...the right title, using data to drive views, and the right thumbnail."
3. **Personal proof, briefly.** "Two years ago, I was faced with a visa scam... Today, I am speaking to you from the UK."
4. **The fix, named plainly.** "All this can be solved with..." / "That is why we built..."
5. **What it does for you.** "Let's take the heavy lifting off your shoulders."
6. **The same call to action.** "Click the link below, get started today, and join the movement."

**Words he uses:** "the biggest risk", "isn't X, it is Y", "first hand", "I want to help you", "pathway", "level of", "get started today",
"join the movement". **Tone:** warm, confident, a mentor who has been through it, not a salesman. No jargon without the plain version straight after.

## 3. How it looks (from his videos, merged with the CarbonLedger palette)
- **Kinetic captions:** a small italic serif lead-in ("the", "to drive", "and also") over one big bold keyword, one word in the accent colour.
  Playfair Display italic plus Outfit 900, accent orange #f97316 to gold #f5b041.
- **Logo bug** top left: the CarbonLedger mark and "RUME DOMINIC".
- **Texture:** halftone dots over the background, cut-in cards that slide in, a highlighter bar under the keyword.
- **Presenter:** Rume, full body for the open and the close, a round portrait with a live voice ring in between.
- **Format:** landscape 1920x1080 by default. Cut 9:16 versions from it, not the other way round.
- CarbonLedger colours stay: deep green #0b1510, leaf green #3ddc97, cream #f4ecdc.

## 4. Channels
| Channel | Length | Open with | Close with |
|---|---|---|---|
| YouTube (landscape) | 60 to 120 s | audience call-out and flip | "Click the link below, and join the movement" |
| LinkedIn video and post | 45 to 90 s, post under 200 words | a personal line from Rume, then the flip | a question to the reader, link in first comment |
| X | 30 to 45 s, or a 4 to 6 post thread | the flip as the first post | link to the app and a receipt anyone can verify |
| Website hero | 20 to 30 s loop, muted, captions | the keyword animation only | "Try the app" |
| Pitch or demo day | 2 to 3 min | the problem by design | what is true today and what comes next, in that order |

## 5. Themes to build next (from Rume's notes)
- **Gamification:** every gram is a point, levels, daily quests, no streak that punishes a missed day, no pressure copy.
- **Smallest countries first:** the frontline is the smallest emitter's pilot target (today Kiribati). Say "pilot target", never "cleared its emissions".
- **Mobile number payments:** a later phase. Payments are a new brief under CLAUDE.md: write a decision entry first, and say nothing
  publicly about paying by phone number until it ships.

## 6. Production
- Template: media/landscape-01 (script.json, voice.py, index.html, build.sh). Copy the folder for each new film.
- **Voice:** the draft uses a British system voice. The final should be Rume's own voice, cloned in ElevenLabs from
  media/brand/voice-samples (about 110 s of him speaking), with VOICE_PROVIDER=elevenlabs.
- **Avatar:** the photo cut-out moves with the loudness of the voice. It does not lip-sync. For a talking, lip-synced Rume, use a
  service such as HeyGen, Hedra or D-ID with his consent and the cloned voice, then drop the clip in place of the portrait.
