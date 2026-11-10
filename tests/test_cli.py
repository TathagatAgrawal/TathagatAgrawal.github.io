"""Tests for the dev server's helpers: change detection and rebuilds that never break the served site."""

from pathlib import Path

import pytest

from portfolio import cli


def test_snapshot_ignores_compiled_caches_and_pdfs() -> None:
    """Files written by running the code or `uv run resume` must not trigger a rebuild."""
    files = cli._snapshot()
    assert files
    assert not any("__pycache__" in p.parts or p.suffix == ".pdf" for p in files)


def test_snapshot_survives_a_file_vanishing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A file deleted between listing and reading its time is skipped instead of raising."""
    original = Path.stat

    def flaky(self: Path, *args: object, **kwargs: object):
        """Fail for one watched file as if it had just been deleted."""
        if self.name == "config.yaml":
            raise FileNotFoundError(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", flaky)
    assert not any(p.name == "config.yaml" for p in cli._snapshot())


def test_rebuild_swaps_in_the_new_site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful rebuild replaces the served folder with the new build and removes the leftovers."""
    out = tmp_path / "_site"
    out.mkdir()
    (out / "old.html").write_text("old")

    def fake_build(path: Path, *, drafts: bool, shown_as: Path | None = None, check_pdfs: bool = True) -> bool:
        """Write a new site to the folder it is given."""
        path.mkdir()
        (path / "new.html").write_text("new")
        return True

    monkeypatch.setattr(cli, "run_build", fake_build)
    assert cli._rebuild(out, drafts=False) is True
    assert [p.name for p in out.iterdir()] == ["new.html"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["_site"]


def test_crashed_rebuild_keeps_the_previous_site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the build raises halfway, the folder being served is untouched and the error is reported."""
    out = tmp_path / "_site"
    out.mkdir()
    (out / "old.html").write_text("old")

    def crashing_build(path: Path, *, drafts: bool, shown_as: Path | None = None, check_pdfs: bool = True) -> bool:
        """Start writing a site and then fail."""
        path.mkdir()
        (path / "half.html").write_text("half")
        raise RuntimeError("template exploded")

    monkeypatch.setattr(cli, "run_build", crashing_build)
    assert cli._rebuild(out, drafts=False) is False
    assert [p.name for p in out.iterdir()] == ["old.html"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["_site"]


def test_failed_content_check_keeps_the_previous_site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When the content has errors nothing is built, and the previous site stays in place."""
    out = tmp_path / "_site"
    out.mkdir()
    (out / "old.html").write_text("old")
    monkeypatch.setattr(cli, "run_build", lambda path, *, drafts, shown_as=None, check_pdfs=True: False)
    assert cli._rebuild(out, drafts=False) is False
    assert [p.name for p in out.iterdir()] == ["old.html"]


def test_code_import_check_passes_for_the_real_package() -> None:
    """The check that guards the self-restart accepts the package as it is now."""
    assert cli._code_imports() is True


def test_copy_folder_defaults_to_icloud_when_it_exists(tmp_path: Path) -> None:
    """With no options the default folder is used if its parent exists, and skipped quietly if not."""
    icloud = tmp_path / "CloudDocs"
    default = icloud / "Resumes"
    assert cli.resolve_copy_dir(None, False, default) is None  # no iCloud Drive on this machine
    icloud.mkdir()
    assert cli.resolve_copy_dir(None, False, default) == default


def test_copy_folder_can_be_overridden_or_turned_off(tmp_path: Path) -> None:
    """--copy-to replaces the default (even when it doesn't exist yet), and --no-copy beats everything."""
    default = tmp_path / "CloudDocs" / "Resumes"
    other = tmp_path / "Elsewhere"
    assert cli.resolve_copy_dir(other, False, default) == other
    assert cli.resolve_copy_dir(Path("~/Somewhere"), False, default) == Path("~/Somewhere").expanduser()
    assert cli.resolve_copy_dir(other, True, default) is None
    (tmp_path / "CloudDocs").mkdir()
    assert cli.resolve_copy_dir(None, True, default) is None


def test_default_copy_folder_is_in_icloud_drive() -> None:
    """The built-in default is the Resumes folder of iCloud Drive, spelled without a user name."""
    assert cli.DEFAULT_COPY_DIR.name == "Resumes" and cli.DEFAULT_COPY_DIR.parent.name == "com~apple~CloudDocs"
    assert cli.DEFAULT_COPY_DIR.is_relative_to(Path.home())
