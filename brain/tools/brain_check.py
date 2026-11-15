#!/usr/bin/env python3
"""Check the company brain, and sweep the repo for things that have gone stale.

  brain_check.py            gate: skills well formed, named paths exist, run records fit the schema. Exit 1 on a problem.
  brain_check.py --sweep    sensor: overdue debt, expired ROOTS waivers, router lines that contradict DEBT.md. Prints JSON, exit 0.

Standard library only. Reads files, writes nothing.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
RUNS = ROOT / "brain" / "feedback" / "runs.jsonl"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Paths an agent is told to open. Only these roots are checked, so prose in backticks is left alone.
PATH = re.compile(r"`((?:brain|rules|docs|tests|scripts|packages|services|apps|conformance|workspaces|db|programs|"
                  r"media/brand|\.agents|\.github)/[A-Za-z0-9_./\-]+)")
OUTCOMES = {"success", "partial", "failed", "refused", "asked"}
LAYERS = {"none", "sensor", "policy", "tool", "gate", "context", "skill"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\+?\d[\d ()-]{9,}\d")


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def check_skills():
    bad = []
    if not SKILLS.is_dir():
        return [".agents/skills is missing"]
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.is_file():
            bad.append(f"{d.name}: no SKILL.md")
            continue
        meta = frontmatter(f.read_text())
        if meta is None:
            bad.append(f"{d.name}: no frontmatter")
            continue
        name, desc = meta.get("name", ""), meta.get("description", "")
        if name != d.name or not NAME.match(name) or len(name) > 64:
            bad.append(f"{d.name}: name must equal the folder, lowercase and hyphens, at most 64 chars")
        if not 20 <= len(desc) <= 1024:
            bad.append(f"{d.name}: description must be 20 to 1024 chars")
    return bad


def check_paths():
    bad = []
    files = list((ROOT / "brain").rglob("*.md")) + list(SKILLS.rglob("*.md")) + [ROOT / "AGENTS.md"]
    for f in files:
        if not f.is_file():
            continue
        for m in PATH.finditer(f.read_text()):
            p = m.group(1).rstrip(".")
            if not (ROOT / p).exists():
                bad.append(f"{f.relative_to(ROOT)}: names {p}, which does not exist")
    return bad


def check_runs():
    bad = []
    if not RUNS.is_file():
        return ["brain/feedback/runs.jsonl is missing"]
    for i, line in enumerate(RUNS.read_text().splitlines(), 1):
        if not line.strip():
            continue
        where = f"runs.jsonl line {i}"
        try:
            r = json.loads(line)
        except ValueError:
            bad.append(f"{where}: not JSON")
            continue
        try:
            dt.date.fromisoformat(r["at"])
            assert isinstance(r["agent"], str) and r["agent"]
            assert isinstance(r["skill"], str) and r["skill"]
            assert isinstance(r["task"], str) and 0 < len(r["task"]) <= 200
            assert r["outcome"] in OUTCOMES
            assert r["layer"] in LAYERS
            assert isinstance(r["finding"], str) and 0 < len(r["finding"]) <= 500
            assert len(r.get("proposal") or "") <= 500
            assert isinstance(r["gates"], list) and all(isinstance(g, str) for g in r["gates"])
            assert isinstance(r["human_needed"], bool)
            assert r["closed_by"] is None or isinstance(r["closed_by"], str)
        except (KeyError, ValueError, AssertionError, TypeError):
            bad.append(f"{where}: does not fit brain/feedback/SCHEMA.md")
            continue
        if r["skill"] != "none" and not (SKILLS / r["skill"]).is_dir():
            bad.append(f"{where}: unknown skill {r['skill']}")
        if EMAIL.search(line) or PHONE.search(line):
            bad.append(f"{where}: looks like personal data (email or phone)")
    return bad


def sweep(today):
    found = []
    paid = set()
    for row in (ROOT / "DEBT.md").read_text().splitlines():
        m = re.match(r"\|\s*(D\d+)\s*\|(.*)", row)
        if not m:
            continue
        did, rest = m.groups()
        cells = [c.strip() for c in rest.split("|")]
        if cells and cells[0].startswith("PAID"):
            paid.add(did)
            continue
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", cells[-2] if len(cells) > 1 else "")
        if dates and dt.date.fromisoformat(dates[-1]) < today:
            found.append({"kind": "debt overdue", "id": did, "review": dates[-1]})
    for row in (ROOT / "ROOTS-SCORE.md").read_text().splitlines():
        m = re.search(r"Review by (\d{4}-\d{2}-\d{2})", row)
        if m and dt.date.fromisoformat(m.group(1)) < today:
            check = row.split("|")[1].strip()
            found.append({"kind": "waiver expired", "id": f"ROOTS {check}", "review": m.group(1)})
    router = (ROOT / "CLAUDE.md").read_text()
    section = router.split("## Not yet true", 1)[-1].split("\n## ", 1)[0]
    for did in sorted(set(re.findall(r"\bD\d+\b", section)) & paid):
        found.append({"kind": "router contradicts DEBT", "id": did, "detail": "CLAUDE.md says not yet true; DEBT.md says PAID"})
    if RUNS.is_file():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("closed_by") is None and r.get("outcome") != "success":
                    found.append({"kind": "open run record", "id": r["task"][:80], "layer": r["layer"], "since": r["at"]})
    return found


def main(argv):
    if "--sweep" in argv:
        print(json.dumps(sweep(dt.date.today()), indent=1))
        return 0
    bad = check_skills() + check_paths() + check_runs()
    for b in bad:
        print("FAIL", b)
    print("brain: PASS" if not bad else f"brain: {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
