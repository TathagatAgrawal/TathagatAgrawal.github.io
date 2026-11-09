"""Tests for Markdown rendering: figures, CSV tables and error reporting."""

from pathlib import Path

from PIL import Image

from portfolio.markdown import render_page


def _image(path: Path, width: int, height: int) -> None:
    """Write a blank PNG of the given size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (width, height), "white").save(path)


def test_lone_image_becomes_numbered_figure(tmp_path: Path) -> None:
    """An image alone in a paragraph becomes a captioned figure; wide images get the wide class."""
    _image(tmp_path / "figures" / "small.png", 400, 300)
    _image(tmp_path / "figures" / "wide.png", 1600, 600)
    text = '![A small plot](figures/small.png "First")\n\n![A wide plot](figures/wide.png "Second")\n'
    html, env = render_page(text, Path("page.md"), tmp_path)
    assert env.errors == []
    assert "<figure>" in html and "Figure 1. First" in html
    assert '<figure class="wide">' in html and "Figure 2. Second" in html


def test_dark_variant_is_used_when_present(tmp_path: Path) -> None:
    """A sibling file named name.dark.png is shown in dark mode."""
    _image(tmp_path / "figures" / "plot.png", 400, 300)
    _image(tmp_path / "figures" / "plot.dark.png", 400, 300)
    html, _ = render_page('![Plot](figures/plot.png "Caption")\n', Path("page.md"), tmp_path)
    assert 'class="light-only"' in html and "plot.dark.png" in html


def test_missing_figure_and_alt_text_are_errors(tmp_path: Path) -> None:
    """A figure file that doesn't exist, or one without alt text, is reported with its line."""
    _image(tmp_path / "figures" / "plot.png", 400, 300)
    text = "Intro\n\n![](figures/plot.png)\n\n![Gone](figures/gone.png)\n"
    _, env = render_page(text, Path("page.md"), tmp_path)
    assert any("page.md:3" in e and "alt text" in e for e in env.errors)
    assert any("page.md:5" in e and "not found" in e for e in env.errors)


def test_csv_table_block(tmp_path: Path) -> None:
    """A table block selects, renames, formats and relabels CSV columns."""
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "r.csv").write_text("name,score,extra\nbb_rsi,0.12345,x\n")
    text = "```table\nfile: results/r.csv\ncaption: Scores\ncolumns:\n  name: Strategy\n  score: Score\nformat:\n  score: '{:.2f}'\nlabels:\n  bb_rsi: Bollinger\n```\n"
    html, env = render_page(text, Path("page.md"), tmp_path)
    assert env.errors == []
    assert "<th>Strategy</th>" in html and '<td class="num">0.12</td>' in html
    assert "<td>Bollinger</td>" in html and "extra" not in html
    assert "Table 1. Scores" in html


def test_csv_table_unknown_column_is_an_error(tmp_path: Path) -> None:
    """Naming a column the CSV doesn't have is reported, listing the columns it does have."""
    (tmp_path / "r.csv").write_text("a,b\n1,2\n")
    _, env = render_page("```table\nfile: r.csv\ncolumns:\n  c: C\n```\n", Path("page.md"), tmp_path)
    assert env.errors and "no column(s) c" in env.errors[0]


def test_h1_is_rejected_on_project_pages(tmp_path: Path) -> None:
    """Project pages take their title from project.yaml, so # headings are flagged."""
    _, env = render_page("# Title\n", Path("page.md"), tmp_path)
    assert env.errors
    _, env = render_page("# Title\n", Path("contact.md"), tmp_path, allow_h1=True)
    assert not env.errors
