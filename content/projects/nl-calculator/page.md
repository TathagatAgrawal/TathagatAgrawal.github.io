## What it does

A calculator you talk to. An LLM reads the request, calls arithmetic tools to get exact results, and replies in natural language. Follow-ups such as "now divide that by 2" refer back to the previous answer.

```text
> add 5 and 3, then multiply the result by 2
[tool call] add(a=5, b=3) -> 8.0
[tool call] multiply(a=8, b=2) -> 16.0
The sum of 5 and 3 is 8, and multiplying that by 2 gives 16.
```

## How it works

- **Tool calling with LangChain**, using free models on OpenRouter through its OpenAI-compatible API.
- **Six tools** (add, subtract, multiply, divide, power, square root) as plain Python functions. Each tool's arguments are a Pydantic model, so arguments are validated before the tool runs (the square root rejects negative numbers outright).
- **An agent loop** keeps calling tools and feeding results back until it has a final answer, so chained requests resolve in one go.
- **A UI-independent core:** the conversation session has no command-line code in it, so a web interface could reuse it unchanged.

It is a small project, built to learn tool calling and argument validation properly before using them in larger agents.
