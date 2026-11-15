# Selling rules: the hard guardrail (from 28 Oct 2026)

Rume's rule: **we only sell with these principles, and with simplicity.** Every post, caption, image, video script, landing
page line and sales message follows this page. Nothing ships until `check_post.py` passes.
The patterns come from [POST-STYLE.md](POST-STYLE.md); the voice from [BRAND-VOICE.md](BRAND-VOICE.md).

## The ten rules
1. **One idea.** Each post, image or scene sells one thing. A second idea is a second post.
2. **The hook stands alone.** The first line is at most 12 words and makes sense on its own.
3. **Short lines.** At most 20 words per line, with a blank line between thoughts.
4. **Plain words.** A 12-year-old can read it: reading grade 8 or lower. Any technical word gets the plain version straight after.
5. **Real proof.** Use at least one real number from Rume's own work. Never an invented number, a borrowed result or a guess.
6. **Lists of three.** Number them 1) 2) 3), with five items at most.
7. **Show the swap.** Name what people believe and what is true: "X. Should be: Y." or "It isn't X, it is Y."
8. **End on a punch or a question.** Never end on a link: the link goes in the first comment.
9. **Simple image.** Use one of the templates, at most 20 words on the picture, and only the brand colours (light blue,
   transparent diamond, white, with deep ink for readability).
10. **Honesty beats simplicity.**
    - Pilot units are always called "pilot units, not yet verified credits".
    - No verified tick, invented handle or fake urgency.
    - An AI image or a third party's cloned voice is labelled. Rume's own cloned voice is never labelled on screen (his rule, 14 Nov 2026).
    - If the simple version would be untrue, use the true one.

## How it is enforced
`python3 media/brand/check_post.py caption.txt [image.html ...]`
- **Fails** on a long hook, a long line, a link in the body, a reading grade over 8, more than five list items, an off-palette
  colour in an image, a hype word, or units or credits without the pilot label.
- **Warns** when there is no number. A person then checks that the number is real, because software cannot.
