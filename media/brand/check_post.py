#!/usr/bin/env python3
"""Selling-rules guardrail (SELLING-RULES.md). Usage: check_post.py caption.txt [image.html ...]
Exit 1 on any FAIL. Standard library only."""
import re, sys

HOOK_WORDS, LINE_WORDS, MAX_GRADE, MAX_LIST = 12, 20, 8.0, 5
HYPE = ["revolutionary", "game-changer", "game changer", "guaranteed", "100% safe", "risk-free", "risk free", "unlock your",
        "skyrocket", "synergy", "leverage", "cutting-edge", "cutting edge", "world-class", "best-in-class", "act now", "limited time"]
PALETTE = {"8fd3ff", "3fa9f5", "ffffff", "fff", "071a2e", "d9d2ff", "000", "000000"}   # sky, deep sky, white, ink, diamond edge
PILOT = "pilot units, not yet verified credits"

def syllables(w):
    w = w.lower().strip(".,!?:;\"'()")
    if len(w) <= 3: return 1
    w = re.sub(r"(?:es|ed|e)$", "", w)
    return max(1, len(re.findall(r"[aeiouy]+", w)))

def grade(text):
    words = re.findall(r"[A-Za-z][A-Za-z'’-]*", text)
    sents = max(1, len(re.findall(r"[.!?]+(?:\s|$)", text)) or text.count("\n") or 1)
    if not words: return 0.0
    return 0.39 * len(words) / sents + 11.8 * sum(map(syllables, words)) / len(words) - 15.59

def check_caption(text):
    fails, warns = [], []
    lines = [l.strip() for l in text.strip().splitlines()]
    body = [l for l in lines if l]
    if not body: return ["empty caption"], warns
    hook = len(body[0].split())
    if hook > HOOK_WORDS: fails.append(f"hook is {hook} words (max {HOOK_WORDS}): {body[0]!r}")
    for l in body:
        n = len(l.split())
        if n > LINE_WORDS: fails.append(f"line is {n} words (max {LINE_WORDS}): {l[:60]!r}…")
    if re.search(r"https?://|www\.", text): fails.append("link in the body: put it in the first comment")
    if re.search(r"https?://|www\.|\.com\b", body[-1]): fails.append("ends on a link: end on a punchline or a question")
    g = grade(text)
    if g > MAX_GRADE: fails.append(f"reading grade {g:.1f} (max {MAX_GRADE}): use shorter words and sentences")
    items = [l for l in body if re.match(r"^\d+[).]\s", l)]
    if len(items) > MAX_LIST: fails.append(f"list has {len(items)} items (max {MAX_LIST})")
    low = text.lower()
    for h in HYPE:
        if h in low: fails.append(f"hype word: {h!r}")
    if re.search(r"\b(carbon )?(units?|credits?|offsets?)\b", low) and PILOT not in low:
        fails.append(f"mentions units/credits without the label {PILOT!r}")
    if not re.search(r"\d", text): warns.append("no real number: add one from Rume's own work (a person checks it is real)")
    return fails, warns

def check_image(html):
    fails = []
    cols = {c.lower() for c in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", html)}
    off = sorted(cols - PALETTE)
    if off: fails.append("off-palette colours: " + ", ".join("#" + c for c in off))
    for m in re.finditer(r'class="post"[^>]*id="([^"]+)"(.*?)(?=class="post"|<script)', html, re.S):
        words = len(re.sub(r"<[^>]+>", " ", re.sub(r"<(style|svg)[\s\S]*?</\1>", " ", m.group(2))).split())
        if words > 20: fails.append(f"{m.group(1)}: {words} words on the image (max 20)")
    return fails

def main(argv):
    if len(argv) < 2: print(__doc__); return 2
    fails, warns = check_caption(open(argv[1], encoding="utf-8").read())
    for p in argv[2:]: fails += [f"{p}: {f}" for f in check_image(open(p, encoding="utf-8").read())]
    for w in warns: print("WARN ", w)
    for f in fails: print("FAIL ", f)
    print("PASS" if not fails else f"{len(fails)} rule(s) broken"); return 1 if fails else 0

if __name__ == "__main__": sys.exit(main(sys.argv))
