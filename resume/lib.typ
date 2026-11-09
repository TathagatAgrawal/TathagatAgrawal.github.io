// Shared resume layout. Each resume file (general.typ, ml.typ, quant.typ) only lists what goes in it;
// every word comes from the YAML files in content/. Compile from the repository root so that
// /content resolves, e.g.  typst compile --root . resume/ml.typ
//
// Text under a `resume:` key in the YAML files is Typst markup (*bold*, _italic_, \@ ...).
// Shared fields (titles, organisations, dates) are plain text.

#let months = (
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
)

// "2026-09" -> "September 2026"; "2025" -> "2025".
#let fmt-date(d) = {
  if d == none { return none }
  let s = str(d)
  if s.len() == 4 { s } else { months.at(int(s.slice(5, 7)) - 1) + " " + s.slice(0, 4) }
}

// A start and end date as shown on the resume. No end date means the role is current.
#let fmt-range(start, end) = {
  if end == none { fmt-date(start) + " – Present" }
  else if str(start) == str(end) { fmt-date(start) }
  else { fmt-date(start) + " – " + fmt-date(end) }
}

#let markup(s) = eval(s, mode: "markup")

// The first value unless it is none.
#let either(a, b) = if a == none { b } else { a }

// The `resume:` part of an entry with the overrides for this variant applied on top.
#let merged(part, variant) = {
  let out = part
  let v = part.at("variants", default: (:)).at(variant, default: none)
  if v != none {
    for (k, val) in v { out.insert(k, val) }
  }
  out
}

#let load-project(key) = {
  let p = yaml("/content/projects/" + key + "/project.yaml")
  if p.at("resume", default: none) == none {
    panic("content/projects/" + key + "/project.yaml has no resume: part, so it can't go on a resume")
  }
  p
}

#let load-experience(key) = {
  let e = yaml("/content/experience/" + key + ".yaml")
  if e.at("resume", default: none) == none {
    panic("content/experience/" + key + ".yaml has no resume: part, so it can't go on a resume")
  }
  e
}

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

#let resume(
  variant: "default",
  // Section keys in display order: summary, experience, projects, publications, skills,
  // education, certifications.
  sections: (),
  experience: (),
  education: (),
  projects: (),
  other-projects: (),
  margin: 0.5in,
  gap: 0.625em,
  name-size: 20pt,
  font-size: 10pt,
  accent: blue,
  doc,
) = {
  let profile = yaml("/content/profile.yaml")
  let github-user = profile.links.github.split("/").last()

  set document(title: profile.name + " – Resume", author: profile.name)
  set page(paper: "a4", margin: margin, numbering: none)
  set par(justify: true, spacing: gap, leading: gap)
  set text(size: font-size)
  set terms(separator: text(weight: "bold", ": "), spacing: gap)
  set list(spacing: gap, tight: true)
  show heading.where(level: 1): it => {
    v(-0.125em)
    text(size: 12pt, fill: accent, it)
    v(-1.05em)
    line(length: 100%, stroke: accent)
  }
  show link: it => text(fill: accent, underline(it))

  // Name and contact links.
  let header-links = profile.resume.at("header_links", default: ("email", "github", "linkedin")).map(k => {
    if k == "email" { profile.email }
    else if k == "github" { link(profile.links.github)[GitHub] }
    else if k == "linkedin" { link(profile.links.linkedin)[LinkedIn] }
    else if k == "website" { link(profile.links.website)[Website] }
  })
  grid(
    columns: (1fr, 1fr),
    align: (left + bottom, right + bottom),
    text(weight: "bold", size: name-size, fill: accent)[#profile.name],
    text(weight: "bold")[#header-links.join([ ~|~ ])],
  )
  v(0.25 * gap)
  line(length: 100%, stroke: accent)

  let project-link(p, r) = {
    if p.at("repository", default: none) != none and not p.at("private", default: false) {
      link("https://github.com/" + github-user + "/" + p.repository)[GitHub]
    } else if r.at("link", default: none) != none {
      link(r.link.url)[#r.link.label]
    }
  }

  for section in sections {
    if section == "summary" {
      markup(merged(profile.resume, variant).summary)
    } else if section == "skills" {
      heading(level: 1)[Technical Skills]
      let skills = yaml("/content/skills.yaml").resume
      let lines = skills.at("variants", default: (:)).at(variant, default: skills.default)
      for l in lines { terms.item(l.label, l.skills) }
    } else if section == "experience" {
      heading(level: 1)[Work Experience]
      for (i, key) in experience.enumerate() {
        let e = load-experience(key)
        let r = merged(e.resume, variant)
        entry-head(either(r.at("title", default: none), e.role), e.organisation, fmt-range(e.start, e.at("end", default: none)), e.at("location", default: none))
        if r.bullets.len() > 0 { bullet-list(r.bullets) }
        if i < experience.len() - 1 { v(gap) }
      }
    } else if section == "education" {
      heading(level: 1)[Education]
      for (i, key) in education.enumerate() {
        let e = load-experience(key)
        let r = merged(e.resume, variant)
        let loc = e.at("location", default: none)
        let place = if loc != none { e.organisation + ", " + loc } else { e.organisation }
        entry-head(either(r.at("title", default: none), e.role), place, fmt-range(e.start, e.at("end", default: none)), e.at("grade", default: none))
        if r.bullets.len() > 0 { bullet-list(r.bullets) }
        if i < education.len() - 1 { v(gap) }
      }
    } else if section == "projects" {
      heading(level: 1)[Projects]
      for (i, key) in projects.enumerate() {
        let p = load-project(key)
        let r = merged(p.resume, variant)
        entry-head(either(r.at("title", default: none), p.title), r.at("tech", default: none), fmt-date(p.date), project-link(p, r))
        if r.bullets.len() > 0 { bullet-list(r.bullets) }
        if i < projects.len() - 1 or other-projects.len() > 0 { v(gap) }
      }
      if other-projects.len() > 0 {
        [*Other projects:*]
        list(..other-projects.map(key => {
          let p = load-project(key)
          let r = merged(p.resume, variant)
          let title = text(weight: "bold", either(r.at("title", default: none), p.title))
          let url = if p.at("repository", default: none) != none and not p.at("private", default: false) {
            "https://github.com/" + github-user + "/" + p.repository
          }
          let details = (r.at("tech", default: none), fmt-date(p.date)).filter(x => x != none).join(", ")
          [#if url != none { link(url, title) } else { title } (#details): #markup(r.at("short", default: ""))]
        }))
      }
    } else if section == "publications" {
      heading(level: 1)[Publications]
      let pubs = yaml("/content/publications.yaml")
      for (i, pub) in pubs.enumerate() {
        let r = pub.at("resume", default: (:))
        let cite = pub.authors.join(", ") + " (" + str(pub.year) + ") " + r.at("title", default: pub.title) + ". " + pub.venue + "."
        let url = pub.at("url", default: none)
        let note = r.at("note", default: none)
        [#text(weight: "bold")[[#(i + 1)]] #cite #if url != none { link(url)[#pub.at("url_label", default: "Paper link")] }#if note != none { [. #markup(note)] }]
        if i < pubs.len() - 1 { v(0.3 * gap) }
      }
    } else if section == "certifications" {
      heading(level: 1)[Certifications]
      let certs = yaml("/content/certifications.yaml")
      for (i, c) in certs.enumerate() {
        entry-head(c.title, c.issuer, fmt-date(c.date), if c.at("url", default: none) != none { link(c.url)[Certificate link] })
        if i < certs.len() - 1 { v(gap) }
      }
    } else {
      panic("unknown resume section " + repr(section))
    }
  }
  doc
}
