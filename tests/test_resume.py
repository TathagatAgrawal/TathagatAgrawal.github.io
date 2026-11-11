"""Tests that every resume compiles, and that the PDFs are stable, named and copied as the config says."""

import shutil
import sys
from pathlib import Path

import pytest

from portfolio import cli
from portfolio.cli import _write_resumes
from portfolio.content import ContentError, load
from portfolio.resume import (
    available_fonts,
    build_pdf,
    compile_resume,
    embedded_timestamp,
    file_name,
    font_paths,
    today_timestamp,
    write_if_changed,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = load(ROOT)


@pytest.mark.parametrize("name", sorted(CONTENT.site.resumes))
def test_resume_compiles(name: str) -> None:
    """The resume is built from its entry in the config and the content files, and produces a PDF."""
    assert compile_resume(CONTENT, name, portable=True).startswith(b"%PDF")


def test_unknown_resume_is_reported() -> None:
    """Asking for a resume that is not in the config fails with the names that are."""
    with pytest.raises(RuntimeError, match="no resume called 'nope'; the resumes are"):
        compile_resume(CONTENT, "nope")


def test_a_pdf_records_the_date_it_was_stamped_with() -> None:
    """The date can be read back out of a PDF, and building twice with the same date gives identical bytes."""
    stamp = 1_700_000_000 - 1_700_000_000 % 86400  # midnight UTC
    first = compile_resume(CONTENT, "general", timestamp=stamp, portable=True)
    assert embedded_timestamp(first) == stamp
    assert compile_resume(CONTENT, "general", timestamp=stamp, portable=True) == first


def test_unchanged_content_keeps_the_existing_pdf_and_its_date() -> None:
    """Rebuilding with nothing changed returns the existing file as it is, so Git sees no change."""
    old = compile_resume(CONTENT, "general", timestamp=1_600_000_000 - 1_600_000_000 % 86400, portable=True)
    data, changed = build_pdf(CONTENT, "general", old, portable=True)
    assert changed is False and data == old
    assert embedded_timestamp(data) == embedded_timestamp(old)


def test_a_missing_or_foreign_pdf_counts_as_changed() -> None:
    """With no previous PDF, or one without a creation date, the resume is built fresh and reported as changed."""
    assert build_pdf(CONTENT, "general", None, portable=True)[1] is True
    assert build_pdf(CONTENT, "general", b"not a pdf", portable=True)[1] is True


def test_changed_content_gives_a_new_pdf_dated_today(tmp_path: Path) -> None:
    """When a bullet changes, the resume is rebuilt and stamped with today's date, not the old one."""
    shutil.copytree(ROOT / "content", tmp_path / "content")
    shutil.copytree(ROOT / "resume", tmp_path / "resume", ignore=shutil.ignore_patterns("*.pdf"))
    old = compile_resume(CONTENT, "ml", timestamp=1_600_000_000 - 1_600_000_000 % 86400, portable=True)
    path = tmp_path / "content" / "experience" / "finlatics.yaml"
    path.write_text(path.read_text().replace("Conducted case studies", "Ran case studies"))
    data, changed = build_pdf(load(tmp_path), "ml", old, portable=True)
    assert changed is True and data != old
    assert embedded_timestamp(data) == today_timestamp()


def test_resume_file_names_come_from_the_config_or_a_default(tmp_path: Path) -> None:
    """A resume's outside name is its `filename` in the config, else "<Name> - Resume (<key>)"."""
    assert file_name(CONTENT, "ml") == "Tathagat Agrawal - Resume (ML)"
    shutil.copytree(ROOT / "content", tmp_path / "content")
    config = tmp_path / "content" / "config.yaml"
    config.write_text(config.read_text().replace("    filename: Tathagat Agrawal - Resume (ML)\n", ""))
    assert file_name(load(tmp_path), "ml") == "Tathagat Agrawal - Resume (ml)"


@pytest.mark.parametrize("bad", ["a/b", "..\\\\x", ".hidden", "what?", "  "])
def test_a_file_name_must_be_a_plain_name(tmp_path: Path, bad: str) -> None:
    """Folders, a leading dot and characters file systems refuse are rejected in `filename`."""
    shutil.copytree(ROOT / "content", tmp_path / "content")
    config = tmp_path / "content" / "config.yaml"
    config.write_text(config.read_text().replace("filename: Tathagat Agrawal - Resume (ML)", f"filename: '{bad}'"))
    with pytest.raises(ContentError, match="filename"):
        load(tmp_path)


def test_write_if_changed_leaves_an_identical_file_alone(tmp_path: Path) -> None:
    """A file that already holds the same bytes isn't rewritten, so its modification time (and iCloud) stay put."""
    path = tmp_path / "a.pdf"
    assert write_if_changed(path, b"one") is True
    stamp = path.stat().st_mtime_ns
    assert write_if_changed(path, b"one") is False and path.stat().st_mtime_ns == stamp
    assert write_if_changed(path, b"two") is True and path.read_bytes() == b"two"


def test_resumes_are_kept_in_the_repo_and_copied_to_another_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One command writes the repo copy and the named copy; running it again changes nothing."""
    monkeypatch.setattr(cli, "build_pdf", lambda c, n, prev: build_pdf(c, n, prev, portable=True))
    repo, copies = tmp_path / "resume", tmp_path / "icloud" / "Resumes"
    repo.mkdir()
    (tmp_path / "icloud").mkdir()
    assert _write_resumes(["general", "ml"], None, copies, repo) is True
    assert sorted(p.name for p in repo.iterdir()) == ["general.pdf", "ml.pdf"]
    assert sorted(p.name for p in copies.iterdir()) == [
        "Tathagat Agrawal - Resume (ML).pdf",
        "Tathagat Agrawal - Resume.pdf",
    ]
    assert (copies / "Tathagat Agrawal - Resume.pdf").read_bytes() == (repo / "general.pdf").read_bytes()
    before = {p: p.stat().st_mtime_ns for p in [*repo.iterdir(), *copies.iterdir()]}
    capsys.readouterr()
    assert _write_resumes(["general", "ml"], None, copies, repo) is True
    assert {p: p.stat().st_mtime_ns for p in before} == before
    assert "Up to date" in capsys.readouterr().out


def test_copy_folder_must_be_in_an_existing_folder(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A copy folder whose parent doesn't exist is an error, not a surprise tree of new folders."""
    (tmp_path / "resume").mkdir()
    assert _write_resumes(["general"], None, tmp_path / "missing" / "Resumes", tmp_path / "resume") is False
    assert "does not exist" in capsys.readouterr().err
    assert not (tmp_path / "missing").exists()


def project_copy(tmp_path: Path, layout: dict[str, object] | None = None, resume: str = "general") -> Path:
    """Copy the content and the Typst layout into tmp_path. With a layout, every resume's layout is reset to the
    defaults and the named resume gets that layout, so the result does not depend on the real config's choices."""
    import yaml

    shutil.copytree(ROOT / "content", tmp_path / "content")
    shutil.copytree(ROOT / "resume", tmp_path / "resume", ignore=shutil.ignore_patterns("*.pdf", "fonts"))
    if layout is not None:
        config = tmp_path / "content" / "config.yaml"
        data = yaml.safe_load(config.read_text())
        for entry in data["resumes"].values():
            entry["layout"] = {}  # start from the defaults, whatever the real config chooses
        data["resumes"][resume]["layout"] = dict(layout)
        config.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return tmp_path


def test_a_bundled_font_can_be_chosen_per_resume(tmp_path: Path) -> None:
    """`font` in a resume's layout changes the typeface in the PDF, and leaves other resumes alone."""
    root = project_copy(tmp_path, {"font": "New Computer Modern"})
    content = load(root)
    assert b"NewCM10" in compile_resume(content, "general")
    assert b"NewCM10" not in compile_resume(content, "ml")
    assert b"LibertinusSerif" in compile_resume(content, "ml")


def test_font_can_be_one_name_or_a_list_of_names(tmp_path: Path) -> None:
    """A single family and a list of families are both accepted, and a bare name becomes a list."""
    one = load(project_copy(tmp_path / "one", {"font": "New Computer Modern"}))
    many = load(project_copy(tmp_path / "many", {"font": ["New Computer Modern", "Libertinus Serif"]}))
    assert one.site.resumes["general"].layout.font == ["New Computer Modern"]
    assert many.site.resumes["general"].layout.font == ["New Computer Modern", "Libertinus Serif"]


@pytest.mark.parametrize("bad", ["", "  ", [], [""], [1], {"a": 1}])
def test_a_font_must_be_a_family_name_or_a_list_of_them(tmp_path: Path, bad: object) -> None:
    """Empty names and other types are rejected when the config is loaded."""
    with pytest.raises(ContentError, match="font"):
        load(project_copy(tmp_path, {"font": bad}))


def test_a_font_that_is_not_available_is_an_error_not_a_silent_fallback(tmp_path: Path) -> None:
    """Typst would quietly use another font, so a misspelt family is reported with the ones that exist."""
    content = load(project_copy(tmp_path, {"font": "New Computer Moderne"}))
    with pytest.raises(
        RuntimeError,
        match=r"'New Computer Moderne' \(did you mean 'New Computer Modern'\?\) is not available.*--list-fonts.*resume/fonts/",
    ):
        compile_resume(content, "general")


def test_font_size_changes_the_text_size(tmp_path: Path) -> None:
    """`font_size` and `name_size` in the layout change the PDF, with no font named."""
    base = load(project_copy(tmp_path / "base", {}))
    changed = load(project_copy(tmp_path / "changed", {"font_size": "9pt", "name_size": "18pt"}))
    assert compile_resume(changed, "general") != compile_resume(base, "general")


def test_extra_fonts_come_from_the_resume_fonts_folder(tmp_path: Path) -> None:
    """resume/fonts/ is searched when it exists, and the bundled fonts are always available."""
    assert font_paths(tmp_path) == []
    (tmp_path / "resume" / "fonts").mkdir(parents=True)
    assert font_paths(tmp_path) == [str(tmp_path / "resume" / "fonts")]
    assert {"Libertinus Serif", "New Computer Modern"} <= set(available_fonts(ROOT))


def pdf_colors_and_sizes(pdf: bytes) -> tuple[set[tuple[float, float, float]], set[float]]:
    """The fill colors and font sizes recorded in a PDF's page content (decompressed from its streams)."""
    import re
    import zlib

    colors: set[tuple[float, float, float]] = set()
    sizes: set[float] = set()
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.DOTALL):
        try:
            content = zlib.decompress(match.group(1))
        except zlib.error:
            continue
        for r, g, b in re.findall(rb"([\d.]+) ([\d.]+) ([\d.]+) scn", content):
            colors.add((round(float(r), 2), round(float(g), 2), round(float(b), 2)))
        sizes.update(float(size) for size in re.findall(rb"/\w+ ([\d.]+) Tf", content))
    return colors, sizes


