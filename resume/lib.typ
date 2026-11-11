// Shared resume layout. It lays out one resume from the data that src/portfolio/resume_data.py builds
// (the sections, jobs, projects, papers and skill lines of that resume, with dates formatted and every
// piece of Markdown already converted to Typst markup), so it never reads the content files itself.
// Build with `uv run resume <name>`; the data arrives as the `data` input.

#let markup(s) = eval(s, mode: "markup")

// A bullet is either a string or a mapping with `text` and nested `bullets`.
#let bullet-list(items) = list(..items.map(b => {
  if type(b) == str { markup(b) } else { [#markup(b.text) #list(..b.bullets.map(markup))] }
}))

// The two-line header used by every entry: bold title and date on top, italic details below.
#let entry-head(title, subtitle, right-top, right-bottom) = grid(
  columns: (auto, 1fr),
  align: (left, right),
  [#text(weight: "bold")[#title]\ #text(style: "italic")[#subtitle]],
  [#text(weight: "bold")[#right-top]\ #text(style: "italic")[#right-bottom]],
)

// A link with the given text, or nothing if there is no address.
#let link-or-none(l) = if l != none { link(l.url)[#l.text] }

#let resume(model, doc) = {
  // Sizes come from the resume's `layout:` in content/config.yaml, written as Typst lengths ("0.4in").
  let size(key, default) = if key in model.layout { eval(model.layout.at(key)) } else { default }
  let margin = size("margin", 0.5in)
  let gap = size("gap", 0.625em)
  let name-size = size("name-size", 20pt)
  let font-size = size("font-size", 10pt)
  let heading-size = size("heading-size", 12pt)
  // The font family (or families to try in order); without one Typst's default text font is used.
  let font = model.layout.at("font", default: none)
  // The theme color: a hex color ("#0b5cad") or one of Typst's color names (navy, teal, ...), already checked in Python.
  let accent = if "accent" in model.layout {
    let c = model.layout.accent
    if c.starts-with("#") { rgb(c) } else { eval(c) }
  } else { blue }

  set document(title: model.name + " – Resume", author: model.name)
  set page(paper: "a4", margin: margin, numbering: none)
  set par(justify: true, spacing: gap, leading: gap)
  set text(size: font-size)
  set text(font: font) if font != none
  set terms(separator: text(weight: "bold", ": "), spacing: gap)
  set list(spacing: gap, tight: true)
  show heading.where(level: 1): it => {
    v(-0.125em)
    text(size: heading-size, fill: accent, it)
    v(-1.05em)
    line(length: 100%, stroke: accent)
  }
  show link: it => text(fill: accent, underline(it))

  // Name and contact links.
  let header-links = model.links.map(l => if "url" in l { link(l.url)[#l.text] } else { l.text })
  grid(
    columns: (1fr, 1fr),
    align: (left + bottom, right + bottom),
    text(weight: "bold", size: name-size, fill: accent)[#model.name],
    text(weight: "bold")[#header-links.join([ ~|~ ])],
  )
  v(0.25 * gap)
  line(length: 100%, stroke: accent)

  // Work experience and education entries share one layout.
  let entries(items) = for (i, e) in items.enumerate() {
    entry-head(e.title, e.subtitle, e.when, e.place)
    if e.bullets.len() > 0 { bullet-list(e.bullets) }
    if i < items.len() - 1 { v(gap) }
  }

  for section in model.sections {
    let kind = section.kind
    if kind == "summary" {
      markup(section.text)
    } else if kind == "skills" {
      heading(level: 1)[Technical Skills]
      for l in section.lines { terms.item(l.label, l.skills) }
    } else if kind == "experience" {
      heading(level: 1)[Work Experience]
      entries(section.entries)
    } else if kind == "education" {
      heading(level: 1)[Education]
      entries(section.entries)
    } else if kind == "projects" {
      heading(level: 1)[Projects]
      for (i, p) in section.entries.enumerate() {
        entry-head(p.title, p.tech, p.date, link-or-none(p.link))
        if p.bullets.len() > 0 { bullet-list(p.bullets) }
        if i < section.entries.len() - 1 or section.others.len() > 0 { v(gap) }
      }
      if section.others.len() > 0 {
        [*Other projects:*]
        list(..section.others.map(o => {
          let title = text(weight: "bold", o.title)
          [#if o.url != none { link(o.url, title) } else { title } (#o.details): #markup(o.short)]
        }))
      }
    } else if kind == "publications" {
      heading(level: 1)[Publications]
      for (i, pub) in section.items.enumerate() {
        let link-text = if pub.url != none { link(pub.url)[#pub.url_label] }
        let note = if pub.note != none { [. #markup(pub.note)] }
        [#text(weight: "bold")[[#(pub.number)]] #pub.cite #link-text#note]
        if i < section.items.len() - 1 { v(0.3 * gap) }
      }
    } else if kind == "certifications" {
      heading(level: 1)[Certifications]
      for (i, c) in section.entries.enumerate() {
        entry-head(c.title, c.issuer, c.date, if c.url != none { link(c.url)[Certificate link] })
        if i < section.entries.len() - 1 { v(gap) }
      }
    } else {
      panic("unknown resume section " + repr(kind))
    }
  }
  doc
}
