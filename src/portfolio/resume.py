"""Compile the resumes defined in content/config.yaml with the Typst compiler bundled in the typst package.

Resumes are built on your own computer, with the fonts installed on it (and any in resume/fonts/), and the
PDFs are committed to Git. GitHub does not rebuild them: it only checks that each one still builds with the
fonts bundled with the build ("portable" mode, which ignores system fonts and the resume's `font` setting),
and publishes the committed PDF.

A PDF records when it was made, so two builds of the same resume differ in a few bytes. To keep the PDFs
that are committed to Git (and copied to iCloud) from changing on every build, a resume is rebuilt with the
date already inside the existing PDF: if the result is identical the existing file is kept, and the date
only moves forward when the content really changed.
"""

from __future__ import annotations

import datetime as dt
import difflib
import json
import re
from pathlib import Path

import typst

from .content import Content, ContentError
from .resume_data import resume_model

ENTRY = "resume/resume.typ"
FONT_DIR = "resume/fonts"
_CREATED = re.compile(rb"CreationDate\s*\(D:(\d{14})Z\)")


def today_timestamp() -> int:
    """Midnight UTC today as a Unix timestamp: the date a changed resume is stamped with."""
    return int(dt.datetime.combine(dt.datetime.now(dt.UTC).date(), dt.time(), tzinfo=dt.UTC).timestamp())


def embedded_timestamp(pdf: bytes) -> int | None:
    """The creation date inside a PDF made by this module, as a Unix timestamp, or None if it has none."""
    match = _CREATED.search(pdf)
    if not match:
        return None
    return int(dt.datetime.strptime(match.group(1).decode(), "%Y%m%d%H%M%S").replace(tzinfo=dt.UTC).timestamp())


def font_paths(root: Path) -> list[str]:
    """The folder of extra font files (resume/fonts/) if there is one, to be searched along with the bundled fonts."""
    folder = root / FONT_DIR
    return [str(folder)] if folder.is_dir() else []


def available_fonts(root: Path, *, system: bool = True) -> list[str]:
    """The font families a resume can use: the fonts bundled with the build, those in resume/fonts/, and, unless
    system is False, those installed on this computer."""
    fonts = typst.Fonts(include_system_fonts=system, include_embedded_fonts=True, font_paths=font_paths(root))
    return sorted(set(fonts.families()))


def _unknown_font_message(name: str, missing: list[str], available: list[str]) -> str:
    """Explain which font names aren't available, suggesting the closest one that is."""
    lowered = {f.lower(): f for f in available}
    parts = []
    for font in missing:
        close = difflib.get_close_matches(font.lower(), list(lowered), n=1, cutoff=0.6)
        parts.append(f"{font!r}" + (f" (did you mean {lowered[close[0]]!r}?)" if close else ""))
    return (
        f"content/config.yaml: resumes.{name}.layout.font: {', '.join(parts)} is not available on this computer. "
        f"`uv run resume --list-fonts` lists what is; fonts installed here work, and so do font files in {FONT_DIR}/"
    )


def compile_resume(content: Content, name: str, *, timestamp: int | None = None, portable: bool = False) -> bytes:
    """Compile the resume called name in content/config.yaml to PDF bytes, stamped with timestamp (today).

    The resume's data is built in Python and handed to resume/resume.typ as a Typst input. The fonts installed
    on this computer are available, so a resume can use any of them. With portable=True only the bundled fonts
    are used and the resume's own `font` setting is ignored, so it builds on any machine (GitHub's, the tests);
    that PDF is only good for checking that the resume builds, not for publishing.
    Raises RuntimeError with the reason if the resume can't be built.
    """
    if name not in content.site.resumes:
        raise RuntimeError(f"no resume called {name!r}; the resumes are {', '.join(content.site.resumes)}")
    try:
        model = resume_model(content, name)
        layout = model["layout"]
        assert isinstance(layout, dict)
        if portable:
            layout.pop("font", None)
        else:
            families = available_fonts(content.root)
            available = {f.lower() for f in families}
            missing = [f for f in layout.get("font", []) if f.lower() not in available]
            if missing:
                raise ContentError(_unknown_font_message(name, missing, families))
        return typst.compile(
            str(content.root / ENTRY),
            root=str(content.root),
            font_paths=font_paths(content.root),
            ignore_system_fonts=portable,
            sys_inputs={"resume": name, "data": json.dumps(model, ensure_ascii=False)},
            timestamp=timestamp if timestamp is not None else today_timestamp(),
        )
    except (ContentError, typst.TypstError) as exc:
        raise RuntimeError(f"resume {name}: {exc}") from exc


def build_pdf(content: Content, name: str, previous: bytes | None, *, portable: bool = False) -> tuple[bytes, bool]:
    """Build a resume, reusing the previous PDF if nothing but the date would differ.

    Returns the PDF and whether it differs from previous (always True when there is no previous PDF).
    """
    stamp = embedded_timestamp(previous) if previous else None
    if previous and stamp is not None:
        data = compile_resume(content, name, timestamp=stamp, portable=portable)
        if data == previous:
            return previous, False
    return compile_resume(content, name, portable=portable), True


def file_name(content: Content, name: str) -> str:
    """The name, without .pdf, a resume's copy gets outside the repository (for example in iCloud Drive).

    It is `filename` in the resume's entry in content/config.yaml, else "<Your name> - Resume (<resume>)".
    """
    return content.site.resumes[name].filename or f"{content.profile.name} - Resume ({name})"


def write_if_changed(path: Path, data: bytes) -> bool:
    """Write data to path unless the file already holds exactly that; return True if it was written."""
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True
