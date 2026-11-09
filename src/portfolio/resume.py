"""Compile the Typst resumes in resume/ with the Typst compiler bundled in the typst package."""

from __future__ import annotations

from pathlib import Path

import typst


def resume_files(root: Path) -> dict[str, Path]:
    """Every resume in resume/ by name (general, ml, ...); lib.typ is the shared layout, not a resume."""
    return {p.stem: p for p in sorted((root / "resume").glob("*.typ")) if p.name != "lib.typ"}


def compile_resume(root: Path, path: Path) -> bytes:
    """Compile one resume to PDF bytes.

    System fonts are ignored so that the PDF is identical on every machine, including GitHub's.
    Raises RuntimeError with Typst's message if compilation fails.
    """
    try:
        return typst.compile(str(path), root=str(root), ignore_system_fonts=True)
    except Exception as exc:  # typst raises its own error types; report them uniformly
        raise RuntimeError(f"{path.relative_to(root)}: {exc}") from exc
