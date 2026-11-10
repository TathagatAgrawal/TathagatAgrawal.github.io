"""Tests for the search-engine helpers and for what the built site gives search engines."""

import html
import json
import re
from pathlib import Path

import pytest

from portfolio import seo
from portfolio.content import ContentError, load
from portfolio.site import build_site

ROOT = Path(__file__).resolve().parents[1]


def test_short_titles_keep_the_site_name() -> None:
    """A title that fits in 60 characters with the site name is left alone."""
    assert seo.title_tag("Projects", "Ada Lovelace") == "Projects · Ada Lovelace"


def test_long_titles_drop_the_name_then_are_cut_at_a_word() -> None:
    """A title too long with the name loses the name; one too long even alone is cut at a word boundary."""
    medium = "A project title that is fairly long but fits alone ok"
    assert seo.title_tag(medium, "Ada Lovelace") == medium
    long = "Advancing Linguistic Frontiers with mBERT Fine-Tuning for Hindi and English Named Entity Recognition"
    result = seo.title_tag(long, "Ada Lovelace")
    assert len(result) <= seo.TITLE_LIMIT and result.endswith("…") and long.startswith(result[:-1])
    assert not result[:-1].endswith(" ")


def test_descriptions_are_plain_text_cut_at_a_word() -> None:
    """Markdown formatting is removed and long text is cut at a word boundary within the limit."""
    text = "A **bold** claim with a [link](https://example.org) and `code`. " * 6
    result = seo.description(text)
    assert "**" not in result and "](" not in result and "`" not in result
    assert len(result) <= seo.DESCRIPTION_LIMIT and result.endswith("…")


def test_json_ld_is_safe_inside_a_script_tag() -> None:
    """Text containing a closing script tag can't end the structured-data block early."""
    text = seo.to_json([{"@type": "Person", "name": "</script><b>x"}])
    assert "</script>" not in text and json.loads(text)["@graph"][0]["name"] == "</script><b>x"


def test_warnings_find_duplicates_and_bad_sizes() -> None:
    """Missing, short, long and repeated titles and descriptions are each reported."""
    good = "d" * 100
    pages = [
        seo.PageSeo("/a/", "One", good),
        seo.PageSeo("/b/", "One", good),
        seo.PageSeo("/c/", "Three", ""),
        seo.PageSeo("/d/", "Four", "short"),
        seo.PageSeo("/e/", "Five", "x" * 200),
    ]
    text = "\n".join(seo.warnings_for(pages))
    assert "/b/: the title is the same as on /a/" in text and "/b/: the description is the same as on /a/" in text
    assert "/c/: no meta description" in text and "/d/: the meta description is only 5" in text
    assert "/e/: the meta description is 200 characters" in text


def test_last_modified_is_none_outside_a_git_repository(tmp_path: Path) -> None:
    """Without Git history the sitemap simply leaves the date out."""
    assert seo.last_modified(tmp_path, ["anything"]) is None


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list[str]]:
    """Build the real site once and return its folder and the build's warnings."""
    out = tmp_path_factory.mktemp("site")
    report = build_site(load(ROOT), out)
    return out, report.warnings


def pages(out: Path) -> list[Path]:
    """Every generated HTML page except the 404 page."""
    return [p for p in out.rglob("index.html")]


def test_every_page_has_a_unique_short_title_and_description(built: tuple[Path, list[str]]) -> None:
    """No page repeats another's title or description, and each is a size search results can show."""
    out, warnings = built
    assert not [w for w in warnings if "description" in w or "title" in w]
    titles, descriptions = set(), set()
    for page in pages(out):
        text = page.read_text(encoding="utf-8")
        title = html.unescape(re.search(r"<title>(.*?)</title>", text, re.DOTALL).group(1))
        description = html.unescape(re.search(r'<meta name="description" content="(.*?)">', text, re.DOTALL).group(1))
        assert len(title) <= seo.TITLE_LIMIT, (page, title)
        assert seo.DESCRIPTION_MIN <= len(description) <= seo.DESCRIPTION_LIMIT + 5, (page, description)
        assert title not in titles and description not in descriptions, page
        titles.add(title)
        descriptions.add(description)


def test_every_page_has_valid_structured_data(built: tuple[Path, list[str]]) -> None:
    """Each page carries JSON-LD that parses, and the right kinds of item for its type."""
    out, _ = built
    kinds: dict[str, set[str]] = {}
    for page in pages(out):
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', page.read_text(encoding="utf-8"), re.DOTALL
        )
        assert match, page
        graph = json.loads(match.group(1))["@graph"]
        kinds[str(page.parent.relative_to(out))] = {item["@type"] for item in graph}
    assert kinds["."] == {"WebSite", "Person"}
    assert "ScholarlyArticle" in kinds["research/grokking-review"]
    assert "Thesis" in kinds["research/grokking-thesis"]
    assert all("BreadcrumbList" in k for name, k in kinds.items() if name != ".")


def test_404_is_not_indexed_and_sitemap_has_dates(built: tuple[Path, list[str]]) -> None:
    """The 404 page asks not to be indexed, and the sitemap lists pages with their change dates."""
    out, _ = built
    assert 'name="robots" content="noindex"' in (out / "404.html").read_text(encoding="utf-8")
    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert "404" not in sitemap and "<lastmod>" in sitemap


def test_unknown_description_key_is_reported(tmp_path: Path) -> None:
    """A description for a page that doesn't exist is an error with a suggestion."""
    import shutil

    shutil.copytree(ROOT / "content", tmp_path / "content")
    config = tmp_path / "content" / "config.yaml"
    config.write_text(config.read_text().replace('  skills: "Skills of', '  skils: "Skills of'))
    with pytest.raises(ContentError, match=r"descriptions: 'skils' is not a page \(did you mean 'skills'"):
        load(tmp_path)
