"""The repository's own structure is tested, so the rules cannot quietly rot (ROOTS checks 1, 2, 3, 5, 6)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = sorted(p for p in (ROOT / "workspaces").iterdir() if p.is_dir())
SECTIONS = ["## Input", "## Process", "## Output", "## Completion", "## Do not"]


def test_every_workspace_has_a_router_with_a_not_to_load_table():
    assert len(WORKSPACES) == 7
    for w in WORKSPACES:
        text = (w / "CLAUDE.md").read_text()
        assert "## What NOT to load" in text, w.name


def test_every_stage_has_a_full_contract():
    stages = [s for w in WORKSPACES for s in (w / "stages").iterdir() if s.is_dir()]
    assert len(stages) >= 20
    for s in stages:
        text = (s / "CONTEXT.md").read_text()
        for sec in SECTIONS:
            assert sec in text, f"{s.relative_to(ROOT)} lacks {sec}"
        assert len(text.splitlines()) < 400


def test_root_router_lists_exactly_the_workspaces_that_exist():
    router = (ROOT / "CLAUDE.md").read_text()
    listed = set(re.findall(r"workspaces/(\w+)", router))
    assert listed == {w.name for w in WORKSPACES}


def test_the_rule_files_the_router_names_all_exist():
    router = (ROOT / "CLAUDE.md").read_text()
    for path in re.findall(r"^\d\. ((?:rules|docs)/[\w/.\-]+\.md)", router, re.M):
        assert (ROOT / path).exists(), path


def test_required_top_level_files_exist():
    for f in ["START-HERE.txt", "CLAUDE.md", "CONTEXT.md", "ARCHITECTURE.md", "BREAK.md", "DEBT.md", "ROOTS-SCORE.md", "CHANGELOG.md",
              ".env.example", ".gitignore", "Anchor.toml", "pyproject.toml", ".github/workflows/ci.yml", "db/migrations/0001_registry.sql",
              "programs/carbon_registry/src/lib.rs", "conformance/registry_vectors.json", "conformance/mandate_vectors.json", "conformance/estimate_vectors.json"]:
        assert (ROOT / f).exists(), f


def test_no_python_module_is_over_400_lines():
    for p in list((ROOT / "packages").rglob("*.py")) + list((ROOT / "services").rglob("*.py")):
        assert len(p.read_text().splitlines()) <= 400, p


def test_env_example_holds_placeholders_only():
    for line in (ROOT / ".env.example").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            if any(k in key for k in ("KEY", "SECRET", "TOKEN", "PASSWORD")):
                assert val.startswith("<") and val.endswith(">"), key


def test_our_documents_have_no_em_or_en_dashes():
    """House style: nothing may read as machine-written. Imported app files are excluded."""
    skip = {"apps", "node_modules", ".git"}
    for p in ROOT.rglob("*"):
        if p.suffix in {".md", ".txt"} and p.is_file() and not (set(p.relative_to(ROOT).parts) & skip):
            t = p.read_text()
            assert "\u2014" not in t and "\u2013" not in t, p.relative_to(ROOT)
