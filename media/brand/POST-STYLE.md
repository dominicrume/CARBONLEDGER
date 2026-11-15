# LinkedIn image posts: what we learned from Alex Hormozi, done in Rume's colours

Source, 28 Oct 2026: 21 public Alex Hormozi LinkedIn posts. Seven of them carry an image; all 21 captions were read.
His "images" activity page needs a login, so this is a sample, not every post he has made. We take the patterns. We do not
copy his words, his likeness, or a verified tick Rume does not have.

## The seven image types he uses
| Type | What it looks like | Rume template |
|---|---|---|
| Reminder card | White, avatar and name top left, two short lines in a plain sans, a lot of empty space | `posts.html` P1 |
| Object poster | One flat saturated colour, one glossy 3D object that stands for the idea (a magnet for "leads"), a small outlined pill label, almost no text | P2 (a glass diamond) |
| Thumbnail | 2 or 3 words in heavy caps, one word in a second colour, an arrow, his face with an expression, one prop | P3 |
| Cut-out on pattern | Him cut out, branded shirt, on a busy black-and-white doodle background | later |
| Proof photo | Candid stage shot: him teaching a full room | needs real photos of Rume speaking |
| Moody portrait | Cinematic, low light, one colour cast | needs a shoot |
| AI portrait | Stylised, and the caption says it is AI-generated | allowed only with that label |

## How the captions are written
- **One-line hook,** then short lines with a blank line between them.
- **Numbered lists** written as 1) 2) 3), usually three items.
- **A swap:** "X. Should be changed to: Y." or "X OR Y".
- **A real number from his own life:** "250 pieces a week", "18-36 months of saying no".
- **A punchline last line.** No link in the post itself.
- **The picture carries one idea and the caption carries the lesson.** The picture never repeats the whole caption.

## Rules in Rume's version
- **Colours:** light blue, transparent diamond (glass) and white, on deep ink #071A2E or on white for readability. See BRAND-VOICE.md §3.
- **Size:** 1080x1350 (LinkedIn's portrait feed size).
- **Text:** one idea, at most about 20 words on the image, and every claim backed.
- **No fake signals:** no verified tick, no invented handle.

Templates are in `posts/posts.html`. Rendered samples go to `posts/out/`, which is git-excluded because it contains his photo.

## Re-check, 14 Nov 2026
Method (the same as on 28 Oct): search for `site:linkedin.com/posts/alexhormozi`, then read each public post page and its
`og:image`. The profile's Images tab needs a login and is not read. Four more public posts (Apr 2023 to Mar 2024) showed a
second form of text card that the table above lacked.

| Type | What it looks like | Rume template |
|---|---|---|
| Dark text card | Square 1080x1080, black, avatar with name and handle top left, plain white sans, two short paragraphs or a list 1) to 5), then a closing line | `posts/textcards.html` #d (deep ink, key word in light blue) |
| White reminder card, square | Square 1080x1080 version of the reminder card: "Friendly reminder:" then one line | `posts/textcards.html` #w |

What this changes: text cards are square, not 1080x1350. They carry no graphics at all, only plain sentences. The sample
found by search is older than the Images tab, so ask Rume for screenshots of that tab to check the newest posts.

## His Images tab, read from Rume's screenshots (14 Nov 2026, about 50 posts)
This is the full current picture, and it replaces the guesses above where they differ.

| Share | Type | What it looks like | Rume template |
|---|---|---|---|
| About 7 in 10 | Text card | Square. White. Black-and-white avatar, bold name, grey handle top left. Plain regular sans (not bold) in black, left aligned, no colour at all. The fewer the words, the bigger the type: 6 words fill the card, 80 words are small. | `posts/hormozi-set.html` p1 (white), p2 (ink), p3 (list) |
| About 2 in 10 | Candid photo, no text | Teaching at a whiteboard, on stage, a seated portrait, writing, with his wife | needs real photos of Rume |
| Rare | Bold poster | Flat colour (yellow or pale grey), heavy centred caps, a small drawn head on top | `posts/hormozi-set.html` p4 (light blue, Rume's head in a ring) |
| Rare | Held sign | A cardboard sign in marker caps, held in his hands | needs a real photo of Rume holding a sign; never fake it |

How he writes the cards:
- **One thought, then a blank line, then the turn:** "Losers become losers by never being willing to lose. / Everyone loses before they win."
- **A quoted excuse, then the answer:** "I work a 9 to 5..." / "You get 104 days off a year. They're called weekends. Use them."
- **A ladder:** "Beginners ask what. Intermediates ask how. Experts ask who. Masters ask why."
- **A contrast pair:** "Aggressive with effort. Relaxed with outcome."
- **A numbered list, 1) to 6), with a closing line.**
- **No hashtags or links on the image.**

Rume's version: the same structure and plain type, our message and voice, ink #071A2E instead of black, an ink card for
contrast, the poster in light blue. No verified tick and no invented handle (we show rumedominic.com). Text stays at 20 words
or fewer to pass `check_post.py`, which is stricter than he is.
