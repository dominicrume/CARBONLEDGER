#!/usr/bin/env python3
"""Small secret scanner for CI (ENGINEERING rule 8). Exit 1 if a likely secret is found.
It skips .env.example, caches and binary files."""
import pathlib
import re
import sys

PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "cloud access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "quoted long secret": re.compile(
        r"""(?i)(api[_-]?key|secret|token|passwd|password)\s*[=:]\s*['"][A-Za-z0-9/+_\-]{20,}['"]"""
    ),
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}
SKIP_FILES = {".env.example"}


def scan(root: str):
    hits = []
    for p in pathlib.Path(root).rglob("*"):
        if not p.is_file() or p.name in SKIP_FILES or any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in PATTERNS.items():
            if rx.search(text):
                hits.append((str(p), label))
    return hits


if __name__ == "__main__":
    found = scan(sys.argv[1] if len(sys.argv) > 1 else ".")
    for path, label in found:
        print(f"SECRET? {label}: {path}")
    print("scan clean" if not found else f"{len(found)} finding(s)")
    sys.exit(1 if found else 0)
