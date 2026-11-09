// One-page general resume. Published on the website as /resume.pdf.
// Build: uv run resume general    Live preview: typst watch --root . resume/general.typ
#import "lib.typ": resume

#show: resume.with(
  variant: "general",
  sections: ("summary", "skills", "experience", "projects", "publications", "education"),
  experience: ("neural-nurture",),
  projects: ("agentic-eval-framework", "ai-clinic-scheduler", "strategy-backtester"),
  other-projects: ("unet-segmentation", "stellar-classification"),
  education: ("vit-bhopal",),
  margin: 0.4in,
  gap: 0.45em,
)