def test_accent_sets_the_theme_color(tmp_path: Path) -> None:
    """A hex accent replaces Typst's blue for the name, headings, rules and links, and a color name works too."""
    blue = (0.0, 0.45, 0.85)
    colors, _ = pdf_colors_and_sizes(compile_resume(load(project_copy(tmp_path / "default", {})), "general"))
    assert blue in colors
    colors, _ = pdf_colors_and_sizes(
        compile_resume(load(project_copy(tmp_path / "hex", {"accent": "#c0392b"})), "general")
    )
    assert (0.75, 0.22, 0.17) in colors and blue not in colors
    colors, _ = pdf_colors_and_sizes(
        compile_resume(load(project_copy(tmp_path / "name", {"accent": "navy"})), "general")
    )
    assert (0.0, 0.12, 0.25) in colors and blue not in colors  # Typst's navy is #001f3f


def test_heading_size_changes_only_the_section_headings(tmp_path: Path) -> None:
    """Section headings are 12pt unless `heading_size` says otherwise; the name and the body keep their sizes."""
    _, default = pdf_colors_and_sizes(compile_resume(load(project_copy(tmp_path / "default", {}, "ml")), "ml"))
    _, bigger = pdf_colors_and_sizes(
        compile_resume(load(project_copy(tmp_path / "bigger", {"heading_size": "14pt"}, "ml")), "ml")
    )
    assert 12.0 in default and 14.0 not in default
    assert 14.0 in bigger and 12.0 not in bigger
    assert {10.0, 20.0} <= bigger  # body and name unchanged


