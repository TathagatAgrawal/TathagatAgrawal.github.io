"""Render Markdown for the website, with numbered figures and tables built from CSV files.

Extensions to plain Markdown:

- An image alone in a paragraph, ``![alt text](figures/plot.png "Caption")``, becomes a numbered
  figure with a caption. Wide images extend beyond the text column; a sibling file named
  ``plot.dark.png`` is shown instead in dark mode.
- A fenced block with the info string ``table`` renders a CSV file as a numbered table. Its body is
  YAML: ``file`` (required), ``caption``, ``columns`` (CSV column: header, in display order),
  ``format`` (CSV column: Python format string) and ``labels`` (raw value: display value).
"""

from __future__ import annotations

import csv
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from PIL import Image

WIDE_MIN_PIXELS = 1000
WIDE_MIN_SVG_ASPECT = 1.6
LARGE_IMAGE_BYTES = 500_000


@dataclass
class RenderEnv:
    """Per-document state shared by the render rules: where files live, counters and problems found."""

    source: Path
    base_dir: Path
    allow_h1: bool = False
    figures: int = 0
    tables: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def where(self, token: Token | None) -> str:
        """Return "file:line" for a token, or just the file when the line is unknown."""
        if token is not None and token.map:
            return f"{self.source}:{token.map[0] + 1}"
        return str(self.source)


def _image_size(path: Path) -> tuple[float, float] | None:
    """Return an image's width and height (pixels, or SVG user units), or None if unreadable."""
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="replace")[:4000]
        box = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', text)
        if box:
            return float(box.group(1)), float(box.group(2))
        w = re.search(r'\bwidth="([\d.]+)', text)
        h = re.search(r'\bheight="([\d.]+)', text)
        return (float(w.group(1)), float(h.group(1))) if w and h else None
    try:
        with Image.open(path) as img:
            return img.size
    except OSError:
        return None


def _figure_html(token: Token, env: RenderEnv, where_token: Token) -> str:
    """Build the <figure> for an image that stands alone in its paragraph."""
    src = token.attrs.get("src", "")
    alt = token.content.strip()
    caption = token.attrs.get("title") or ""
    where = env.where(where_token)
    path = (env.base_dir / str(src)).resolve()
    if re.match(r"^[a-z]+://", str(src)):
        env.errors.append(f"{where}: figure {src}: use a file in the project folder, not a web address")
        return ""
    if not path.exists():
        env.errors.append(f"{where}: figure {src} not found (looked in {env.base_dir})")
        return ""
    if not alt:
        env.errors.append(f"{where}: figure {src} needs alt text describing what it shows: ![alt text]({src})")
    if path.stat().st_size > LARGE_IMAGE_BYTES:
        env.warnings.append(f"{where}: figure {src} is {path.stat().st_size // 1000} KB; consider compressing it")

    size = _image_size(path)
    wide = False
    dims = ""
    if size:
        w, h = size
        if path.suffix.lower() == ".svg":
            wide = h > 0 and w / h >= WIDE_MIN_SVG_ASPECT
        else:
            wide = w >= WIDE_MIN_PIXELS
            dims = f' width="{int(w)}" height="{int(h)}"'

    dark = path.with_name(f"{path.stem}.dark{path.suffix}")
    s = html.escape(str(src))
    a = html.escape(alt)
    if dark.exists():
        dark_src = html.escape(str(Path(str(src)).with_name(dark.name)))
        img = (
            f'<img class="light-only" src="{s}"{dims} alt="{a}" loading="lazy">'
            f'<img class="dark-only" src="{dark_src}"{dims} alt="{a}" loading="lazy">'
        )
    else:
        img = f'<img src="{s}"{dims} alt="{a}" loading="lazy">'

    env.figures += 1
    cap = f"<figcaption>Figure {env.figures}. {html.escape(caption)}</figcaption>" if caption else ""
    cls = ' class="wide"' if wide else ""
    return f'<figure{cls}>\n  <a href="{s}">{img}</a>\n  {cap}\n</figure>\n'


def _figures_rule(state: StateCore) -> None:
    """Core rule: turn paragraphs that contain only an image into <figure> blocks."""
    env: RenderEnv = state.env["render"]
    tokens = state.tokens
    out: list[Token] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if (
            t.type == "paragraph_open"
            and i + 2 < len(tokens)
            and tokens[i + 1].type == "inline"
            and tokens[i + 2].type == "paragraph_close"
        ):
            kids = [k for k in tokens[i + 1].children or [] if not (k.type == "text" and not k.content.strip())]
            if len(kids) == 1 and kids[0].type == "image":
                block = Token("html_block", "", 0)
                block.content = _figure_html(kids[0], env, t)
                block.map = t.map
                out.append(block)
                i += 3
                continue
        if t.type == "inline":
            for kid in t.children or []:
                if kid.type == "image":
                    src = str(kid.attrs.get("src", ""))
                    if not re.match(r"^[a-z]+://", src) and not (env.base_dir / src).exists():
                        env.errors.append(f"{env.where(t)}: image {src} not found")
        if t.type == "heading_open" and t.tag == "h1" and not env.allow_h1:
            env.errors.append(f"{env.where(t)}: use ## for headings; the page title comes from the YAML file")
        out.append(t)
        i += 1
    state.tokens = out


