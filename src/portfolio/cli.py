"""Command-line entry points: `uv run build` for the website and `uv run resume` for resume PDFs."""

from __future__ import annotations

import argparse
import functools
import http.server
import sys
import tempfile
import threading
import time
from pathlib import Path

from . import checks
from .content import ContentError, load
from .resume import compile_resume, resume_files
from .site import build_site

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ["content", "resume", "src/portfolio"]


def run_build(out: Path, *, drafts: bool) -> bool:
    """Validate everything, build the site into out/ and print problems. Returns True on success."""
    try:
        content = load(ROOT)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        return False

    errors = checks.leak_check(ROOT)
    warnings: list[str] = []

    resumes = resume_files(ROOT)
    published: bytes | None = None
    for name, path in resumes.items():
        try:
            pdf = compile_resume(ROOT, path)
        except RuntimeError as exc:
            errors.append(f"Resume does not compile: {exc}")
            continue
        if name == content.site.published_resume:
            published = pdf
    if content.site.published_resume not in resumes:
        errors.append(f"content/site.yaml: published_resume: no resume/{content.site.published_resume}.typ")

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
        f"Built {out} ({shown} of {len(content.projects)} projects shown{', plus hidden ones' if drafts else ''}; resumes: {', '.join(resumes)})."
    )
    return True


def _snapshot() -> dict[Path, float]:
    """Modification times of every watched file, to detect edits while serving."""
    return {p: p.stat().st_mtime for d in WATCHED for p in (ROOT / d).rglob("*") if p.is_file()}


def serve(out: Path, port: int, *, drafts: bool) -> None:
    """Build, serve out/ at http://localhost:<port>, and rebuild whenever a watched file changes."""
    run_build(out, drafts=drafts)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    handler.log_message = lambda *args: None  # type: ignore[method-assign]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Serving http://localhost:{port}/ (rebuilds on save; Ctrl+C to stop)")
    seen = _snapshot()
    try:
        while True:
            time.sleep(1)
            now = _snapshot()
            if now != seen:
                seen = now
                print("Change detected, rebuilding...")
                run_build(out, drafts=drafts)
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


def resume_main() -> None:
    """`uv run resume <name>`: compile resume/<name>.typ to resume/<name>.pdf (or --out)."""
    names = resume_files(ROOT)
    parser = argparse.ArgumentParser(prog="resume", description="Compile a resume to PDF.")
    parser.add_argument(
        "name", nargs="?", choices=sorted(names) + ["all"], default="all", help="which resume (default: all)"
    )
    parser.add_argument("--out", type=Path, help="output file (only with a single resume)")
    args = parser.parse_args()

    try:
        load(ROOT)
    except ContentError as exc:
        print(f"Content errors:\n{exc}", file=sys.stderr)
        sys.exit(1)
    targets = names if args.name == "all" else {args.name: names[args.name]}
    ok = True
    for path in targets.values():
        out = args.out if args.out and len(targets) == 1 else path.with_suffix(".pdf")
        try:
            out.write_bytes(compile_resume(ROOT, path))
            print(f"Wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            ok = False
    sys.exit(0 if ok else 1)
