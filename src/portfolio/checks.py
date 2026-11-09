"""Checks run on every build: no private data in tracked files, and no broken links on the site."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

TEXT_SUFFIXES = {
    ".md",
    ".yaml",
    ".yml",
    ".typ",
    ".py",
    ".html",
    ".css",
    ".js",
    ".toml",
    ".txt",
    ".csv",
    ".json",
    ".cfg",
}

# A 10-digit Indian mobile number, optionally with +91 / 91 / 0 in front and a space or dash in the
# middle. Digits next to a decimal point or other digits don't count, so results such as
# 0.6932422294 in a CSV file are not mistaken for phone numbers.
PHONE = re.compile(r"(?<![\d.])(?:\+91[\s-]?|91[\s-]|0)?[6-9]\d{4}[\s-]?\d{5}(?![\d.])")


def candidate_files(root: Path) -> list[Path]:
    """Files Git would publish: tracked files plus untracked files that aren't ignored."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout.decode()
    except (OSError, subprocess.CalledProcessError):
        # Not a Git checkout: check everything except the folders Git would ignore.
        skip = {"private", "_site", ".venv", ".git"}
        return [p for p in root.rglob("*") if p.is_file() and not skip & set(p.relative_to(root).parts)]
    return [root / name for name in out.split("\0") if name]


def find_phone_numbers(text: str) -> list[str]:
    """Return everything in text that looks like an Indian mobile number."""
    return [m.group(0) for m in PHONE.finditer(text)]


def leak_check(root: Path) -> list[str]:
    """Report files that would publish a phone number, and any file under private/ that Git tracks."""
    problems = []
    for path in candidate_files(root):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == "private":
            problems.append(f"{rel}: files in private/ must never be committed (check .gitignore)")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in find_phone_numbers(line):
                problems.append(
                    f"{rel}:{lineno}: looks like a phone number ({match}); phone numbers stay out of the repository"
                )
    return problems


LINK = re.compile(r'\b(?:href|src)="([^"]+)"')


def link_check(site: Path) -> list[str]:
    """Report links and images in the built site that point to files that don't exist."""
    problems = []
    for page in sorted(site.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            parts = urlsplit(raw)
            if parts.scheme or raw.startswith(("#", "//")):
                continue
            path = unquote(parts.path)
            target = site / path.lstrip("/") if path.startswith("/") else page.parent / path
            if target.is_dir() or path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{page.relative_to(site)}: broken link {raw}")
    return problems
