# Portfolio website and resume

My portfolio website and my resumes, generated from one set of content files. Every project, job, skill and paper is written once in `content/`, as one Markdown file each; a small Python script builds the website from it, and the same script prepares the data that Typst lays out as the resume PDFs.

- Website: `https://tathagatagrawal.github.io` (published by GitHub Actions once this repository is public)
- Resumes: `general` (one page, published as `/resume.pdf`), `ml` and `quant`, all defined in `content/config.yaml`

## Quick start

Requires [uv](https://docs.astral.sh/uv/). Typst is installed by uv as a Python package, so nothing else is needed.

```sh
uv run build --serve          # build the site, serve it at http://localhost:8000, rebuild on every save
uv run build --serve --drafts # the same, including projects not listed in the config (for reviewing them)
uv run build                  # check everything and build the site into _site/
uv run resume                 # build all resumes to resume/*.pdf, which are kept in Git (or: uv run resume ml)
uv run resume --copy-to DIR   # ...and copy them, under their own names, into DIR (see Resume PDFs)
uv run resume ml --watch      # rebuild resume/ml.pdf on every save, for a live preview
uv run pytest                 # tests
```

While serving, saving a content, resume or template file rebuilds the site; saving a Python file restarts the server by itself (if the new code doesn't import, the old code keeps running and the error is printed). A build that fails keeps serving the previous site and prints the error.

Run this once per clone so a broken build or a phone number can never be committed:

```sh
git config core.hooksPath .githooks
```

## Where things live

```
content/
  index.md                the profile: name, email, links, headline, resume summary (frontmatter) and the home-page intro (body)
  config.yaml             THE file that decides what appears where: which projects the website shows and features, and what each resume contains
  skills.yaml             the website's Skills page (with ids) and the resume's skill lines
  certifications.yaml
  experience/<key>.yaml   one file per job or degree
  research/<key>/         one folder per paper or thesis (its page is /research/<key>/):
    index.md                frontmatter: citation, link, summary; body: a brief overview with the results
    figures/                images used by the page
  projects/<key>/         one folder per project:
    index.md                frontmatter: facts, the website summary and the resume text; body: the project's web page
    figures/                images used by the page
    results/                CSV files used by the page
  pages/contact.md        the Contact page
resume/
  resume.typ, lib.typ     the resume layout; the content comes from src/portfolio/resume_data.py
  general.pdf, ml.pdf, quant.pdf   the built resumes, kept in Git (`uv run resume` rewrites them)
src/portfolio/            the website builder, the resume data builder, templates, stylesheet and checks
private/                  gitignored: cover letters, application notes, tailored resumes
```

Each `.md` file starts with a block of YAML between two `---` lines (the **frontmatter**: the facts and short texts), followed by Markdown (the **body**: the web page). Everything is written once: the website uses it as it is, and for the resumes the build applies each resume's overrides and converts the text to Typst.

A **key** is a folder or file name. It is the website address (`content/projects/trade-filter-ml/` becomes `/projects/trade-filter-ml/`) and the name a resume uses to include it (jobs and degrees: the file name without `.yaml`).

## Text formats

| Where | Format |
| --- | --- |
| Titles, dates, organisations, `tech` lines, a project's `status`, skill lines | Plain text. Dates are `2026-08` or `2026` |
| `summary`, `result`, and every bullet (jobs, projects, papers, resumes), `short`, `note` | One line of inline Markdown: bold, italic, code and links |
| `status` in `content/index.md` | A short Markdown block |
| The body of `index.md` files, `content/index.md` and `content/pages/*.md` | Full Markdown (see below) |

The full syntax, and the few things that work differently in resume text, is in [Markdown syntax](#markdown-syntax).

**YAML pitfall:** a list item that starts with `*` or contains a colon followed by a space must be wrapped in single quotes, with any `'` inside doubled: `- '*Fine-tuned LLMs* using SFT: it''s fast.'`. Long text can also go in a folded block, which needs no quoting:

```yaml
summary: >-
  Any text here, over as many lines as you like: colons, *stars* and 'quotes' are all fine.
```

The build explains the problem, naming the file and line, if you forget.

## Adding a project

1. Copy a project folder that is similar (for example `content/projects/strategy-backtester/`) and rename it; the new folder name is the project's key.
2. Edit `index.md`. The frontmatter comes first, the page below it:

   ```markdown
   ---
   title: My Project
   date: 2026-12                  # when it was done (YYYY-MM)
   category: llm                  # a group id from content/config.yaml: llm, quant, tools, ml, practice
   repository: my-project         # GitHub repository name; leave out if there is none
   private: true                  # true while the repository is private; the page then says "walkthrough on request"
   skills: [rag, fastapi, python] # ids from content/skills.yaml
   links:                         # optional extra links shown under the title
     - label: Report
       url: https://...

   summary: One or two sentences for the Projects list and under the title.
   result: The outcome in one sentence, shown in bold near the top. Optional.
   status: Complete               # e.g. In progress; shown on the page, and in lists unless Complete

   resume:                        # leave this whole part out for a project that is not on any resume
     tech: Python, FastAPI, ...
     bullets:
       - Built a **thing** that does X, improving Y by **40%**.
     short: one-liner used when the project is listed under "Other projects"
     variants:                    # optional: different wording for one resume
       general:
         bullets:
           - A shorter version for the one-page resume.
   ---

   ## The problem

   The web page, in Markdown.
   ```

3. Write the page below the frontmatter. Don't add a `#` title; it comes from the frontmatter. A good shape is `## The problem`, `## What I built`, `## Result`, `## What I learned` (or `## Limits`).
4. Show it (optional): add its key to `website.projects` in `content/config.yaml` to publish its page, to `website.featured` to put it on the home page, and to `projects:` (or `other_projects:`) under the resumes that should list it. Until you list it, it is hidden from the published site and appears only in `--drafts` builds.
5. Run `uv run build --serve`, check the page, commit and push.

## Jobs and degrees

A job or degree (`content/experience/<key>.yaml`) is written once and used by the website and every resume:

```yaml
type: work                        # work or education
role: Applied Scientist
organisation: Neural Nurture
start: 2025-10
summary: One line for the home page.

bullets:                          # shown on the website and on every resume
  - Built a **recommender** that improved NDCG@3 by 40%.
  - text: A bullet with sub-bullets underneath.
    bullets:
      - The first sub-bullet.

website:                          # optional: only if the website should say something different
  bullets:
    - A shorter version for the website.

resume:                           # optional: only if resumes should say something different
  title: Shorter title for resumes
  bullets:                        # replaces the shared bullets on every resume
    - ...
  variants:
    general:                      # replaces them on the resume called general only
      bullets:
        - ...
```

For one resume the bullets come from the first of: that resume's `variants` entry, `resume.bullets`, `bullets`. The website uses `website.bullets` if there is one, otherwise `bullets`. Delete an override to go back to the shared text.

## Skills and resume skill lines

`content/skills.yaml` has two parts. `groups` is the website's Skills page: each skill has an id, and projects and jobs list the ids they used. `resume_lines` is the resume's "Technical Skills" section: each line (a label and plain text) is written once under an id, and a resume lists the ids of the lines it shows, in order, under `skills:` in `content/config.yaml`. To show a line under a different label on one resume, write `- {line: dev-tools, label: Developer Tools}` there.

The resume lines name specific tools (OpenCV, Azure ML, Cursor...), while the Skills page lists capabilities, so the two are separate lists on purpose.

## Markdown syntax

Pages are written in Markdown: [CommonMark](https://commonmark.org/) plus tables, strikethrough, figures and CSV tables. This section lists everything the build understands.

### Which kind of page

| Page | Where it is written | Notes |
| --- | --- | --- |
| Project, paper and thesis pages | Below the frontmatter of `index.md` | Start with `##` headings. A `#` title is an error, because the title comes from the frontmatter |
| Home page intro | Below the frontmatter of `content/index.md` | A few paragraphs; the headline is `headline:` in the frontmatter |
| Standalone pages such as Contact | `content/pages/<name>.md`, served at `/<name>/` | No frontmatter. Start with your own `# Title`: the only place `#` is allowed |

Short texts in the frontmatter (`summary`, `result`, bullets) are a single line of inline Markdown: no paragraphs, lists or headings.

### Text

| You write | You get |
| --- | --- |
| `**bold**`, `*italic*`, `***both***` | **bold**, *italic*, ***both*** |
| `` `code` `` | `code` |
| `~~strikethrough~~` | ~~strikethrough~~ (page text only) |
| `\*not italic\*` | A backslash before a Markdown character shows the character itself |
| `&nbsp;` | A non-breaking space: the words on each side stay on one line. Other entities work too (`&amp;`, `&copy;`) |
| `## Heading`, `### Subheading` | Headings. There is no `#` (see above) and headings get no automatic anchors |
| A blank line | Starts a new paragraph. Lines inside a paragraph are joined, so write each paragraph as one long line |
| Two spaces or a `\` at the end of a line | A line break inside a paragraph |
| `- item` or `1. item` | Bulleted or numbered list; indent the next level by two spaces |
| `> quote` | A block quote |
| `---` on its own line, with blank lines around it | A horizontal rule (safe inside the body; only the first `---` pair of the file is the frontmatter) |
| ```` ```python ```` ... ```` ``` ```` | A code block; the language after the opening fence is optional |

Typography is automatic: `--` becomes an en dash (3--5 gives 3–5), `---` an em dash, `...` an ellipsis, straight quotes become curly quotes, and `(c)` and `+-` become © and ±.

### Links

| You write | Notes |
| --- | --- |
| `[text](https://example.com)` | An external link. `<https://example.com>` also works; a bare URL is not turned into a link |
| `[text](mailto:me@example.com)` | An email link |
| `[Anuchhed](/projects/anuchhed/)` | A page on this site: write the path from the site root. The paths are `/projects/<key>/`, `/research/<key>/`, `/experience/`, `/skills/`, `/research/`, `/projects/`, `/contact/` |
| `[the degree](/experience/#vit-bhopal)` | A place on a page: `/experience/#<job key>`, `/skills/#<skill id>`, `/projects/#<category id>` |
| `[results](results/holdout.csv)` | A file next to the page. Everything in the page's folder except `index.md` is published beside it |
| `[Resume](/resume.pdf)` | Any link to a `.pdf` opens in a new tab |

The build stops if a link or an image points to a page or file that doesn't exist (the part after `#` is not checked).

### Figures

Put the image in the page's `figures/` folder and write it on a line of its own:

```markdown
![What the figure shows, for screen readers](figures/holdout-lift.png "The caption shown under it.")
```

- It becomes a numbered figure ("Figure 1."). The alt text is required, the image must exist in the page's folder, and a web address is not allowed.
- The caption is the quoted title. Leave it out for a figure without a caption.
- Images 1,000 pixels or wider (and wide SVGs) extend beyond the text column so their labels stay readable; smaller ones stay in the column. Clicking a figure opens it full size.
- For a figure that should change with dark mode, add `holdout-lift.dark.png` beside it; it is picked up automatically. A figure without a dark version is dimmed in dark mode so a white plot doesn't glare.
- PNG, JPEG, WebP or SVG. Keep files under about 500 KB (the build warns above that). Prefer lossless WebP for charts: about half the size of the PNG with identical pixels (`uv run python -c "from PIL import Image; Image.open('a.png').save('a.webp', lossless=True)"`).
- An image in the middle of a sentence is an ordinary inline image: no number, no caption and no alt text check.

### Tables

An ordinary Markdown table. A colon in the divider row aligns a column:

```markdown
| Model | F1 |
| :--- | ---: |
| mBERT | 0.946 |
```

A table built from a CSV file: put the CSV in `results/` and add a `table` block. The block is YAML and only `file` is required. These tables are numbered ("Table 1.") and numeric columns are right-aligned.

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

### Raw HTML

HTML tags in a page pass through unchanged (`<br>`, `<kbd>Ctrl</kbd>`, `<details>`), and the build does not check them. Use them sparingly, and not in text that also goes on a resume.

### Not supported

Footnotes (`[^1]`), task lists (`- [ ]`), definition lists, maths, and automatic links for bare URLs. They are not errors: they come out as plain text or as broken links, so don't use them.

### Resume text

The text of a resume (bullets, `short`, `note`, the profile summary) is converted from Markdown to Typst by the build.

- Supported: `**bold**`, `*italic*`, `` `code` ``, `[links](https://...)`, `&nbsp;` and backslash escapes. The characters Typst treats specially (`@ $ # ~ _ *` and so on) are escaped for you, so write `NDCG@3` and `$5` plainly.
- A single `~` is a tilde. For a non-breaking space write `&nbsp;`.
- An image or raw HTML in resume text is an error that names the file and bullet.
- `~~strikethrough~~` and the other page-only syntax is not interpreted: it is printed as typed.
- Resume text is one paragraph per bullet: line breaks are joined into spaces, and `--`, `...` and straight quotes become Typst's dashes, ellipses and curly quotes just as on the website.

## Common edits

| I want to... | Do this |
| --- | --- |
| Edit a project's web page | Edit the text below the frontmatter in `content/projects/<key>/index.md` |
| Edit a project's resume bullets | Edit `resume.bullets` in the frontmatter of `content/projects/<key>/index.md` (`resume.variants.<name>` for one resume) |
| Show or hide a project on the website | Add or remove its key under `website.projects` in `content/config.yaml` |
| Change the featured projects, or how many | Edit `website.featured` in `content/config.yaml` (the list is the home page, in order) |
| Make a repository's link appear | Set `private: false` once the GitHub repository is public |
| Add or change a job | Edit or copy a `.yaml` file in `content/experience/` (see Jobs and degrees); list its key under `experience:` in the resumes in `content/config.yaml` |
| Say something different on the website and on the resumes | In the job's file, add `website.bullets` or `resume.bullets`; delete them to share the text again |
| Add a skill | Add it to a group in `content/skills.yaml`, then add its id to the projects and jobs that used it. The Skills page links them automatically |
| Change a resume's skills lines | Edit `resume_lines` at the bottom of `content/skills.yaml`, and the resume's `skills:` list in `content/config.yaml` |
| Add a thesis | Add `content/research/<key>/index.md` like a paper, but with `kind: thesis`, `title`, `degree:` (the key of its education entry in `content/experience/`, which supplies the degree, university and year) and `summary`. Papers that came from it say `thesis: <key>` |
| Add a paper | Add `content/research/<key>/index.md`: citation and summary in the frontmatter, a brief overview and results below it (figures and tables work as on project pages, with images in a `figures/` folder beside it). It gets a page at `/research/<key>/`; list its key under `publications:` in each resume in `content/config.yaml` that should show it |
| Change the headline or email | Edit the frontmatter of `content/index.md`; the intro paragraph is its body. The preview image shown when the site is shared (`/og-image.png`) is drawn from your name and headline at every build, so it follows along |
| Change a resume's sections, order, jobs, projects or papers | Edit its entry under `resumes:` in `content/config.yaml` (lists are in display order, so the length is the count) |
| Change a resume's margins or sizes | Add `layout:` to its entry, e.g. `layout: { margin: 0.4in, gap: 0.45em, name_size: 16pt, font_size: 10pt }` |
| Add a resume | Add an entry under `resumes:` in `content/config.yaml` (with a `filename`); `uv run resume <name>` builds it, and `website.resume` picks the one published as `/resume.pdf` |
| Get the resumes on my phone | `uv run resume --copy-to` an iCloud Drive folder (see Resume PDFs) |
| Make a resume for one application | Add an entry to `resumes:` with a neutral name (the config is committed, so keep company names out of it), build it with `uv run resume <name>`, and delete the entry afterwards. Save the PDF in `private/` |
| Change the Contact page | Edit `content/pages/contact.md` |
| Add another standalone page | Add `content/pages/<name>.md` (it is served at `/<name>/`) |

## What the build checks

`uv run build` stops with a clear message (file, line or field) if:

- a frontmatter block or YAML file has a syntax error, a misspelt field, or a date that isn't `YYYY` or `YYYY-MM`;
- a project, job or thesis lists a skill id that doesn't exist (it suggests the closest one), or a project's category isn't in `config.yaml`;
- `config.yaml` names a project, job or paper that doesn't exist (it suggests the closest key), features a project that isn't shown, puts a degree under experience, lists a section with nothing under it, lists a skill line that doesn't exist, or has a layout size without a unit;
- a figure or CSV file is missing, a figure has no alt text, or a table names a column the CSV doesn't have;
- any resume fails to build, for example because a bullet contains an image or raw HTML, which a resume can't show;
- any link or image on the generated site points to a page or file that doesn't exist;
- a file that would be committed contains something that looks like a phone number, or anything in `private/` is tracked by Git.

It only warns (the site still builds) about search-engine problems: a page with no meta description, one under 70 or over about 160 characters, or two pages with the same title or description.

## Resume PDFs

`uv run resume` builds every resume to `resume/<name>.pdf`. These PDFs **are committed to Git**, so GitHub always holds the current resumes. Commit them whenever the content changes:

```sh
uv run resume                 # rebuild the PDFs
git add resume && git commit  # keep them in the repository
```

A PDF records the date it was made, so a rebuild would normally change every file. To avoid that, a resume is rebuilt with the date already inside the existing PDF: if the result is identical the file is left alone, and the date only moves forward when the content really changed. `uv run build --check` (and the pre-commit hook) warns when a committed PDF no longer matches the content, so you are reminded to rebuild it.

**A copy on your phone.** `--copy-to DIR` also writes each PDF into a folder you choose, named by `filename` in its entry in `content/config.yaml` (for example `Tathagat Agrawal - Resume (ML).pdf`, which is what a recruiter sees when you send it). Point it at a folder in iCloud Drive and the files appear on your iPhone in the Files app:

```sh
uv run resume --copy-to "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Resumes"
```

To do this on every run, put the folder in an environment variable once, in `~/.zshrc`, and run plain `uv run resume`:

```sh
export RESUME_COPY_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Resumes"
```

The folder (`Resumes`) is created if its parent exists, and a file is only rewritten when it changed, so iCloud isn't made to re-upload identical PDFs. A symlink would not work here: iCloud stores a link as a path on your Mac, which your phone can't follow, so the real files have to live in iCloud.

## Search engines (SEO)

**The build does this for you:**

- A `<title>` of at most 60 characters on every page: "Page · Name" when that fits, otherwise the page title alone, cut at a word. The page's own heading and the social preview keep the full text.
- A `<meta description>` on every page, cut at a word near 155 characters, as plain text. Projects, papers and the thesis use their `summary`; the other pages use `descriptions` in `content/config.yaml`.
- Structured data (JSON-LD, schema.org): a `Person` and `WebSite` on the home page (your name, job, university and profile links), a `ScholarlyArticle` with authors and DOI for each paper, a `Thesis`, and breadcrumbs on every other page. It is built from the content files, so it can't disagree with the pages.
- A sitemap with the date each page's files last changed (from Git history), a `robots.txt` that points to it, a canonical address on every page, and `noindex` on the 404 page.
- A social preview image drawn from your name and headline, and `og:type` set to `article` for projects and papers.

**What you write:**

- `home_title` in `content/config.yaml`: the home page's title. Keep it to about 60 characters and put your name first.
- `descriptions` in the same file: one unique sentence of 70 to 160 characters for each of projects, experience, skills, research and contact.
- A clear `summary` on every project, paper and thesis, since it becomes the description search results show. Don't reuse a sentence between pages.
- The full name `Tathagat Agrawal` in the text of the home page, so that searches for your name match the page itself.

**After the site is live** (nothing can appear in search results before that):

1. Add the site in [Google Search Console](https://search.google.com/search-console) and [Bing Webmaster Tools](https://www.bing.com/webmasters) and submit `https://tathagatagrawal.github.io/sitemap.xml`. Search Console's verification file (`google….html`) lives in `src/portfolio/static/`, which the build copies to the site's root; don't delete it, because Google re-checks it.
2. Link to the site from the places search engines already trust: the website field of your GitHub and LinkedIn profiles, Hugging Face, each repository's README, and your papers' publisher pages. Links from other sites are what make a site appear when someone searches your name.
3. Check a page with Google's [Rich Results Test](https://search.google.com/test/rich-results) and [PageSpeed Insights](https://pagespeed.web.dev/).

## Publishing

Every push to `main` runs `.github/workflows/publish.yml` (which fetches the full Git history, for the sitemap's dates): it builds the site and the general resume, runs the tests, and deploys to GitHub Pages. GitHub Pages is free only for public repositories, so while this repository is private the deploy step is skipped and the workflow only checks the build.

To go live:

1. Make the repository public (**Settings → General → Change visibility**).
2. **Settings → Pages → Source: GitHub Actions**.
3. Push any commit (or re-run the workflow). The site appears at `https://tathagatagrawal.github.io`.
4. Add `website` to `header_links` in `content/index.md` to put the site's link on the resumes.

## Privacy

Phone number and street address are never written anywhere in this repository; the resumes show email, GitHub and LinkedIn only. `private/` is gitignored, and the build plus the pre-commit hook refuse to proceed if a phone number appears in any file that would be committed.
