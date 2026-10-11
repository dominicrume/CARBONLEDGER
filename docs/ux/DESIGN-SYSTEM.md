# Design System

Rewritten 2026-10-11 after the partner call: the product is a game you play with the planet, and the first screens
were dry. Direction from the UI/UX Pro Max query (organic, biophilic, dark-first) and the taste-skill discipline
rules (one accent, one shape system, no AI tells, motion only where it means something, both themes, reduced motion).

## Read of the brief
A gamified consumer climate app with seven tabs, for people who want to act and feel the difference, and for judges.
Dials: variance 7, motion 6, density 5. No build step and a strict CSP, so the system is native CSS tokens, not a
framework. The partner's information architecture (tabs, flows, wording rules) is kept.

## Tokens (apps/web/css/app.css)
| Token | Dark | Light | Use |
|---|---|---|---|
| --bg, --bg-2 | #0d1712, #12201a | #f3f6f2, #e8eee7 | page ground, inset ground |
| --surface, --surface-2 | #152419, #1b2e24 | #ffffff, #f8faf7 | panels, tiles |
| --fg, --fg-2, --fg-3 | #f1f5f0 at 100, 78, 66% | #0e1a13 at 100, 74, 62% | text; fg-3 keeps 4.5 to 1 |
| --primary | #3ddc97 | #0b6e4b | the one accent: actions, progress, the Frontline |
| --gold | #f5c451 | #8a5a00 | rewards only: XP, level ring, badges |
| --ok, --warn, --bad | green, amber, red | | queue status on the globe and the queue, nothing else |

Shape lock: cards 16px, controls 12px, buttons and chips pill. Type: Outfit for everything (800 for display, 600
for labels, 400 body), DM Mono for every number. Icons: Phosphor regular, vendored as one sprite in
apps/web/vendor/icons.svg, always `aria-hidden` beside visible text. No emoji. No hand-drawn icons.

## The game loop on screen
1. **Header**: the level ring (gold, progress to the next level) and the connection state. Tapping the ring opens Me.
2. **Mission strip** on Shop, Travel and Daily: the Frontline country, how far it is, how many players are on it.
   Tapping it opens the World tab on that country.
3. **Retire button** shows the XP it is worth. One gram retired is one point, so the score and the receipt agree.
4. **Reward moment** after a retirement, above the receipt: XP gained, level bar from before to after, a level-up
   banner, new badges popping in, the country line, confetti for a level-up or a badge. Haptic tick on phones.
5. **Me, the command centre**: level ring, retired total with the simulated tag, weekly streak, badge count, the
   three nearest quests from the skill tree, a badge shelf, the tree, the league, partner quests, history.
6. **World, the clock**: countries cleared of 193, the symbolic stock cleared, players and receipts on the ledger
   (from GET /v1/stats/world, so the line moves as other people play), the globe, the Frontline card, the queue
   with positions. Finishing a country opens a celebration sheet.
7. **Business**: the same loop in its own league, plus the mandate screen.

## Claims discipline, unchanged
"Retire pilot units", never offset. The simulated tag beside every unit count. The ledger's name on screen comes
from what the server reports (dry-run or a Solana cluster), never from a config string. The game is labelled
symbolic. tests/test_web_wording.py and the browser suite fail if a banned word returns.

## Motion
180 to 420 ms, transform and opacity only. Progress bars ease to their new width; the reward number and badges pop
once; confetti falls once. Everything stops under prefers-reduced-motion, including the globe.

## Checks before any public demo
Contrast at least 4.5 to 1 (axe at WCAG 2.1 AA runs on every tab, the shelf, the confirm sheet and the receipt in
the browser suite). Every action reachable by keyboard; the badge shelf is a focusable region. Both themes.
Screens at 375, 430, 768 and 1200 wide.
