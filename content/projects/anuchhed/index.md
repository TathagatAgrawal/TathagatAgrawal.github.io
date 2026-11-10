---
title: "Anuchhed: citation-first Q&A over the Constitution of India"
date: 2026-11
category: llm
repository: constitution-rag
private: true
skills: [rag, embeddings, llm-evaluation, langgraph, llm-apis, prompt-engineering, fastapi, databases, web-frontend, python]

summary: >-
  Ask anything about the Constitution of India and every statement in the answer cites the exact
  Article, clause or amendment it comes from, with quotes verified against the official text.
result: >-
  On a 70-question development set, 97% of answers behaved correctly (against 87% when the same
  model answered from memory and 71% for naive RAG), and every quote shown matched the official
  text exactly.
status: In progress

resume:
  tech: Python, LangGraph, FastAPI, Gemini API, Qwen3 embeddings, SQLite FTS5
  bullets:
    - 'Built **citation-first Q&A** over the Constitution of India: the official PDF parsed into a provision tree with amendment history, and **hybrid retrieval** (reference lookup, BM25, dense embeddings, cross-encoder reranking) chosen through an eight-configuration ablation.'
    - Every statement cites its provision and every quote is **verified against the official text**; on a 70-question development set, 97% correct behaviour versus 87% answering from memory and 71% for naive RAG, with 100% exact quotes.
  short: citation-first RAG over the Constitution of India with verified quotes
---

## The problem

General-purpose chatbots answer legal questions fluently but cite loosely or not at all. For a constitution, a wrong Article number, a repealed provision presented as current, or a paraphrase passed off as a quote is worse than no answer. Anuchhed answers questions about the Constitution of India so that every statement can be checked against the official text.

## What I built

- **A corpus with provenance.** The Legislative Department's official edition (as on 10 September 2026, including the 106th Amendment) is parsed into a tree of Articles, clauses, Schedules and amendment history, stored in SQLite. The source PDF is pinned by URL and checksum, so a changed upstream file fails the build instead of being ingested silently.
- **Hybrid retrieval.** Direct reference lookup ("Article 21A"), BM25 keyword search, local dense embeddings (Qwen3-Embedding-0.6B) and a cross-encoder reranker, compared in an eight-configuration ablation.
- **Verified answers.** The model drafts an answer in which every statement cites a provision; a verifier checks each citation and quote against the official text and repairs or removes anything that doesn't match. A LangGraph conversation layer handles follow-up questions.
- **A deterministic evaluation.** Gold questions record which provisions a correct answer must rest on and which facts it must contain; the evaluator refuses to run if a gold fact isn't actually in the cited text.

## Results so far

Deterministic reference lookup is the largest single retrieval gain for every search method:

| Retrieval configuration | Recall@5 | MRR |
| --- | ---: | ---: |
| BM25 | 0.787 | 0.733 |
| Lookup + BM25 | 0.897 | 0.784 |
| Dense embeddings | 0.843 | 0.765 |
| Lookup + dense | 0.963 | 0.871 |
| Hybrid (lookup + BM25 + dense) | 0.937 | 0.872 |
| Lookup + dense + reranker | 0.957 | 0.868 |

Whole answers, compared with the same model answering from memory and with a naive RAG baseline:

| System | Right behaviour | Key facts | Citation recall | Quotes exact |
| --- | ---: | ---: | ---: | ---: |
| Anuchhed | 97% | 95% | 95% | 100% |
| Same model, no retrieval | 87% | 89% | 87% | 64% |
| Naive RAG (embedding search, plain prompt) | 71% | 78% | 78% | 70% |

Answering from memory is a strong baseline on well-known questions, but it fails exactly where retrieval matters: it doesn't know the 106th Amendment came into force in April 2026, and only 64% of its quotes match the official text.

## Status and limits

Ingestion, retrieval and verified answers work end to end, including follow-up questions. The numbers above come from a development set of 70 questions that I drafted with an AI assistant and have not yet reviewed against the text, so they are indicative rather than final. A locked test set of about 250 questions and the deployment come next.

*Independent educational project. Not legal advice.*
