# Perk SignalOps Agent

Production-shaped account research and qualification agent for a Perk-style Revenue Systems workflow.

This project demonstrates a reusable multi-step AI-agent pattern for GTM operations: ingest Clay-style account data, enrich it, generate a research brief, score ICP fit, route the account with deterministic rules, and write structured outputs into a Salesforce-like CRM table.

## Why This Exists

Perk sells travel and spend automation. Its revenue team needs to decide which companies are worth pursuing, why now, which pain matters most, and which sales motion should own the account.

Manual account research does not scale well across outbound, enrichment, Salesforce hygiene, and rep preparation. This demo shows how a Revenue Systems team could automate the repeatable parts while routing uncertain cases to a human review queue.

## Workflow

1. **Input**
   - Company name/domain or CSV of leads.
   - Demo input is `data/sample_leads.csv`, shaped like a Clay export.

2. **Enrichment**
   - Adds firmographic fields, source URLs, and data-quality notes.
   - The project includes an HTTP client with timeout and retry support for future live enrichment.

3. **Research**
   - Uses a replayable LLM provider for deterministic demos and tests.
   - `ReplayLLMProvider` reads saved structured outputs from `data/replay_llm_responses.json`.
   - `HeuristicLLMProvider` handles accounts not found in the replay file.

4. **Scoring**
   - Produces a structured fit score, confidence, ICP matches/gaps, primary pain, and rationale.
   - Scoring is deterministic and testable.

5. **Routing**
   - Uses non-LLM decision logic.
   - High score + high confidence: `auto_qualify`.
   - Low confidence or medium fit: `human_review`.
   - Low fit with sufficient confidence: `reject`.

6. **CRM Writeback**
   - Writes structured records into SQLite as a Salesforce-style stand-in.
   - Fields include fit score, confidence, region, segment, sales motion, owner queue, next action, and review reason.

7. **Observability**
   - Every step writes structured JSONL events to `data/agent_runs.jsonl`.
   - The Streamlit UI shows CRM records, confidence scores, routing decisions, and flagged items.

## Architecture

```text
CSV / Lead Input
      |
      v
EnrichmentStep
      |
      v
ResearchStep -> ReplayLLMProvider / HeuristicLLMProvider
      |
      v
ScoringStep
      |
      v
RoutingStep
      |
      v
SQLiteCRMWriter
      |
      v
Streamlit dashboard + JSONL trace logs
```

The framework layer lives in `src/signalops/framework.py`. Each workflow step implements the same `AgentStep` contract, so a second workflow, such as an outbound-email drafter or renewal-risk agent, can reuse the same scaffolding.

## Run The Demo

From this folder:

```bash
PYTHONPATH=src python3 run_pipeline.py
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Optional UI:

```bash
python3 -m pip install "streamlit>=1.36"
PYTHONPATH=src python3 -m streamlit run app.py
```

## What This Proves For The Perk Role

- Multi-step agent pipeline, not a single prompt.
- Python implementation with reusable step abstractions.
- Replayable LLM outputs for deterministic testing.
- Confidence threshold and human review queue.
- Deterministic routing logic outside the LLM.
- Structured logging for traceability.
- CRM-style writeback through an API-like writer layer.
- Thin UI for non-technical GTM/RevOps visibility.
- Clear path to plug in OpenAI, Claude, Salesforce, Clay, Apollo, Outreach, or enrichment APIs.

## Production Extensions

- Replace replay provider with OpenAI/Claude structured-output provider.
- Replace SQLite writer with Salesforce REST API writes.
- Add live enrichment connectors for Clay, Apollo, Clearbit-like APIs, job posts, funding/news signals, and company sites.
- Add async queueing and idempotency keys for batch processing.
- Add row-level approval actions in the review queue.
- Add evaluation sets for false positives, false negatives, and hallucinated evidence.
