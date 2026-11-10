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
from .resume import compile_resume
from .site import build_site

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ["content", "resume", "src/portfolio"]


def run_build(out: Path, *, drafts: bool, shown_as: Path | None = None) -> bool:
    """Validate everything, build the site into out/ and print problems. Returns True on success.

    shown_as is the folder to name in the final message when out/ is only a staging folder.
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
        try:
            pdf = compile_resume(content, name)
        except RuntimeError as exc:
            errors.append(f"Resume does not compile: {exc}")
            continue
        if name == content.site.website.resume:
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
        ok = run_build(staging, drafts=drafts, shown_as=out)
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
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()

    if args.serve:
        serve(args.out, args.port, drafts=args.drafts)
        return
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            sys.exit(0 if run_build(Path(tmp) / "site", drafts=args.drafts) else 1)
    sys.exit(0 if run_build(args.out, drafts=args.drafts) else 1)


def _write_resumes(targets: list[str], out_file: Path | None) -> bool:
    """Reload the content and compile each named resume to resume/<name>.pdf; print and return any problem."""
    try:
        content = load(ROOT)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        return False
    ok = True
    for name in targets:
        out = out_file if out_file and len(targets) == 1 else ROOT / "resume" / f"{name}.pdf"
        try:
            out.write_bytes(compile_resume(content, name))
            print(f"Wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            ok = False
    return ok


def resume_main() -> None:
    """`uv run resume <name>`: compile a resume from content/config.yaml to resume/<name>.pdf (or --out)."""
    try:
        names = list(load(ROOT).site.resumes)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(prog="resume", description="Compile a resume to PDF.")
    parser.add_argument(
        "name", nargs="?", choices=sorted(names) + ["all"], default="all", help="which resume (default: all)"
    )
    parser.add_argument("--out", type=Path, help="output file (only with a single resume)")
    parser.add_argument("--watch", action="store_true", help="rebuild the PDF on every save (for live preview)")
    args = parser.parse_args()

    targets = names if args.name == "all" else [args.name]
    ok = _write_resumes(targets, args.out)
    if args.watch:
        print("Watching content, resume and code files; Ctrl+C to stop.")
        try:
            _watch(lambda: _write_resumes(targets, args.out))
        except KeyboardInterrupt:
            return
    sys.exit(0 if ok else 1)
