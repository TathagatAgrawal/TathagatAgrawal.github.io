"""Command-line entry points: `uv run build` for the website and `uv run resume` for resume PDFs."""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable
from pathlib import Path

from . import checks
from .content import ContentError, load
from .resume import available_fonts, build_pdf, compile_resume, file_name, write_if_changed
from .site import build_site

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ["content", "resume", "src/portfolio"]
# Where `uv run resume` also copies the PDFs unless told otherwise: a folder in iCloud Drive, so they reach a phone.
DEFAULT_COPY_DIR = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Resumes"


def run_build(
    out: Path, *, drafts: bool, shown_as: Path | None = None, check_pdfs: bool = True, ci: bool = False
) -> bool:
    """Validate everything, build the site into out/ and print problems. Returns True on success.

    shown_as is the folder to name in the final message when out/ is only a staging folder.

    The site's /resume.pdf is the resume PDF committed in resume/, not one built here. check_pdfs warns when a
    committed PDF no longer matches the content. The dev server turns it off, because the PDFs are naturally out
    of date while you edit, and it shows a fresh build of the resume instead. ci is for GitHub, which has none of
    your fonts: it only checks that each resume still builds with the bundled fonts, and publishes the committed
    PDFs without comparing them.
    """
    try:
        content = load(ROOT)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        return False

    errors = checks.leak_check(ROOT)
    warnings: list[str] = []

    resumes = list(content.site.resumes)
    published: bytes | None = None
    for name in resumes:
        committed = ROOT / "resume" / f"{name}.pdf"
        previous = committed.read_bytes() if committed.exists() else None
        try:
            if ci:
                compile_resume(content, name, portable=True)  # only to see that it builds; the output is discarded
                pdf, changed = previous, False
            else:
                pdf, changed = build_pdf(content, name, previous)
        except RuntimeError as exc:
            errors.append(f"Resume does not compile: {exc}")
            continue
        if check_pdfs and changed:
            state = "is missing" if previous is None else "is out of date"
            warnings.append(f"resume/{name}.pdf {state}; run `uv run resume` and commit it")
        if name == content.site.website.resume:
            if not check_pdfs and not ci:
                published = pdf  # the dev server shows your latest edits
            elif previous is not None:
                published = previous  # what is committed is what is published
            elif ci:
                errors.append(
                    f"resume/{name}.pdf is missing, so the site has no resume to publish; run `uv run resume` and commit it"
                )
            else:
                published = pdf

    report = build_site(content, out, drafts=drafts)
    errors += report.errors
    warnings += report.warnings
    if published is not None:
        (out / "resume.pdf").write_bytes(published)
    errors += checks.link_check(out)

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} problem(s); fix them before publishing.", file=sys.stderr)
        return False
    shown = sum(1 for p in content.projects.values() if p.visible)
    print(
        f"Built {shown_as or out} ({shown} of {len(content.projects)} projects shown{', plus hidden ones' if drafts else ''}; resumes: {', '.join(resumes)})."
    )
    return True


def _snapshot() -> dict[Path, float]:
    """Modification times of every watched file, to detect edits while serving.

    Compiled caches and PDFs are skipped (they are written by running the code and `uv run resume`, not
    edited), and a file that disappears while scanning is ignored.
    """
    times: dict[Path, float] = {}
    for d in WATCHED:
        for p in (ROOT / d).rglob("*"):
            if "__pycache__" in p.parts or p.suffix == ".pdf":
                continue
            try:
                if p.is_file():
                    times[p] = p.stat().st_mtime
            except OSError:
                continue
    return times


def _rebuild(out: Path, *, drafts: bool) -> bool:
    """Rebuild the site for the dev server without ever stopping it or leaving a broken site behind.

    The site is built next to out/ and swapped in afterwards, so a build that crashes halfway leaves the
    previous site being served. Content errors are printed by run_build; any other error is printed here
    with its traceback. Returns True when the build had no problems.
    """
    staging = out.with_name(out.name + ".building")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        ok = run_build(staging, drafts=drafts, shown_as=out, check_pdfs=False)
    except Exception:  # noqa: BLE001 - deliberate: keep serving the previous site however the build failed
        traceback.print_exc()
        print("Build crashed; still serving the previous site. Fix the error and save again.", file=sys.stderr)
        shutil.rmtree(staging, ignore_errors=True)
        return False
    if staging.exists():
        old = out.with_name(out.name + ".old")
        shutil.rmtree(old, ignore_errors=True)
        if out.exists():
            os.replace(out, old)
        os.replace(staging, out)
        shutil.rmtree(old, ignore_errors=True)
    return ok


