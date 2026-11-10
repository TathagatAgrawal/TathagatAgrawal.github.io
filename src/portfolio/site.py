"""Build the static website from content/ into _site/."""

from __future__ import annotations

import datetime as dt
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from . import markdown, seo, social
from .content import Content, Project, date_key, format_date

NAV = [
    ("/projects/", "Projects", "projects"),
    ("/experience/", "Experience", "experience"),
    ("/skills/", "Skills", "skills"),
    ("/research/", "Research", "research"),
    ("/contact/", "Contact", "contact"),
    ("/resume.pdf", "Resume (PDF) \u2197", "resume"),
]
STATIC = Path(__file__).parent / "static"


@dataclass
class BuildReport:
    """Problems found while building: errors stop the build, warnings are only printed."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _date_range(start: str, end: str | None) -> str:
    """Format a start and end date for the website, e.g. "Oct 2025 – present"."""

    def short(d: str) -> str:
        """Abbreviate the month name to three letters."""
        text = format_date(d)
        parts = text.split(" ")
        return f"{parts[0][:3]} {parts[1]}" if len(parts) == 2 else text

    if end is None:
        return f"{short(start)} – present"
    if start == end:
        return short(start)
    return f"{short(start)} – {short(end)}"


def _environment() -> Environment:
    """Create the Jinja2 environment with the helper functions the templates use."""
    env = Environment(
        loader=PackageLoader("portfolio", "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.globals.update(
        inline=lambda text: Markup(markdown.render_inline(text)),
        block=lambda text: Markup(markdown.render_block(text)),
        year=lambda d: format_date(d, month=False),
        month=format_date,
        daterange=_date_range,
        venue=lambda v: v.removeprefix("In: "),
    )
    return env


def ordered_projects(content: Content, *, drafts: bool) -> list[tuple[object, list[Project]]]:
    """Projects grouped by category in config.yaml order, newest first; hidden ones only for drafts."""
    groups = []
    for category in content.site.categories:
        items = [p for p in content.projects.values() if p.data.category == category.id and (p.visible or drafts)]
        items.sort(key=lambda p: (date_key(p.data.date), p.data.title), reverse=True)
        if items:
            groups.append((category, items))
    return groups


def _source_url(content: Content, repository: str | None, private: bool) -> str | None:
    """The public GitHub URL of a repository, or None if there is none or it is private."""
    if not repository or private:
        return None
    return f"{content.profile.links.github.rstrip('/')}/{repository}"


def _write(path: Path, text: str) -> None:
    """Write a generated file, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_site(content: Content, out: Path, *, drafts: bool = False) -> BuildReport:
    """Render every page into out/ (which is emptied first) and return the problems found."""
    report = BuildReport()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in STATIC.iterdir():
        shutil.copy2(f, out / f.name)
    card = social.card(content.profile.name, content.profile.headline, urlsplit(content.site.url).netloc)
    (out / "og-image.png").write_bytes(card)

    env = _environment()
    groups = ordered_projects(content, drafts=drafts)
    listed = [p for _, items in groups for p in items]
    with_pages = [p for p in listed if p.page]
    shown_keys = {p.key for p in listed}
    skill_names = content.skill_names()
    work = sorted(
        (e for e in content.experience.values() if e.data.type == "work"),
        key=lambda e: date_key(e.data.start),
        reverse=True,
    )
    education = sorted(
        (e for e in content.experience.values() if e.data.type == "education"),
        key=lambda e: date_key(e.data.start),
        reverse=True,
    )

    common = {
        "site": content.site,
        "profile": content.profile,
        "nav": NAV,
        "drafts": drafts,
        "updated": format_date(dt.date.today().strftime("%Y-%m")),
    }

    site_url = content.site.url.rstrip("/")
    descriptions = content.site.descriptions
    meta: list[seo.PageSeo] = []

    def ld(*items: dict[str, object] | list[dict[str, object]]) -> str:
        """Structured data (JSON-LD) for a page, from one or more schema.org items."""
        flat = [x for item in items for x in (item if isinstance(item, list) else [item])]
        return seo.to_json(flat)

    def crumbs(*trail: tuple[str, str]) -> dict[str, object]:
        """A breadcrumb trail from the home page down to the given (name, path) pairs."""
        return seo.breadcrumbs([("Home", site_url + "/"), *[(n, site_url + path) for n, path in trail]])

    def page(
        template: str,
        path: str,
        section: str,
        title: str,
        description: str | None = None,
        *,
        jsonld: str | None = None,
        og_type: str = "website",
        **extra: object,
    ) -> None:
        """Render one template to the file for a site path such as /projects/.

        title is the page's own title: the <title> adds the site name and is kept short enough for search
        results, while the page's <h1> and the social preview keep the full text.
        """
        if path == "/":
            tag = og_title = content.site.home_title
        else:
            tag = seo.title_tag(title, name)
            og_title = f"{title} · {name}"
        desc = description or content.site.description
        html = env.get_template(template).render(
            **common,
            section=section,
            path=path,
            page_title=tag,
            og_title=og_title,
            og_type=og_type,
            jsonld=jsonld,
            description=desc,
            **extra,
        )
        if path != "/404.html":
            meta.append(seo.PageSeo(path, tag, desc))
        target = out / path.lstrip("/")
        if path.endswith("/"):
            target = target / "index.html"
        _write(target, html)

    name = content.profile.name

    # Home
    featured = [content.projects[key] for key in content.site.website.featured]
    profile_links = [content.profile.links.github, content.profile.links.linkedin]
    page(
        "home.html",
        "/",
        "home",
        name,
        jsonld=ld(seo.home_graph(name, site_url, content.profile.headline, profile_links, work, education)),
        featured=featured,
        project_count=len(listed),
        work=work,
        education=education,
        publications=content.publications,
    )

    # Projects list and one page per project
    page(
        "projects.html",
        "/projects/",
        "projects",
        "Projects",
        descriptions.get("projects"),
        jsonld=ld(crumbs(("Projects", "/projects/"))),
        groups=groups,
    )
    categories = {c.id: c for c in content.site.categories}
    for i, p in enumerate(with_pages):
        body, render_env = markdown.render_page(p.body, p.path.relative_to(content.root), p.dir)
        report.errors += render_env.errors
        report.warnings += render_env.warnings
        for asset in p.dir.rglob("*"):
            if asset.is_file() and asset.name != "index.md":
                dest = out / "projects" / p.key / asset.relative_to(p.dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, dest)
        page(
            "project.html",
            f"/projects/{p.key}/",
            "projects",
            p.data.title,
            seo.description(p.data.summary),
            jsonld=ld(crumbs(("Projects", "/projects/"), (p.data.title, f"/projects/{p.key}/"))),
            og_type="article",
            p=p,
            category=categories[p.data.category],
            source=_source_url(content, p.data.repository, p.data.private),
            body=Markup(body),
            built_with=[(s, skill_names[s]) for s in p.data.skills],
            prev=with_pages[i - 1] if i > 0 else None,
            next=with_pages[i + 1] if i + 1 < len(with_pages) else None,
        )

    # Experience
    page(
        "experience.html",
        "/experience/",
        "experience",
        "Experience",
        descriptions.get("experience"),
        jsonld=ld(crumbs(("Experience", "/experience/"))),
        work=work,
        education=education,
        certifications=content.certifications,
    )

    # Skills, each linked to the shown projects and the jobs that used it
    evidence: dict[str, list[tuple[str, str]]] = {sid: [] for sid in skill_names}
    for e in work + education:
        for sid in e.data.skills:
            evidence[sid].append((f"/experience/#{e.key}", e.data.organisation.split(" – ")[0]))
    for p in with_pages:
        for sid in p.data.skills:
            evidence[sid].append((f"/projects/{p.key}/", p.data.title.split(":")[0]))
    for t in content.theses:
        if t.page:
            for sid in t.skills:
                evidence[sid].append((f"/research/{t.key}/", "Master's thesis"))
    page(
        "skills.html",
        "/skills/",
        "skills",
        "Skills",
        descriptions.get("skills"),
        jsonld=ld(crumbs(("Skills", "/skills/"))),
        groups=content.skills.groups,
        evidence=evidence,
    )

    # Research
    def shown(key: str | None) -> Project | None:
        """The project with this key if it has a page on this build, else None."""
        p = content.projects.get(key) if key else None
        return p if p and p.key in shown_keys and p.page else None

    degrees = {e.key: e for e in education}
    page(
        "research.html",
        "/research/",
        "research",
        "Research",
        descriptions.get("research"),
        jsonld=ld(crumbs(("Research", "/research/"))),
        publications=content.publications,
        theses=[(t, degrees[t.degree]) for t in content.theses],
    )

    def research_page(entry: object, template: str, structured: dict[str, object], **extra: object) -> None:
        """Render the page of a paper or thesis from the Markdown body of its index.md, and copy its images."""
        entry_dir = content.root / "content" / "research" / entry.key
        body, render_env = markdown.render_page(
            entry.body, (entry_dir / "index.md").relative_to(content.root), entry_dir
        )
        report.errors += render_env.errors
        report.warnings += render_env.warnings
        for asset in entry_dir.rglob("*"):
            if asset.is_file() and asset.name != "index.md":
                dest = out / "research" / entry.key / asset.relative_to(entry_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, dest)
        path = f"/research/{entry.key}/"
        page(
            template,
            path,
            "research",
            entry.title,
            seo.description(entry.summary),
            jsonld=ld(structured, crumbs(("Research", "/research/"), (entry.title, path))),
            og_type="article",
            body=Markup(body),
            **extra,
        )

    # One page per paper and thesis that has text below its frontmatter
    for pub in content.publications:
        if pub.page:
            thesis = next((t for t in content.theses if t.key == pub.thesis and t.page), None)
            structured = seo.paper_graph(pub, f"{site_url}/research/{pub.key}/", name, site_url)
            research_page(pub, "publication.html", structured, pub=pub, project=shown(pub.project), thesis=thesis)
    for t in content.theses:
        if t.page:
            structured = seo.thesis_graph(t, degrees[t.degree], f"{site_url}/research/{t.key}/", name, site_url)
            research_page(
                t,
                "thesis.html",
                structured,
                t=t,
                degree=degrees[t.degree],
                source=_source_url(content, t.repository, t.private),
                built_with=[(sid, skill_names[sid]) for sid in t.skills],
            )

    # Standalone Markdown pages such as contact.md
    for key, path in content.pages.items():
        body, render_env = markdown.render_page(
            path.read_text(encoding="utf-8"), path.relative_to(content.root), path.parent, allow_h1=True
        )
        report.errors += render_env.errors
        report.warnings += render_env.warnings
        label = key.replace("-", " ").capitalize()
        page(
            "page.html",
            f"/{key}/",
            key,
            label,
            descriptions.get(key),
            jsonld=ld(crumbs((label, f"/{key}/"))),
            body=Markup(body),
        )

    page("404.html", "/404.html", "", "Page not found")
    report.warnings += seo.warnings_for(meta)

    # Sitemap: every published page, with the date its source files last changed
    def rel(p: Path) -> str:
        """A path inside the repository, as Git wants it."""
        return str(p.relative_to(content.root))

    entries: list[tuple[str, list[str]]] = [
        ("/", ["content/index.md", "content/config.yaml"]),
        ("/projects/", ["content/projects", "content/config.yaml"]),
        ("/experience/", ["content/experience", "content/certifications.yaml"]),
        ("/skills/", ["content/skills.yaml"]),
        ("/research/", ["content/research"]),
    ]
    entries += [(f"/{k}/", [rel(path)]) for k, path in content.pages.items()]
    entries += [(f"/projects/{p.key}/", [rel(p.dir)]) for p in with_pages if p.visible]
    entries += [
        (f"/research/{e.key}/", [f"content/research/{e.key}"])
        for e in [*content.publications, *content.theses]
        if e.page
    ]
    lines = []
    for url, sources in entries:
        modified = seo.last_modified(content.root, sources)
        stamp = f"<lastmod>{modified}</lastmod>" if modified else ""
        lines.append(f"  <url><loc>{content.site.url}{url}</loc>{stamp}</url>")
    sitemap = "\n".join(lines)
    _write(
        out / "sitemap.xml",
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n',
    )
    _write(out / "robots.txt", f"User-agent: *\nSitemap: {content.site.url}/sitemap.xml\n")
    return report