@pytest.mark.parametrize("bad", ["blue-ish", "#12", "#gggggg", "0b5cad", "rgb(1,2,3)", "red; panic()", 12, ["red"]])
def test_an_accent_must_be_a_hex_color_or_a_known_name(tmp_path: Path, bad: object) -> None:
    """Anything else is rejected when the config is loaded, with a hint about the quotes."""
    with pytest.raises(ContentError, match="accent"):
        load(project_copy(tmp_path, {"accent": bad}))


def test_heading_size_needs_a_unit(tmp_path: Path) -> None:
    """Like the other sizes, a bare number is an error."""
    with pytest.raises(ContentError, match="heading_size"):
        load(project_copy(tmp_path, {"heading_size": 14}))


def test_portable_mode_ignores_the_font_setting(tmp_path: Path) -> None:
    """GitHub has none of your fonts, so it builds without the `font` setting; a normal build insists on the font."""
    content = load(project_copy(tmp_path, {"font": "A Font Only My Laptop Has"}))
    assert compile_resume(content, "general", portable=True).startswith(b"%PDF")
    with pytest.raises(RuntimeError, match="is not available on this computer"):
        compile_resume(content, "general")


def test_font_names_are_not_case_sensitive(tmp_path: Path) -> None:
    """Typst matches families without regard to case, so the check does too."""
    content = load(project_copy(tmp_path, {"font": "new computer modern"}))
    assert b"NewCM10" in compile_resume(content, "general")


