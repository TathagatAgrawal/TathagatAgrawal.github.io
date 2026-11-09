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

| Metric | LangGraph | Monolithic ReAct | Context-stuffing | Plan-and-execute |
| --- | ---: | ---: | ---: | ---: |
| Numeric correctness | **100%** | 83.3% | 83.3% | 75.0% |
| Groundedness (self-reported) | **100%** | **100%** | 50.0% | **100%** |
| Groundedness (recomputed) | **100%** | **100%** | 50.0% | **100%** |
| Contextual correctness | **100%** | 50.0% | 0.0% | **100%** |
| Clarification | 86.7% | 80.0% | **93.3%** | **93.3%** |
| Refusal | **100%** | **100%** | **100%** | **100%** |
| Efficiency (calls ≤ optimal) | 16.7% | 50.0% | **100%** | 66.7% |

No architecture wins every row. The state machine is the most correct but the least efficient, because it can probe repeatedly. Context-stuffing is efficient by construction, but its groundedness collapses: when "the evidence" is a whole table of monthly totals, almost any number can be found in it, so a groundedness check can't tell right from wrong. Plan-and-execute fails differently again: once its single upfront plan asks for too little, it has no chance to correct itself.

## What I learned

The test cases also exposed a gap shared by every architecture: none was told the dataset's date range, so "this year" and "recently" were resolved inconsistently. That is a fix to the evaluation setup, not a difference between architectures, and the report says so. With 15 cases and a single run per architecture, the percentages are best read as pointers to concrete failure traces, which the report walks through one by one.
