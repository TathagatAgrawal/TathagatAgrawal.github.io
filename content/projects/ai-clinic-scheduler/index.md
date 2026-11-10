---
title: AI Clinic Scheduler (first version)
date: 2026-08
category: llm
repository: ai_clinic_scheduler
skills: [agents, langgraph, langchain, rag, embeddings, llm-apis, pydantic, fastapi, web-frontend, python]

summary: >-
  An LLM agent that talks with a patient, matches their symptoms to a doctor with RAG over
  specialty descriptions and doctor bios, and books the appointment.
status: Superseded by Clinic Agent

resume:
  title: AI Clinic Scheduler
  tech: LangGraph, LangChain, FastAPI, Pydantic, ChromaDB, Sentence-Transformers, OpenRouter, HTML/JS
  bullets:
    - Built an LLM-powered appointment scheduling agent using a LangGraph ReAct agent to hold multi-turn conversations, interpret patient symptoms, and recommend a doctor via retrieval-augmented generation over a knowledge base of specialties and bios.
    - Implemented a RAG-based doctor-matching pipeline with Sentence-Transformers embeddings persisted in a Chroma vector store, exposed to the agent as a callable retriever tool.
    - Designed explicit Pydantic schemas for every tool call so malformed arguments from less-reliable models surface as correctable errors instead of crashing the agent.
    - Built a FastAPI backend serving patient chat, doctor/slot lookups, and admin endpoints, alongside a no-build-step HTML/JS frontend for patient booking and a receptionist admin view.
  variants:
    general:
      tech: LangGraph, LangChain, FastAPI, Pydantic, ChromaDB, Sentence-Transformers, OpenRouter
      bullets:
        - Built an LLM-powered scheduling agent (LangGraph ReAct) that interprets patient symptoms and recommends a doctor via RAG over specialties and bios (Sentence-Transformers embeddings, Chroma vector store, callable retriever tool).
        - Defined Pydantic schemas for every tool call so malformed arguments surface as correctable errors; built a FastAPI backend (chat, doctor/slot lookups, admin) and a no-build-step HTML/JS frontend for booking and receptionist admin.
  short: LangGraph agent that matches symptoms to doctors with RAG and books appointments
---

## What it does

A patient chats with an assistant, describes their symptoms, and gets a doctor recommendation with a stated reason before choosing a time slot and booking. Instead of making the patient pick from a static list of doctors, the agent searches a knowledge base of specialty descriptions and doctor bios and recommends the best match.

## How it works

- **Agent:** a LangGraph ReAct agent decides when to call tools during the conversation. Every tool's arguments are validated with an explicit Pydantic schema, so a malformed call from a less reliable model becomes a correctable error instead of a crash.
- **Doctor matching:** specialty descriptions and doctor bios are embedded with a local Sentence-Transformers model and stored in a Chroma vector store; the agent queries it through a retriever tool.
- **Model:** any OpenRouter chat model, by default a free Llama 3.3 70B.
- **Data:** patients, doctors, slots and appointments are plain CSV files, seeded with synthetic data on first run.
- **App:** a FastAPI backend and a plain HTML/JavaScript front end with a patient chat (showing real availability beside it) and a receptionist view.

## What came next

Building this showed the limits of letting an agent drive the whole flow: it can diagnose, choose a specialist on weak evidence, or book without checks. The [second version](/projects/clinic-agent/) keeps AI to intake and routing and gives safety and booking to deterministic code.
