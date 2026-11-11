"""Tests that stylesheets and scripts are addressed by a fingerprint, so browsers never use a stale copy."""

import re
from pathlib import Path

from portfolio import site
from portfolio.content import load
from portfolio.site import asset_versions, build_site

ROOT = Path(__file__).resolve().parents[1]


def test_every_css_and_js_file_has_a_fingerprint() -> None:
    """The stylesheet and the script each get a short fingerprint."""
    versions = asset_versions()
    assert set(versions) >= {"style.css", "theme.js"}
    assert all(re.fullmatch(r"[0-9a-f]{10}", v) for v in versions.values())


def test_the_fingerprint_changes_with_the_file(tmp_path: Path, monkeypatch) -> None:
    """Editing a stylesheet gives it a new fingerprint, which is what makes browsers fetch it again."""
    folder = tmp_path / "static"
    folder.mkdir()
    (folder / "style.css").write_text("a { color: red }")
    monkeypatch.setattr(site, "STATIC", folder)
    before = asset_versions()["style.css"]
    assert asset_versions()["style.css"] == before
    (folder / "style.css").write_text("a { color: blue }")
    assert asset_versions()["style.css"] != before


def test_pages_load_the_fingerprinted_addresses(tmp_path: Path) -> None:
    """Every page, including the 404 page, links the stylesheet and script with the current fingerprint."""
    build_site(load(ROOT), tmp_path)
    versions = asset_versions()
    for page in [tmp_path / "index.html", tmp_path / "404.html", tmp_path / "projects" / "index.html"]:
        text = page.read_text(encoding="utf-8")
        assert f'href="/style.css?v={versions["style.css"]}"' in text, page
        assert f'src="/theme.js?v={versions["theme.js"]}"' in text, page