def _format_cell(value: str, fmt: str | None, labels: dict[str, str]) -> str:
    """Apply a label replacement or a Python format string to one CSV value."""
    if value in labels:
        return labels[value]
    if fmt:
        try:
            return fmt.format(float(value))
        except ValueError:
            return value
    return value


def _is_number(value: str) -> bool:
    """True when a CSV value parses as a number."""
    try:
        float(value)
    except ValueError:
        return False
    return True


def _csv_table_html(token: Token, env: RenderEnv) -> str:
    """Render a ```table fenced block (YAML options) as a numbered table from a CSV file."""
    where = env.where(token)
    try:
        spec = yaml.safe_load(token.content) or {}
    except yaml.YAMLError as exc:
        env.errors.append(f"{where}: table block is not valid YAML: {exc}")
        return ""
    if not isinstance(spec, dict) or "file" not in spec:
        env.errors.append(f"{where}: table block needs at least `file: results/name.csv`")
        return ""
    unknown = set(spec) - {"file", "caption", "columns", "format", "labels"}
    if unknown:
        env.errors.append(f"{where}: table block: unknown option(s) {', '.join(sorted(unknown))}")
    path = env.base_dir / str(spec["file"])
    if not path.exists():
        env.errors.append(f"{where}: table file {spec['file']} not found")
        return ""
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    available = list(rows[0].keys()) if rows else []
    columns: dict[str, str] = spec.get("columns") or {c: c for c in available}
    formats: dict[str, str] = spec.get("format") or {}
    labels: dict[str, str] = {str(k): str(v) for k, v in (spec.get("labels") or {}).items()}
    missing = [c for c in list(columns) + list(formats) if c not in available]
    if missing:
        env.errors.append(
            f"{where}: {spec['file']} has no column(s) {', '.join(missing)}; it has {', '.join(available)}"
        )
        return ""
    numeric = {c: c in formats or all(_is_number(r[c]) for r in rows) for c in columns}

    def cell(tag: str, col: str, text: str) -> str:
        """One table cell, right-aligned for numeric columns."""
        cls = ' class="num"' if numeric[col] else ""
        return f"<{tag}{cls}>{html.escape(text)}</{tag}>"

    head = "".join(cell("th", c, name) for c, name in columns.items())
    body = "\n".join(
        "<tr>" + "".join(cell("td", c, _format_cell(r[c], formats.get(c), labels)) for c in columns) + "</tr>"
        for r in rows
    )
    env.tables += 1
    caption = spec.get("caption")
    cap = f"<figcaption>Table {env.tables}. {html.escape(str(caption))}</figcaption>" if caption else ""
    return (
        f'<figure>\n<div class="table"><table>\n<thead><tr>{head}</tr></thead>\n'
        f"<tbody>\n{body}\n</tbody>\n</table></div>\n{cap}\n</figure>\n"
    )


def _fence(self: RendererHTML, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    """Render ```table blocks as CSV tables and every other fence as a normal code block."""
    token = tokens[idx]
    if token.info.strip() == "table":
        return _csv_table_html(token, env["render"])
    return RendererHTML.fence(self, tokens, idx, options, env)


def _table_open(self: RendererHTML, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    """Wrap Markdown tables in a box that scrolls sideways on narrow screens."""
    return '<div class="table">' + self.renderToken(tokens, idx, options, env)


def _table_close(self: RendererHTML, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    """Close the scrolling box opened by _table_open."""
    return self.renderToken(tokens, idx, options, env) + "</div>"


def _link_open(self: RendererHTML, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    """Open links to PDF files in a new tab, so the reader keeps the site and has it to come back to."""
    if (tokens[idx].attrGet("href") or "").lower().endswith(".pdf"):
        tokens[idx].attrSet("target", "_blank")
        tokens[idx].attrSet("rel", "noopener")
    return self.renderToken(tokens, idx, options, env)


def _parser() -> MarkdownIt:
    """Create the Markdown parser with tables, figures and CSV table blocks enabled."""
    md = MarkdownIt("commonmark", {"html": True, "typographer": True}).enable(
        ["table", "strikethrough", "replacements", "smartquotes"]
    )
    md.core.ruler.after("inline", "figures", _figures_rule)
    md.add_render_rule("fence", _fence)
    md.add_render_rule("table_open", _table_open)
    md.add_render_rule("table_close", _table_close)
    md.add_render_rule("link_open", _link_open)
    return md


_MD = _parser()


def render_page(text: str, source: Path, base_dir: Path, *, allow_h1: bool = False) -> tuple[str, RenderEnv]:
    """Render a whole Markdown document; problems are collected in the returned RenderEnv.

    Project pages get their title from the frontmatter of index.md, so a # heading there is an error; standalone
    pages such as contact.md bring their own (allow_h1=True).
    """
    env = RenderEnv(source=source, base_dir=base_dir, allow_h1=allow_h1)
    out = _MD.render(text, {"render": env})
    return out, env


def render_inline(text: str) -> str:
    """Render a short piece of Markdown (a summary or one bullet) without a wrapping <p>."""
    env = RenderEnv(source=Path("(inline)"), base_dir=Path("."))
    return _MD.renderInline(text, {"render": env})


def render_block(text: str) -> str:
    """Render a few paragraphs of Markdown from a YAML field."""
    env = RenderEnv(source=Path("(field)"), base_dir=Path("."))
    return _MD.render(text, {"render": env})
