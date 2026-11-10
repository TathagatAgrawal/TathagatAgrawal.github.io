"""Render the social preview image (shown when a link to the site is shared) from the profile.

The card is drawn with Typst and its bundled fonts, so it looks the same on every machine and always
shows the current name and headline from content/index.md.
"""

from __future__ import annotations

import typst

WIDTH, HEIGHT = 1200, 630

_SOURCE = b"""
#set page(width: 1200pt, height: 630pt, margin: 90pt, fill: rgb("#ffffff"))
#set text(fill: rgb("#111111"), font: "Libertinus Serif")
#set par(leading: 0.6em)
#let given = sys.inputs
#align(horizon, stack(
  dir: ttb,
  spacing: 52pt,
  text(size: 84pt, weight: "bold")[#given.name],
  text(size: 42pt, fill: rgb("#5c5c5c"))[#given.headline],
  text(size: 30pt, fill: rgb("#5c5c5c"))[#given.site],
))
"""


def card(name: str, headline: str, site: str) -> bytes:
    """Return a 1200x630 PNG with the name, headline and web address of the site."""
    png = typst.compile(
        _SOURCE,
        format="png",
        ppi=72.0,
        ignore_system_fonts=True,
        sys_inputs={"name": name, "headline": headline, "site": site},
    )
    assert isinstance(png, bytes)  # one page gives one image
    return png
