// Two-page resume for quantitative research and trading roles.
// Build: uv run resume quant    Live preview: typst watch --root . resume/quant.typ
#import "lib.typ": resume

#show: resume.with(
  variant: "quant",
  sections: ("summary", "experience", "publications", "skills", "education", "projects", "certifications"),
  experience: ("neural-nurture", "finlatics"),
  projects: (
    "strategy-backtester",
    "ai-clinic-scheduler",
    "mbert-ner",
    "stellar-classification",
    "unet-segmentation",
    "crop-disease",
  ),
  education: ("vit-bhopal",),
  name-size: 16pt,
)
