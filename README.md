# Portfolio website and resume

My portfolio website and my resumes, generated from one set of content files. Every project, job, skill and paper is written once in `content/`; a small Python script builds the website from it, and Typst builds the resume PDFs from the same files.

- Website: `https://tathagatagrawal.github.io` (published by GitHub Actions once this repository is public)
- Resumes: `resume/general.typ` (one page, published as `/resume.pdf`), `resume/ml.typ`, `resume/quant.typ`

## Quick start

Requires [uv](https://docs.astral.sh/uv/). Typst is installed by uv as a Python package; the `typst` command line is only needed for live resume previews.

```sh
uv run build --serve          # build the site, serve it at http://localhost:8000, rebuild on every save
uv run build --serve --drafts # the same, including projects marked hidden (for reviewing them)
uv run build                  # check everything and build the site into _site/
uv run resume                 # build all resumes to resume/*.pdf (or: uv run resume ml)
typst watch --root . resume/ml.typ   # live preview of one resume while editing
uv run pytest                 # tests
```

Run this once per clone so a broken build or a phone number can never be committed:

```sh
git config core.hooksPath .githooks
```

## Where things live

```
content/
  profile.yaml            name, email, links, home-page intro, resume summary
  site.yaml               project groups, featured count, which resume is published
  skills.yaml             website Skills page (with ids) and the resume's skills lines
  publications.yaml       papers
  certifications.yaml
  experience/<key>.yaml   one file per job or degree
  projects/<key>/         one folder per project:
    project.yaml            facts shared by website and resume, plus website and resume text
    page.md                 the project's web page (Markdown)
    figures/                images used by page.md
    results/                CSV files used by page.md
  pages/contact.md        the Contact page
resume/
  lib.typ                 resume layout (shared by every resume)
  general.typ, ml.typ, quant.typ   which sections, jobs and projects each resume shows
src/portfolio/            the website builder (templates, stylesheet, checks)
private/                  gitignored: cover letters, application notes, tailored resumes
```

A project's **key** is its folder name. It is the website address (`content/projects/trade-filter-ml/` becomes `/projects/trade-filter-ml/`) and the name a resume uses to include it.

## Text formats

| Where | Format |
| --- | --- |
| Shared fields (title, dates, organisation, links) | Plain text. Dates are `2026-08` or `2026` |
| `website:` fields and `page.md` | Markdown: `**bold**`, `*italic*`, `[link](https://...)`, `## Heading`, `- list` |
| `resume:` fields | Typst markup, as before: `*bold*`, `_italic_`, `NDCG\@3`, `\[1\]` |

**YAML pitfall:** a list item that starts with `*` or contains a colon followed by a space must be wrapped in single quotes, with any `'` inside doubled: `- '*Fine-tuned LLMs* using SFT: it''s fast.'`. Long text can also go in a folded block, which needs no quoting:

```yaml
summary: >-
  Any text here, over as many lines as you like: colons, *stars* and 'quotes' are all fine.
```

The build explains the problem, naming the file and line, if you forget.

## Adding a project

1. Copy a project folder that is similar (for example `content/projects/strategy-backtester/`) and rename it; the new folder name is the project's key.
2. Edit `project.yaml`:

   ```yaml
   title: My Project
   date: 2026-12                  # when it was done (YYYY-MM)
   category: llm                  # a group id from content/site.yaml: llm, quant, tools, ml, research, practice
   repository: my-project         # GitHub repository name; leave out if there is none
   private: true                  # true while the repository is private; the page then says "walkthrough on request"
   skills: [rag, fastapi, python] # ids from content/skills.yaml
   links:                         # optional extra links shown under the title
     - label: Report
       url: https://...

   website:                       # leave this whole part out for a resume-only project
     summary: One or two sentences for the Projects list and under the title.
     result: The outcome in one sentence, shown in bold near the top. Optional.
     status: Complete             # e.g. In progress; shown on the page, and in lists unless Complete
     featured: false              # true puts it on the home page (at most 3)
     hidden: false                # true keeps it off the published site

   resume:                        # leave this whole part out for a website-only project
     tech: Python, FastAPI, ...
     bullets:
       - Built a *thing* that does X, improving Y by *40%*.
     short: one-liner used when the project is listed under "Other projects"
     variants:                    # optional: different wording for one resume
       general:
         bullets:
           - A shorter version for the one-page resume.
   ```

3. Write `page.md` in Markdown. Don't add a `#` title; it comes from `project.yaml`. A good shape is `## The problem`, `## What I built`, `## Result`, `## What I learned` (or `## Limits`).
4. Put the project on a resume (optional): add its key to `projects:` (or `other-projects:` on the one-page resume) in `resume/general.typ`, `ml.typ` or `quant.typ`.
5. Run `uv run build --serve`, check the page, commit and push.

## Figures and tables

**Figures:** put the image in the project's `figures/` folder and add it to `page.md` on a line of its own:

```markdown
![What the figure shows, for screen readers](figures/holdout-lift.png "The caption shown under it.")
```

- Figures are numbered automatically ("Figure 1."). Alt text is required.
- Images 1,000 pixels or wider (and wide SVGs) extend beyond the text column so their labels stay readable; smaller ones stay in the column. Clicking a figure opens it full size.
- For a figure that should change with dark mode, add `holdout-lift.dark.png` beside it; it is picked up automatically.
- PNG, JPEG, WebP or SVG. Keep files under about 500 KB (the build warns above that).

**Small tables:** ordinary Markdown tables.

```markdown
| Model | F1 |
| --- | ---: |
| mBERT | 0.946 |
```

**Result tables from CSV:** put the CSV in `results/` and add a `table` block. Only `file` is required.

````markdown
```table
file: results/holdout.csv
caption: Holdout results.
columns:                 # which columns, in order, with their headings
  scope: Strategy
  expectancy_diff: Change in R
format:                  # Python format strings
  expectancy_diff: "{:+.3f}"
labels:                  # replace raw values
  bb_rsi: Bollinger + RSI fade
```
````

## Common edits

| I want to... | Do this |
| --- | --- |
| Edit a project's web page | Edit `content/projects/<key>/page.md` |
| Edit a project's resume bullets | Edit `resume:` in `content/projects/<key>/project.yaml` |
| Show or hide a project on the website | Set `website.hidden` in its `project.yaml` |
| Change the featured projects | Set `website.featured: true` on up to three projects |
| Make a repository's link appear | Set `private: false` once the GitHub repository is public |
| Add or change a job | Edit or copy a file in `content/experience/`; list its key under `experience:` in the resume files |
| Add a skill | Add it to a group in `content/skills.yaml`, then add its id to the projects and jobs that used it. The Skills page links them automatically |
| Change the resume's skills lines | Edit `resume:` at the bottom of `content/skills.yaml` |
| Add a paper | Add an entry to `content/publications.yaml` (it appears on the website and every resume) |
| Change the headline or email | Edit `content/profile.yaml` |
| Change a resume's sections, order or projects | Edit `resume/general.typ`, `ml.typ` or `quant.typ` |
| Make a resume for one application | Copy `resume/ml.typ` to `private/resumes/<company>.typ`, change the lists, build with `typst compile --root . private/resumes/<company>.typ` |
| Change the Contact page | Edit `content/pages/contact.md` |
| Add another standalone page | Add `content/pages/<name>.md` (it is served at `/<name>/`) |

## What the build checks

`uv run build` stops with a clear message (file, line or field) if:

- a YAML file has a syntax error, a misspelt field, or a date that isn't `YYYY` or `YYYY-MM`;
- a project or job lists a skill id that doesn't exist (it suggests the closest one), or a project's category isn't in `site.yaml`;
- more projects are featured than `featured_count` allows;
- a figure or CSV file is missing, a figure has no alt text, or a table names a column the CSV doesn't have;
- any resume fails to compile (for example it lists a project that has no `resume:` part);
- any link or image on the generated site points to a page or file that doesn't exist;
- a file that would be committed contains something that looks like a phone number, or anything in `private/` is tracked by Git.

## Publishing

Every push to `main` runs `.github/workflows/publish.yml`: it builds the site and the general resume, runs the tests, and deploys to GitHub Pages. GitHub Pages is free only for public repositories, so while this repository is private the deploy step is skipped and the workflow only checks the build.

To go live:

1. Make the repository public (**Settings → General → Change visibility**).
2. **Settings → Pages → Source: GitHub Actions**.
3. Push any commit (or re-run the workflow). The site appears at `https://tathagatagrawal.github.io`.
4. Add `website` to `header_links` in `content/profile.yaml` to put the site's link on the resumes.

## Privacy

Phone number and street address are never written anywhere in this repository; the resumes show email, GitHub and LinkedIn only. `private/` is gitignored, and the build plus the pre-commit hook refuse to proceed if a phone number appears in any file that would be committed.
