---
title: Agentic Eval Framework
date: 2026-09
category: llm
repository: agentic-eval-framework
skills: [llm-evaluation, agents, langgraph, langchain, llm-apis, pydantic, databases, testing, python]
links:
  - label: Comparison report
    url: https://github.com/TathagatAgrawal/agentic-eval-framework/blob/main/report/report.md

summary: >-
  Scores any LLM agent on six deterministic metrics with no LLM-as-judge, demonstrated on four
  interchangeable agent architectures.
result: >-
  The metrics separate the four designs clearly: for example 100% against 50% groundedness, and
  tool-call efficiency from 17% to 100%. No architecture wins on every metric.
status: Complete

resume:
  tech: Python, Gemini API, LangGraph, LangChain, SQLite, Pydantic
  bullets:
    - Built an architecture-agnostic evaluation framework scoring agentic LLM systems on six deterministic, rule-based metrics (numeric correctness, dual groundedness checks, contextual/clarification/refusal correctness, tool-call efficiency) with no LLM-as-judge in the loop.
    - Implemented four interchangeable agent architectures (LangGraph state machine, ReAct, context-stuffing, plan-and-execute) behind a single agent adapter interface to validate that the framework's metrics meaningfully discriminate between designs.
    - Authored a research-style comparison report identifying concrete architecture trade-offs (e.g., a 50%-vs-100% groundedness gap, tool-call efficiency differences) from failure-trace-level analysis.
  variants:
    general:
      bullets:
        - Built an architecture-agnostic framework scoring agentic LLM systems on six deterministic, rule-based metrics (numeric correctness, dual groundedness checks, contextual/clarification/refusal correctness, tool-call efficiency) with no LLM-as-judge.
        - Implemented four interchangeable agent architectures (LangGraph state machine, ReAct, context-stuffing, plan-and-execute) behind one adapter interface; the comparison report shows concrete trade-offs (e.g., 50%-vs-100% groundedness).
  short: deterministic evaluation of agentic LLM systems across four architectures
---

## The problem

Agent evaluations often use a second LLM as the judge, which is expensive, noisy and hard to trust. I wanted metrics that are deterministic, cheap to rerun, and sharp enough to tell two agent designs apart.

The test bed is a personal-finance Q&A agent over a synthetic transaction history. Every question in that domain ("how much did I spend on dining in Q1?") has exactly one correct answer that can be computed from the data, so answers can be checked by rules instead of by another model.

## What I built

- **Six metrics, each a deterministic function of the agent's trace:** numeric correctness; groundedness, computed twice (the agent's own check, and the same check re-run independently by the harness); contextual correctness in multi-turn conversations; asking for clarification when, and only when, it should; refusing out-of-scope questions; and tool-call efficiency against a hand-verified optimal count.
- **One interface for any agent:** `AgentAdapter.run_turn(question, prior_turns) -> RunTrace`. Anything that implements it can be scored, compared and tracked across runs.
- **Four architectures to compare:** a LangGraph state machine (contextualize, route, act, draft, ground-check), a monolithic ReAct loop, a context-stuffing design with no tool calls, and plan-and-execute.
- **A deterministic synthetic dataset:** 18 months of transactions with two injected anomalies, and 15 test cases covering lookups, comparisons, trends, ambiguity, out-of-scope questions, multi-turn follow-ups and an adversarial case.

## Result

All four architectures, using the same model (`gemini-3.5-flash-lite`), the same tools and the same data:

![Grouped horizontal bar chart of seven evaluation metrics for four agent architectures. LangGraph scores 100% on numeric correctness, both groundedness checks, contextual correctness and refusal, but only 86.7% on clarification and 16.7% on efficiency. Monolithic ReAct is 100% on groundedness and refusal but 50% on contextual correctness. Context-stuffing is the most efficient at 100% but scores 50% on groundedness and 0% on contextual correctness. Plan-and-execute is 100% on groundedness, contextual correctness and refusal, 75% on numeric correctness and 66.7% on efficiency.](figures/architecture-comparison.svg "Scores of the four architectures on each metric, with the best in each row in bold.")

No architecture wins every row. The state machine is the most correct but the least efficient, because it can probe repeatedly. Context-stuffing is efficient by construction, but its groundedness collapses: when "the evidence" is a whole table of monthly totals, almost any number can be found in it, so a groundedness check can't tell right from wrong. Plan-and-execute fails differently again: once its single upfront plan asks for too little, it has no chance to correct itself.

## What I learned

The test cases also exposed a gap shared by every architecture: none was told the dataset's date range, so "this year" and "recently" were resolved inconsistently. That is a fix to the evaluation setup, not a difference between architectures, and the report says so. With 15 cases and a single run per architecture, the percentages are best read as pointers to concrete failure traces, which the report walks through one by one.
