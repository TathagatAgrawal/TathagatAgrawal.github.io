"""Convert the Markdown used in content files into Typst markup, so the resumes can share the website's text.

Only inline Markdown is supported, because that is what a bullet, a summary or a note is: `**bold**`,
`*italic*`, `` `code` ``, `[links](https://...)`, and backslash escapes. Anything else (images, raw HTML)
is an error rather than something that would silently come out wrong on a resume.
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

# No typographer here: Typst makes its own dashes, ellipses and curly quotes from -- and ... and ".
_PARSER = MarkdownIt("commonmark")

# Characters that mean something in Typst markup. Each is escaped with a backslash.
_SPECIAL = str.maketrans({c: "\\" + c for c in "\\#$*_`@<>[]~/"})
_MARKER = re.compile(r"^[-+=](?=\s)")
_NUMBER = re.compile(r"^(\d+)\.(?=\s)")


def _escape(text: str) -> str:
    """Escape the characters in plain text that Typst would otherwise treat as markup.

    A non-breaking space (written `&nbsp;` in Markdown) becomes Typst's `~`, which keeps the words on either
    side of it on one line.
    """
    return text.translate(_SPECIAL).replace("\u00a0", "~")


def _string(text: str) -> str:
    """Write text as a Typst string literal, for a link's address."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_typst(markdown: str) -> str:
    """Convert one line of inline Markdown into Typst markup.

    Raises ValueError for Markdown that has no equivalent here (an image, raw HTML).
    """
    tokens = _PARSER.parseInline(markdown)
    children = tokens[0].children or []
    out: list[str] = []
    after_link = False
    for token in children:
        out.append(_render(token, after_link))
        after_link = token.type == "link_close"
    result = "".join(out)
    # A bullet that starts like a list item or a numbered item would become one in Typst.
    if _MARKER.match(result):
        result = "\\" + result
    elif number := _NUMBER.match(result):
        result = number.group(1) + "\\." + result[number.end() :]
    return result


def _render(token: Token, after_link: bool) -> str:
    """Render one inline token; after_link guards the text right after a link from being read as a call."""
    kind = token.type
    if kind in {"text", "text_special"}:
        text = _escape(token.content)
        if after_link and text[:1] in {"(", "."}:
            # Typst reads `#link(..)[..](more)` and `#link(..)[..].more` as a call and a field access.
            text = "\\" + text
        return text
    if kind == "softbreak":
        return " "
    if kind == "hardbreak":
        return "\\ "
    if kind in {"strong_open", "strong_close"}:
        return "*"
    if kind in {"em_open", "em_close"}:
        return "_"
    if kind == "code_inline":
        return f"`{token.content}`"
    if kind == "link_open":
        return f"#link({_string(token.attrGet('href') or '')})["
    if kind == "link_close":
        return "]"
    raise ValueError(f"{kind} is not supported in resume text: {token.content!r}")
