---
title: I Built My Dad a Local AI Translator for His Stock Research
published: false
tags: devchallenge, weekendchallenge, hf26challenge, opensource
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).*

## What I built

I built **Argus Friend Brief**, a local AI research translator for my dad.

My dad uses [Argus](https://github.com/apurva0510/argus), a stock-research dashboard I built for our family, every day. It tracks 53 companies across AI infrastructure, semiconductors, power, cooling, networking, and emerging compute. Argus brings prices, technical metrics, peer-relative valuation, news, SEC filings, and bull/bear theses into one place.

That solved the scattered-data problem, but it created another one: a dashboard can show everything and still make the reader do the hard work of connecting it.

Argus Friend Brief takes a sanitized snapshot of that research and asks a local Gemma model to explain one company in plain language. The result is organized into five questions:

- What changed?
- Why does it matter?
- What supports the bull case?
- What supports the bear case?
- What should we monitor next?

Every factual claim links back to the exact evidence record that supported it. The app is research support only. It does not produce buy, sell, hold, price-target, or position-sizing advice.

## Demo

**Live demo:** [argus-friend-brief.streamlit.app](https://argus-friend-brief.streamlit.app/)

**Recorded walkthrough:** [Watch the MP4 on GitHub](https://github.com/apurva0510/argus-friend-brief/blob/main/artifacts/argus-friend-brief-demo.mp4)

The hosted preview includes saved, citation-validated Gemma examples for NVDA, VRT, and
CEG so it works without a cloud GPU. Those outputs are clearly labeled in the interface.
Clone the repository and run Ollama locally to generate a fresh brief for any of the 53
companies.

The current demo includes sanitized snapshots for all 53 active companies in Argus, refreshed after the October 2 market close. It can run entirely on a laptop after the model has been downloaded.

**What my dad said (paraphrased):** “This helps me break down the research into terms
that are much easier to digest, instead of having to navigate a bunch of technical
dashboards.”

## Code

{% github apurva0510/argus-friend-brief %}

Repository: [github.com/apurva0510/argus-friend-brief](https://github.com/apurva0510/argus-friend-brief)

The project is intentionally small:

- Streamlit provides the interface.
- A read-only exporter creates a sanitized JSON snapshot from Argus's local SQLite database.
- Ollama runs `gemma3:4b` locally.
- Pydantic defines the response schema.
- Citation and language guards validate the result before it reaches the screen.

The committed demo snapshot means someone can inspect the project without access to my production database or Supabase credentials.

## How I built it

The data path is straightforward:

```text
Argus SQLite database
        |
        | immutable, read-only export
        v
Sanitized evidence catalog
        |
        | local inference
        v
Gemma 3 4B through Ollama
        |
        | structured JSON
        v
Citation and safety validation
        |
        v
Streamlit briefing
```

### A deliberately narrow snapshot

The exporter opens the Argus database with SQLite's read-only and immutable options. It collects current and previous metrics, signals, fundamentals, peer valuation, existing deterministic theses, recent news, and SEC filings.

It deliberately leaves out personal watchlist notes, authentication data, and credentials. Each exported fact gets a compact evidence ID such as `NVDA.E001`, plus its label, value, date, and source.

### Constrained local generation

The model does not receive the database or an open-ended question. It receives one company's evidence catalog and a Pydantic-derived JSON schema. Temperature is set to zero, and the prompt tells the model to use only the supplied evidence.

Each generated claim must include one to three evidence IDs. The interface uses those IDs to display the underlying values and source dates in expandable evidence panels.

### Failing closed

My first real Gemma run exposed a problem that the mocked tests did not. The model returned valid JSON but mistyped long, timestamp-heavy citation IDs. Even its repair attempt failed.

I shortened the IDs to deterministic forms such as `NVDA.E001` and reran the same test. Citation validation then passed.

The next browser test found a subtler issue: Gemma described Argus's internal “opportunity score” as if it were an investment opportunity. That is not what the score means. I added a deterministic language guard for investment-direction phrases and clarified the prompt: the opportunity score is a research-ranking signal, not an expected return or recommendation.

If a response contains an unknown citation or disallowed language, the app gives the model one repair attempt. If the repaired response still fails, the app displays an error instead of an unsupported brief.

The repository currently has 20 tests covering snapshot lookup, read-only export behavior,
structured Ollama requests, citation validation, repair behavior, the language guard, saved
demo briefs, and privacy-preserving trace metadata. I also tested the complete flow with the
real local model and verified the interface in a browser.

### Observing the local agent without uploading its research

I added optional Sentry agent tracing around the briefing pipeline, Ollama calls, and both
validation passes. The traces show model latency, token counts, whether citation or safety
validation failed, whether the repair path ran, and generic inference failure types.

The instrumentation disables automatic integrations and does not send tickers, prompts,
model responses, evidence catalogs, URLs, exception messages, or personal notes. Without a
`SENTRY_DSN`, it is a no-op and the application remains fully local. This lets me debug the
agent's behavior without turning the observability tool into another copy of my dad's data.

### Preserving the development decisions with Entire

I enabled Entire for the repository and connected its Codex hooks so the implementation
history is attributable to the agent session that produced it. Entire checkpoints preserve
the relationship between a change and the conversation behind it, which is especially useful
here because several of the most important improvements came from testing real model behavior:
shortening citation IDs, tightening investment-language safeguards, and limiting Sentry to
metadata-only traces.

The integration is repository-scoped, telemetry is disabled, and automatic checkpoint pushing
is off. That keeps the captured history under my control while still providing verifiable
development provenance. This submission update was made in a fresh Codex session after the
repository hooks were reviewed and approved, creating the project's first attributable Entire
checkpoint.

## Why does open innovation matter?

The most important feature is not that this app has a chat-like interface. It is where the reasoning happens.

My dad's watchlists and research context do not need to leave his laptop. Once Gemma is downloaded, inference runs locally through Ollama without sending the snapshot to a model provider. There is no per-request fee, API account, or service dependency.

Open weights also let me inspect and change the full behavior around the model. I can replace Gemma with another compatible local model, change the context window, tighten the schema, or build different validators without redesigning the application around one vendor's API.

That flexibility mattered during development. The model's first citation format was unreliable, so I changed the evidence contract. Its first interpretation of an internal score was too strong, so I added a guard and changed the prompt. The surrounding code decides what is acceptable; the model is one replaceable part of the system.

A closed API could generate similar prose. Local, open-weight inference made the privacy, cost, repairability, and model-swapping properties part of the product itself. For a small family research tool, those properties matter more than access to the largest hosted model.

That tradeoff also shows up across the DEV community. Projects like
[Genie](https://dev.to/asimie/genie-building-a-privacy-first-autonomous-agent-that-controls-your-phone-entirely-offline-4da2)
and this [local Gemma SEO agent](https://dev.to/avraham_aminov_542e8309b6/building-a-local-ai-seo-agent-with-gemma-ollama-docker-and-react-303j)
approach local inference from different directions, but reach the same useful conclusion:
privacy and control can be product features, not just deployment details.

## My agent session

I curated the build history into a short, secret-scrubbed DevRelay session covering the
scope decisions, snapshot refresh, safety fixes, local Gemma validation, and browser demo.

{% agent_session 385 %}

[Open the agent session on DEV](https://dev.to/agent_sessions/building-argus-friend-brief-with-local-gemma-wtfqtx)

## Prize categories

- **Best Use of Gemma** — Argus Friend Brief runs Gemma 3 4B locally through Ollama as the core research-translation engine.
- **Best Use of Sentry Agent Tracing** — metadata-only traces cover local model calls, validation failures, repair attempts, token usage, latency, and generic inference failures.
- **Best Use of Entire** — repository-scoped Codex hooks connect this change to its development session, preserving attributable implementation history without automatically publishing it.
