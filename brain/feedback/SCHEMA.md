# Run records

Every agent appends one JSON object per line to `brain/feedback/runs.jsonl` at the end of a task. Humans may add
records too. `brain/tools/brain_check.py` rejects a record that breaks this schema, so the gate fails.

| Field | Type | Meaning |
|---|---|---|
| `at` | `YYYY-MM-DD` | Day of the run |
| `agent` | string | Who ran it: `claude-code`, `codex`, `gemini`, `human:rume`, a cron name |
| `skill` | string | The skill used, from `.agents/skills/`, or `none` |
| `task` | string, at most 200 chars | What was asked, in one line |
| `outcome` | one of `success`, `partial`, `failed`, `refused`, `asked` | What happened |
| `layer` | one of `none`, `sensor`, `policy`, `tool`, `gate`, `context`, `skill` | Which layer was missing or wrong. `none` on a clean success |
| `finding` | string, at most 500 chars | What worked or broke, specific enough to act on |
| `proposal` | string, at most 500 chars, optional | The change that would make the next run succeed |
| `gates` | list of strings | The gate commands run and their result, e.g. `scripts/check.sh: pass` |
| `human_needed` | bool | True when the next step is in the ASK tier |
| `closed_by` | string or null | The commit, pull request or decision that answered it |

Privacy: ids, codes, counts and file paths only. No names of customers, no emails, no phone numbers, no message
text. The checker refuses records containing an email address or a phone number.

Example:
```json
{"at": "2026-11-09", "agent": "claude-code", "skill": "retire-units", "task": "Explain why a retirement was refused", "outcome": "success", "layer": "none", "finding": "Refusal code BELOW_COMPUTED: the client total was lower than the server's recompute.", "gates": [], "human_needed": false, "closed_by": null}
```
