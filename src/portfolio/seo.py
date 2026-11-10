"""Search-engine helpers: titles and descriptions of a sensible length, structured data, sitemap dates.

- `title_tag` and `description` keep the text that search results show within the length they display, so
  nothing is cut off in the middle of a word.
- The `*_graph` functions build schema.org structured data (JSON-LD) from the content files, so search
  engines can tell that this is a person's site and which pages are papers.
- `last_modified` gives the sitemap the date each page's source files last changed, from Git.
- `warnings_for` reports pages whose title or description is missing, badly sized or a duplicate.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import markdown
from .content import Experience, Publication, Thesis

TITLE_LIMIT = 60
DESCRIPTION_LIMIT = 155  # search results show about 160 characters
DESCRIPTION_MIN = 70


def plain_text(text: str) -> str:
    """Turn a line of inline Markdown into plain text (no formatting, no tags), for a meta description."""
    rendered = markdown.render_inline(text)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", rendered))).strip()


def shorten(text: str, limit: int) -> str:
    """Cut text to at most limit characters at a word boundary, ending with an ellipsis if it was cut."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-–—(")
    return cut + "…"


def title_tag(title: str, site_name: str) -> str:
    """The <title> of a page: "Title · Name" if that fits in 60 characters, else the title alone, shortened."""
    full = f"{title} · {site_name}"
    if len(full) <= TITLE_LIMIT:
        return full
    return shorten(title, TITLE_LIMIT)


def description(markdown_text: str) -> str:
    """A meta description made from a summary: plain text, cut at a word boundary."""
    return shorten(plain_text(markdown_text), DESCRIPTION_LIMIT)


def _me(content_name: str, site_url: str) -> dict[str, str]:
    """The site owner as a schema.org Person, for use as an author."""
    return {"@type": "Person", "name": content_name, "url": site_url}


def _is_owner(author: str, name: str) -> bool:
    """True when a citation-style author ("Agrawal T") is the site owner ("Tathagat Agrawal")."""
    parts = name.split()
    return len(parts) >= 2 and author.strip() == f"{parts[-1]} {parts[0][0]}"


def breadcrumbs(trail: list[tuple[str, str]]) -> dict[str, object]:
    """A schema.org BreadcrumbList for a trail of (name, address) pairs, from the home page down."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url} for i, (name, url) in enumerate(trail, 1)
        ],
    }


def home_graph(
    name: str, site_url: str, headline: str, links: list[str], work: list[Experience], education: list[Experience]
) -> list[dict[str, object]]:
    """Structured data for the home page: the website, and the person it is about."""
    person: dict[str, object] = {
        "@type": "Person",
        "@id": f"{site_url}/#person",
        "name": name,
        "url": site_url,
        "description": headline,
        "sameAs": links,
    }
    current = next((e for e in work if e.data.end is None), None)
    if current:
        person["jobTitle"] = current.data.role
        person["worksFor"] = {"@type": "Organization", "name": current.data.organisation.split(" – ")[0]}
    if education:
        person["alumniOf"] = {"@type": "CollegeOrUniversity", "name": education[0].data.organisation}
    site = {
        "@type": "WebSite",
        "@id": f"{site_url}/#website",
        "name": name,
        "url": site_url,
        "inLanguage": "en",
        "publisher": {"@id": f"{site_url}/#person"},
    }
    return [site, person]


def paper_graph(pub: Publication, page_url: str, owner: str, site_url: str) -> dict[str, object]:
    """Structured data for a paper's page: a ScholarlyArticle with its authors, venue and DOI."""
    data: dict[str, object] = {
        "@type": "ScholarlyArticle",
        "headline": pub.title,
        "url": page_url,
        "mainEntityOfPage": page_url,
        "datePublished": str(pub.year),
        "inLanguage": "en",
        "author": [
            _me(owner, site_url) if _is_owner(a, owner) else {"@type": "Person", "name": a} for a in pub.authors
        ],
        "isPartOf": {"@type": "CreativeWork", "name": pub.venue.removeprefix("In: ")},
    }
    if pub.summary:
        data["description"] = plain_text(pub.summary)
    if pub.url:
        data["sameAs"] = pub.url
        doi = re.match(r"https?://(?:dx\.)?doi\.org/(.+)$", pub.url)
        if doi:
            data["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": doi.group(1)}
    return data


def thesis_graph(thesis: Thesis, degree: Experience, page_url: str, owner: str, site_url: str) -> dict[str, object]:
    """Structured data for a thesis page: a schema.org Thesis, with its author and university."""
    data: dict[str, object] = {
        "@type": "Thesis",
        "name": thesis.title,
        "url": page_url,
        "mainEntityOfPage": page_url,
        "inLanguage": "en",
        "author": _me(owner, site_url),
        "sourceOrganization": {"@type": "CollegeOrUniversity", "name": degree.data.organisation},
        "description": plain_text(thesis.summary),
    }
    if degree.data.end:
        data["datePublished"] = degree.data.end[:4]
    return data


def to_json(items: list[dict[str, object]]) -> str:
    """The text of a JSON-LD script: schema.org items in one @graph, safe to put inside a <script> tag."""
    text = json.dumps({"@context": "https://schema.org", "@graph": items}, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/").replace("<!--", "<\\!--")


def last_modified(root: Path, paths: list[str]) -> str | None:
    """The date (YYYY-MM-DD) these files last changed, or None if Git can't say.

    Files with uncommitted changes count as changed today. In a shallow clone every file shows the date of
    the one commit that was fetched, so the publishing workflow fetches the full history.
    """

    def git(*args: str) -> str | None:
        """Run a Git command in the repository and return its output, or None if it fails."""
        try:
            done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            return None
        return done.stdout.strip()

    dirty = git("status", "--porcelain", "--", *paths)
    if dirty is None:
        return None
    if dirty:
        return dt.date.today().isoformat()
    return git("log", "-1", "--format=%cs", "--", *paths) or None


@dataclass
class PageSeo:
    """What search engines see of one page."""

    path: str
    title: str
    description: str


def warnings_for(pages: list[PageSeo]) -> list[str]:
    """Report pages with a missing or badly sized description, or a title or description used twice."""
    out: list[str] = []
    for key, label in (("title", "title"), ("description", "description")):
        seen: dict[str, str] = {}
        for page in pages:
            value = getattr(page, key)
            if value in seen:
                out.append(
                    f"{page.path}: the {label} is the same as on {seen[value]}; search engines want each page to differ"
                )
            seen.setdefault(value, page.path)
    for page in pages:
        if not page.description:
            out.append(f"{page.path}: no meta description")
        elif len(page.description) > DESCRIPTION_LIMIT + 5:
            out.append(
                f"{page.path}: the meta description is {len(page.description)} characters; search results cut it off after about 160"
            )
        elif len(page.description) < DESCRIPTION_MIN:
            out.append(
                f"{page.path}: the meta description is only {len(page.description)} characters; about 70 to 160 works best"
            )
        if len(page.title) > TITLE_LIMIT:
            out.append(
                f"{page.path}: the title is {len(page.title)} characters; search results cut it off after about 60"
            )
    return out
