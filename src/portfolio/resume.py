"""Compile the resumes defined in content/config.yaml with the Typst compiler bundled in the typst package."""

from __future__ import annotations

import json

import typst

from .content import Content, ContentError
from .resume_data import resume_model

ENTRY = "resume/resume.typ"


def compile_resume(content: Content, name: str) -> bytes:
    """Compile the resume called name in content/config.yaml to PDF bytes.

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
        )
    except (ContentError, typst.TypstError) as exc:
        raise RuntimeError(f"resume {name}: {exc}") from exc