def test_installed_fonts_are_available_as_well_as_the_bundled_ones() -> None:
    """Resumes can use every font on this computer, in addition to the bundled and resume/fonts/ ones."""
    bundled = set(available_fonts(ROOT, system=False))
    everything = set(available_fonts(ROOT))
    assert {"Libertinus Serif", "New Computer Modern"} <= bundled <= everything


def test_list_fonts_prints_what_a_resume_can_use(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`uv run resume --list-fonts` prints the font families, one per line, and builds nothing."""
    monkeypatch.setattr(sys, "argv", ["resume", "--list-fonts"])
    cli.resume_main()
    lines = capsys.readouterr().out.splitlines()
    assert "Libertinus Serif" in lines and lines == sorted(set(lines))


def test_github_publishes_the_committed_resume_without_building_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """In --ci mode the site's resume.pdf is the committed one, and no 'out of date' comparison is attempted."""
    assert cli.run_build(tmp_path / "site", drafts=False, ci=True) is True
    assert (tmp_path / "site" / "resume.pdf").read_bytes() == (ROOT / "resume" / "general.pdf").read_bytes()
    assert "out of date" not in capsys.readouterr().err


def test_github_needs_a_committed_resume_to_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no committed resume PDF, --ci fails and says to build and commit it, instead of publishing nothing."""
    monkeypatch.setattr(cli, "ROOT", project_copy(tmp_path / "project"))
    assert cli.run_build(tmp_path / "site", drafts=False, ci=True) is False
    assert "resume/general.pdf is missing" in capsys.readouterr().err


def test_a_normal_build_publishes_the_committed_resume_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """What is committed is what is published, whether or not a fresh build would look different."""
    monkeypatch.setattr(cli, "build_pdf", lambda c, n, prev: (b"%PDF-a fresh build", True))
    assert cli.run_build(tmp_path / "site", drafts=False) is True
    assert (tmp_path / "site" / "resume.pdf").read_bytes() == (ROOT / "resume" / "general.pdf").read_bytes()


def test_the_dev_server_shows_a_fresh_resume_so_edits_are_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With check_pdfs off (the dev server) /resume.pdf is the fresh build, and there is no 'out of date' warning."""
    monkeypatch.setattr(cli, "build_pdf", lambda c, n, prev: (b"%PDF-a fresh build", True))
    assert cli.run_build(tmp_path / "site", drafts=False, check_pdfs=False) is True
    assert (tmp_path / "site" / "resume.pdf").read_bytes() == b"%PDF-a fresh build"
    assert "out of date" not in capsys.readouterr().err
