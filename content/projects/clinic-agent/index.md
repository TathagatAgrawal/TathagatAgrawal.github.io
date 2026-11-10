---
title: "Clinic Agent: AI-assisted appointment scheduling"
date: 2026-10
category: llm
repository: clinic-agent
private: true
skills: [embeddings, scikit-learn, calibration, experiment-design, llm-apis, prompt-engineering, llm-evaluation, fastapi, databases, testing, web-frontend, python]

summary: >-
  Patients describe their concern and get real appointment options with a suitable doctor. AI
  assists with intake and routing; deterministic code owns safety and booking, and everything
  works with the LLM switched off.
result: >-
  On 218 held-out cases, the trained department classifier chose an acceptable department 97.2%
  of the time with no wrong-specialist choices, against 85.3% and 8 wrong specialists for the
  hand-tuned router it replaced.
status: Complete (version 1)

resume:
  tech: Python, FastAPI, PostgreSQL, scikit-learn, fastembed, Gemini API
  bullets:
    - 'Built a clinic scheduling system where **AI assists but never decides**: LLM intake summaries and a trained department router, with deterministic code owning red-flag safety checks, availability and booking; the full flow works with the LLM off.'
    - Replaced a hand-tuned similarity router with a **calibrated classifier** on local embeddings; on 218 held-out cases it chose an acceptable department **97.2% vs 85.3%**, with **0 vs 8** wrong-specialist routings.
    - Hardened the app for real use (Argon2id passwords, CSRF protection, rate limits, append-only audit log, identifier scrubbing before any LLM call) with tests for concurrent bookings and authorization on every route.
  short: AI-assisted clinic scheduling with a calibrated department router (97.2% acceptable on held-out cases)
---

## The problem

A patient writes a few words ("my left hand keeps going numb and tingly") and needs appointment times with a suitable doctor. Doing that with an LLM is easy to demo and hard to trust: a model that diagnoses, picks the wrong specialist or writes to the schedule directly is a liability. This project draws a hard line: AI assists with intake and routing, but never diagnoses, never makes a clinical decision and never writes to the database.

This is the second, rebuilt version of my [first AI clinic scheduler](https://github.com/TathagatAgrawal/ai_clinic_scheduler), which let a LangGraph agent drive the whole conversation.

## What I built

- **Patient flow:** a short intake form, an optional clarifying question, and up to three real appointment options with a suitable doctor. Staff manage the schedule from a dashboard; admins manage doctors, hours and leave.
- **Safety first:** emergency wording is caught by deterministic red-flag rules before any routing. The LLM only writes summaries, and its output is treated as untrusted.
- **Department routing:** a small, calibrated classifier on local embeddings (BAAI/bge-base) plus the patient's age band. It picks a specialist only when confident; otherwise the patient goes to General Medicine, the clinic's normal first stop. A similarity router runs as an automatic fallback.
- **Booking:** a single module owns all writes to appointments, with database constraints that make double-booking impossible, and tested reschedule and cancellation rules.
- **Security:** Argon2id passwords, server-side sessions, CSRF tokens, lockout and rate limits, strict content security policy, an append-only audit log that never contains symptom text, and scrubbing of identifiers before any text reaches an LLM.

## Result

I compared the original hand-tuned similarity router with the trained classifier on 218 held-out cases, written before any of this round's training and evaluated once, and on two perturbed copies of them (typos, and the concern wrapped in chatty text).

![Three bar charts comparing the similarity router and two classifiers on clean, typo and chatty held-out cases: acceptable choice, share sent to General Medicine, and wrong-specialist rate. The bge-base classifier is best on all three.](figures/heldout-comparison.webp "Routers on the 218 held-out cases and two perturbed copies. The bge-base classifier (green) is now the default.")

| Held-out, 218 cases | Similarity router | Classifier (bge-small) | Classifier (bge-base, adopted) |
| --- | ---: | ---: | ---: |
| Acceptable department | 85.3% | 93.1% | **97.2%** |
| Sent to General Medicine | 55.5% | 52.8% | **47.2%** |
| Wrong specialist | 3.7% (8) | 0.0% | **0.0%** |

Tuning the classifier's own settings made almost no difference; a larger embedding model was the only change with real headroom.

## Limits

The routing data is synthetic, written by one author, and has not been reviewed by a clinician, so the held-out set is independent in content but not in style. The choice of bge-base was made after the first look at the held-out results. Version 1 has no multi-factor authentication for staff and no email or SMS notifications.
