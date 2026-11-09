## What it does

Upload an academic paper as a PDF. Three independent LLM "reviewers", each reading through a different lens (methodology, novelty, clarity), answer a fixed set of review questions and back every answer with quotes from the paper. A "chair" agent then reconciles the panel into an executive summary, a per-question consensus and an overall triage signal, and says explicitly where the reviewers disagree instead of quietly averaging their views.

## How it works

- **Ingestion:** the PDF is parsed and mapped into sections, with metadata extracted.
- **Reviewers and chair:** structured output validated with Pydantic schemas (which double as the LLM's response schema), using the Gemini API's free tier through a provider-agnostic client.
- **Grounding check:** a deterministic check flags any answer whose quoted evidence can't be found in the paper text. It is independent of the model and free to run.
- **Fault isolation:** if one reviewer fails (timeout, quota, malformed output), the chair works with whoever succeeded and reports who is missing.
- **Output:** results are saved per paper, keyed by a hash of its content, as JSON and as a Markdown report downloadable from the Streamlit interface.
- **Tests:** the test suite runs without any live model calls.
