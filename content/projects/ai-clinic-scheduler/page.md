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
