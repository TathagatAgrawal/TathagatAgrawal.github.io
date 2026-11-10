"""Tests that every resume compiles, and that the PDFs are stable, named and copied as the config says."""

import shutil
from pathlib import Path

import pytest

from portfolio.cli import _write_resumes
from portfolio.content import ContentError, load
from portfolio.resume import (
    build_pdf,
    compile_resume,
    embedded_timestamp,
    file_name,
    today_timestamp,
    write_if_changed,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = load(ROOT)


@pytest.mark.parametrize("name", sorted(CONTENT.site.resumes))
def test_resume_compiles(name: str) -> None:
    """The resume is built from its entry in the config and the content files, and produces a PDF."""
    assert compile_resume(CONTENT, name).startswith(b"%PDF")


def test_unknown_resume_is_reported() -> None:
    """Asking for a resume that is not in the config fails with the names that are."""
    with pytest.raises(RuntimeError, match="no resume called 'nope'; the resumes are"):
        compile_resume(CONTENT, "nope")


def test_a_pdf_records_the_date_it_was_stamped_with() -> None:
    """The date can be read back out of a PDF, and building twice with the same date gives identical bytes."""
    stamp = 1_700_000_000 - 1_700_000_000 % 86400  # midnight UTC
    first = compile_resume(CONTENT, "general", timestamp=stamp)
    assert embedded_timestamp(first) == stamp
    assert compile_resume(CONTENT, "general", timestamp=stamp) == first


def test_unchanged_content_keeps_the_existing_pdf_and_its_date() -> None:
    """Rebuilding with nothing changed returns the existing file as it is, so Git sees no change."""
    old = compile_resume(CONTENT, "general", timestamp=1_600_000_000 - 1_600_000_000 % 86400)
    data, changed = build_pdf(CONTENT, "general", old)
    assert changed is False and data == old
    assert embedded_timestamp(data) == embedded_timestamp(old)


def test_a_missing_or_foreign_pdf_counts_as_changed() -> None:
    """With no previous PDF, or one without a creation date, the resume is built fresh and reported as changed."""
    assert build_pdf(CONTENT, "general", None)[1] is True
    assert build_pdf(CONTENT, "general", b"not a pdf")[1] is True


def test_changed_content_gives_a_new_pdf_dated_today(tmp_path: Path) -> None:
    """When a bullet changes, the resume is rebuilt and stamped with today's date, not the old one."""
    shutil.copytree(ROOT / "content", tmp_path / "content")
    shutil.copytree(ROOT / "resume", tmp_path / "resume", ignore=shutil.ignore_patterns("*.pdf"))
    old = compile_resume(CONTENT, "ml", timestamp=1_600_000_000 - 1_600_000_000 % 86400)
    path = tmp_path / "content" / "experience" / "finlatics.yaml"
    path.write_text(path.read_text().replace("Conducted case studies", "Ran case studies"))
    data, changed = build_pdf(load(tmp_path), "ml", old)
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One command writes the repo copy and the named copy; running it again changes nothing."""
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
