"""Tests for converting Markdown text into Typst markup for the resumes."""

import json
from pathlib import Path

import pytest
import typst

from portfolio.typst_markup import to_typst

FLATTEN = r"""
#let flat(c) = if type(c) == str { c } else if c.has("text") { c.text } else if c.has("children") {
  c.children.map(flat).join() } else if c.has("body") { flat(c.body) } else if c == [ ] { " " } else { "" }
#let items = json(bytes(sys.inputs.data))
#metadata(items.map(s => flat(eval(s, mode: "markup")))) <out>
"""


def visible_text(tmp_path: Path, converted: list[str]) -> list[str]:
    """Evaluate converted Typst markup with the Typst compiler and return the text each string shows."""
    source = tmp_path / "flatten.typ"
    source.write_text(FLATTEN, encoding="utf-8")
    result = typst.query(
        str(source), "<out>", field="value", one=True, root=str(tmp_path), sys_inputs={"data": json.dumps(converted)}
    )
    return json.loads(result) if isinstance(result, str) else result


@pytest.mark.parametrize(
    ("markdown", "typst_markup"),
    [
        ("plain text", "plain text"),
        ("a **bold** and *italic* word", "a *bold* and _italic_ word"),
        ("NDCG@3 and Q&A and C/C++", r"NDCG\@3 and Q&A and C\/C++"),
        ("costs $5, issue #1, ~9 months", r"costs \$5, issue \#1, \~9 months"),
        ("keep against&nbsp;9 months together", "keep against~9 months together"),
        ("a literal nbsp character\u00a0works too", "a literal nbsp character~works too"),
        (r"publications \[1\] and \[2\]", r"publications \[1\] and \[2\]"),
        ("a `code` span", "a `code` span"),
        ("see [the paper](https://x.org/a?b=c)", 'see #link("https://x.org/a?b=c")[the paper]'),
        (
            "see [paper](https://x.org)(2024) and [it](https://y.org).",
            'see #link("https://x.org")[paper]\\(2024) and #link("https://y.org")[it]\\.',
        ),
        ("a -- b and 'quoted' \"text\"", "a -- b and 'quoted' \"text\""),
        ("- not a list", r"\- not a list"),
        ("1. not a numbered list", r"1\. not a numbered list"),
    ],
)
def test_markdown_becomes_typst(markdown: str, typst_markup: str) -> None:
    """Each Markdown construct becomes the Typst markup that shows the same thing."""
    assert to_typst(markdown) == typst_markup


@pytest.mark.parametrize("markdown", ["![alt](pic.png)", "some <b>html</b>"])
def test_unsupported_markdown_is_an_error(markdown: str) -> None:
    """Images and raw HTML have no resume equivalent, so they are reported instead of mangled."""
    with pytest.raises(ValueError, match="not supported"):
        to_typst(markdown)


def test_converted_text_compiles_and_reads_as_written(tmp_path: Path) -> None:
    """Awkward text goes through the real Typst compiler and comes out as the characters that were written."""
    written = [
        "Built **NDCG@3** ranking, ~9 months, $5 & 100% of C/C++ #1 (see [paper](https://x.org)(2024)).",
        "Publications \\[1\\] and \\[2\\]; a_b_c *italic* `code` -- dash.",
        "- leading dash and 1. numbered",
        "against&nbsp;9 months and about ~9 months",
    ]
    shown = visible_text(tmp_path, [to_typst(text) for text in written])
    assert shown[0] == "Built NDCG@3 ranking, ~9 months, $5 & 100% of C/C++ #1 (see paper(2024))."
    assert shown[1] == "Publications [1] and [2]; a_b_c italic code – dash."  # Typst makes the en dash
    assert shown[2] == "- leading dash and 1. numbered"
    assert shown[3] == "against\u00a09 months and about ~9 months"  # a non-breaking space, and a real tilde
