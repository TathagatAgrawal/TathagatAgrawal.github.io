"""Compile the resumes defined in content/config.yaml with the Typst compiler bundled in the typst package.

A PDF records when it was made, so two builds of the same resume differ in a few bytes. To keep the PDFs
that are committed to Git (and copied to iCloud) from changing on every build, a resume is rebuilt with the
date already inside the existing PDF: if the result is identical the existing file is kept, and the date
only moves forward when the content really changed.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import typst

from .content import Content, ContentError
from .resume_data import resume_model

ENTRY = "resume/resume.typ"
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


def compile_resume(content: Content, name: str, *, timestamp: int | None = None) -> bytes:
    """Compile the resume called name in content/config.yaml to PDF bytes, stamped with timestamp (today).

    The resume's data is built in Python and handed to resume/resume.typ as a Typst input. System fonts
    are ignored so that the PDF is identical on every machine, including GitHub's.
    Raises RuntimeError with the reason if the resume can't be built.
    """
    if name not in content.site.resumes:
        raise RuntimeError(f"no resume called {name!r}; the resumes are {', '.join(content.site.resumes)}")
    try:
        model = resume_model(content, name)
        return typst.compile(
            str(content.root / ENTRY),
            root=str(content.root),
            ignore_system_fonts=True,
            sys_inputs={"resume": name, "data": json.dumps(model, ensure_ascii=False)},
            timestamp=timestamp if timestamp is not None else today_timestamp(),
        )
    except (ContentError, typst.TypstError) as exc:
        raise RuntimeError(f"resume {name}: {exc}") from exc


def build_pdf(content: Content, name: str, previous: bytes | None) -> tuple[bytes, bool]:
    """Build a resume, reusing the previous PDF if nothing but the date would differ.

    Returns the PDF and whether it differs from previous (always True when there is no previous PDF).
    """
    stamp = embedded_timestamp(previous) if previous else None
    if previous and stamp is not None:
        data = compile_resume(content, name, timestamp=stamp)
        if data == previous:
            return previous, False
    return compile_resume(content, name), True


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