def _code_imports() -> bool:
    """Check in a fresh interpreter that the package imports, printing the error if it does not.

    This runs before the server restarts itself on a code change, so that a half-typed edit to a .py
    file doesn't take the server down: it keeps running the old code until the file is fixed.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import portfolio.cli"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def _watch(on_change: Callable[[], None], before_restart: Callable[[], None] = lambda: None) -> None:
    """Call on_change whenever a watched file changes, until interrupted.

    Python code can't be reloaded in place, so when a .py file changes (and still imports) the process
    restarts itself with the same command line, after calling before_restart to release anything it holds.
    """
    seen = _snapshot()
    while True:
        time.sleep(1)
        now = _snapshot()
        if now == seen:
            continue
        changed = {p for p in now.keys() | seen.keys() if now.get(p) != seen.get(p)}
        seen = now
        if any(p.suffix == ".py" for p in changed):
            print("Python code changed, restarting...")
            if _code_imports():
                before_restart()
                os.execv(sys.executable, [sys.executable, *sys.argv])
            print("The code doesn't import yet; still running the old code. Fix it and save again.")
            continue
        print("Change detected, rebuilding...")
        try:
            on_change()
        except Exception:  # noqa: BLE001 - deliberate: a failed rebuild must not end the watch
            traceback.print_exc()


def serve(out: Path, port: int, *, drafts: bool) -> None:
    """Build, serve out/ at http://localhost:<port>, and keep it up to date as files change.

    Content, resume and template edits rebuild the site; Python edits restart the server (see _watch).
    """
    _rebuild(out, drafts=drafts)
    out.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    handler.log_message = lambda *args: None  # type: ignore[method-assign]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Serving http://localhost:{port}/ (rebuilds on save, restarts on code changes; Ctrl+C to stop)")

    def release() -> None:
        """Close the listening socket so the restarted server can use the port."""
        server.shutdown()
        server.server_close()

    try:
        _watch(lambda: _rebuild(out, drafts=drafts), release)
    except KeyboardInterrupt:
        server.shutdown()


def main() -> None:
    """`uv run build`: check the content and build the website (and the published resume)."""
    parser = argparse.ArgumentParser(prog="build", description="Build the website into _site/.")
    parser.add_argument("--serve", action="store_true", help="serve the site locally and rebuild on every save")
    parser.add_argument(
        "--drafts", action="store_true", help="include projects marked hidden (never use for publishing)"
    )
    parser.add_argument("--check", action="store_true", help="only check for problems; write nothing")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="for GitHub, which lacks your fonts: only check that each resume builds with the bundled fonts, "
        "and publish the committed resume PDFs",
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()

    if args.serve:
        serve(args.out, args.port, drafts=args.drafts)
        return
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            sys.exit(0 if run_build(Path(tmp) / "site", drafts=args.drafts, ci=args.ci) else 1)
    sys.exit(0 if run_build(args.out, drafts=args.drafts, ci=args.ci) else 1)


def _write_resumes(
    targets: list[str], out_file: Path | None, copy_dir: Path | None = None, repo_dir: Path | None = None
) -> bool:
    """Reload the content and build each named resume; print and return any problem.

    Each PDF goes to resume/<name>.pdf (or out_file), where it is kept under Git and only changes when the
    content does, and, if copy_dir is given, to <copy_dir>/<filename>.pdf as well.
    """
    try:
        content = load(ROOT)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        return False
    repo_dir = repo_dir or ROOT / "resume"
    if copy_dir is not None:
        if not copy_dir.parent.exists():
            print(
                f"error: {copy_dir.parent} does not exist, so {copy_dir.name!r} can't be created in it", file=sys.stderr
            )
            return False
        copy_dir.mkdir(exist_ok=True)
    ok = True
    for name in targets:
        out = out_file if out_file and len(targets) == 1 else repo_dir / f"{name}.pdf"
        previous = out.read_bytes() if out.exists() else None
        try:
            pdf, _ = build_pdf(content, name, previous)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            ok = False
            continue
        shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
        print(f"{'Wrote' if write_if_changed(out, pdf) else 'Up to date:'} {shown}")
        if copy_dir is not None:
            copy = copy_dir / f"{file_name(content, name)}.pdf"
            print(f"  {'copied to' if write_if_changed(copy, pdf) else 'already in'} {copy}")
    return ok


def resolve_copy_dir(copy_to: Path | None, no_copy: bool, default: Path = DEFAULT_COPY_DIR) -> Path | None:
    """The folder resumes are copied to, or None for no copy.

    --no-copy means none; --copy-to names a folder (an error later if its parent is missing). Otherwise the
    default is used, but only when its parent exists, so a machine without iCloud Drive just skips the copy.
    """
    if no_copy:
        return None
    if copy_to is not None:
        return copy_to.expanduser()
    return default if default.parent.exists() else None


def resume_main() -> None:
    """`uv run resume <name>`: build resumes from content/config.yaml into resume/ and, optionally, another folder."""
    try:
        names = list(load(ROOT).site.resumes)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(prog="resume", description="Build resumes as PDFs into resume/ (kept in Git).")
    parser.add_argument(
        "name", nargs="?", choices=sorted(names) + ["all"], default="all", help="which resume (default: all)"
    )
    parser.add_argument("--out", type=Path, help="write the PDF here instead of resume/<name>.pdf (single resume only)")
    parser.add_argument(
        "--copy-to",
        type=Path,
        metavar="DIR",
        help="copy each PDF into DIR, under its `filename` from config.yaml, instead of the default folder "
        f"({str(DEFAULT_COPY_DIR).replace(str(Path.home()), '~')})",
    )
    parser.add_argument("--no-copy", action="store_true", help="only write resume/<name>.pdf; don't copy anywhere")
    parser.add_argument("--watch", action="store_true", help="rebuild the PDF on every save (for live preview)")
    parser.add_argument("--list-fonts", action="store_true", help="list the fonts a resume can use, then stop")
    args = parser.parse_args()
    if args.list_fonts:
        print("\n".join(available_fonts(ROOT)))
        return
    copy_dir = resolve_copy_dir(args.copy_to, args.no_copy)

    targets = names if args.name == "all" else [args.name]
    ok = _write_resumes(targets, args.out, copy_dir)
    if args.watch:
        print("Watching content, resume and code files; Ctrl+C to stop.")
        try:
            _watch(lambda: _write_resumes(targets, args.out, copy_dir))
        except KeyboardInterrupt:
            return
    sys.exit(0 if ok else 1)
