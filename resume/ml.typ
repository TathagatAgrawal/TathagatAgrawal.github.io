// Two-page resume for ML, NLP and LLM roles.
// Build: uv run resume ml    Live preview: typst watch --root . resume/ml.typ
#import "lib.typ": resume

#show: resume.with(
  variant: "ml",
  sections: ("summary", "experience", "publications", "skills", "education", "projects", "certifications"),
  experience: ("neural-nurture", "finlatics"),
  projects: (
    "agentic-eval-framework",
    "ai-clinic-scheduler",
    "mbert-ner",
    "strategy-backtester",
    "stellar-classification",
    "unet-segmentation",
  ),
  education: ("vit-bhopal",),
)
