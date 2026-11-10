---
title: Legal document Q&A with RAG
date: 2025-07
category: llm
repository: RAG_DSL
skills: [rag, embeddings, langchain, llm-apis, prompt-engineering, python]

summary: >-
  Ingests a legal PDF, extracts its key concepts, generates question-answer pairs about them, and
  answers natural-language questions from a command line.
status: Complete

resume:
  title: RAG-Based Legal AI Assistant
  tech: LangChain, Sentence-Transformers, OpenRouter, Python
  bullets:
    - Built a RAG-based legal-AI agent using LangChain and HuggingFace embedding models to answer questions about legal documents.
    - Developed LLM prompt templates to extract top legal concepts and automatically generate focused Q&A pairs.
    - Created dual in-memory vector stores, one for source chunks and one for Q&A pairs, enabling fast cosine-similarity searches.
    - Built a CLI that orchestrates retrieval, LLM inference, and response delivery with logging and a "not legal advice" disclaimer.
  short: RAG assistant for legal PDFs with generated Q&A pairs as a second index
---

## What it does

Point it at a legal PDF (the example is India's Model Tenancy Act) and ask questions in plain English at a command-line prompt. Every answer ends with a reminder that it is not legal advice.

## How it works

1. **Ingestion:** the PDF is split into overlapping chunks of 1,000 characters with 200 characters of overlap.
2. **Index:** chunks are embedded with the `all-MiniLM-L6-v2` Sentence-Transformer and stored in an in-memory vector index.
3. **Concept extraction:** an LLM lists the five most important legal concepts in the document.
4. **Generated Q&A:** for each concept the LLM writes one focused question and answer, which go into a second index.
5. **Answering:** a question retrieves the closest passages from both indexes, and the LLM (Mistral Small 3.2 through OpenRouter) answers from that combined context. Every exchange is logged.

## What I learned

The second index of generated Q&A pairs helps with questions phrased differently from the statute, but it also shows the limit of simple chunk retrieval: asked to define sub-letting, the assistant correctly said the retrieved excerpts didn't define it and pointed to the sections that might. Precise legal answers need retrieval that understands the document's structure, which is what my later [Anuchhed](/projects/anuchhed/) project does.
