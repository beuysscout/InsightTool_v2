# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Insight Tool is an AI-augmented research analysis platform that analyzes customer interview transcripts to produce evidence-backed insights for product design opportunities. The project is currently in the **planning/pre-implementation phase** — the repository contains a comprehensive research plan (`researchplan.md`) but no source code yet.

## Repository Status

- `researchplan.md` — The sole deliverable so far: a 1,200+ line architectural design document covering workflows, agent specifications, data structures, UI flows, and privacy architecture.
- No build system, tests, linting, or source code exist yet.

## Planned Technical Stack

**Backend:** FastAPI, PostgreSQL, Pydantic (structured output validation)
**Frontend:** React
**AI:** Claude API (Sonnet 4.6) — extended thinking enabled for Brief Agent, Codebook Seeder, and Insight Generator only
**NLP/Parsing:** sentence-transformers (embeddings), webvtt-py, presidio-analyzer (PII detection)
**Analysis:** scikit-learn, pandas, Jinja2 (HTML report generation)
**Config formats:** YAML for research brief, interview guide, and codebook

## Architecture

The system is a **multi-agent orchestration** built around a shared `StudyState` object (persisted in PostgreSQL). Agents are idempotent and communicate only through StudyState mutations managed by the FastAPI service.

### Four workflow phases:

1. **Pre-Research** (once per study) — Brief Agent, Guide Generator Agent, Codebook Seeder Agent convert freeform objectives into structured YAML artifacts
2. **Per-Session** (after each interview) — Parser, Guide Coverage, Deductive Coder (run in parallel with Coverage), Inductive Discovery, Session QA, Human Review Gate, Next Session Prep
3. **Cross-Session** (after each reviewed session) — Pattern Aggregator, Saturation Monitor, Codebook Curator
4. **Synthesis & Report** (after data collection) — Insight Generator, Evidence Linker, Report Compiler

### Key design constraints:

- **Privacy-first:** PII is redacted locally (via Presidio) before any LLM call; original transcripts are permanently discarded after anonymization
- **Human-in-the-loop:** Low-confidence codes (<0.6) are never auto-accepted; all synthesis insights require editorial review
- **Embedding pre-filter:** Cosine similarity pre-filter reduces LLM calls by 60-80% before deductive coding
- **Temperature discipline:** `temperature=0` for deductive coding (deterministic); `0.3-0.5` for inductive/insight generation
- **Parallelism:** Guide Coverage and Deductive Coder run concurrently; per-study concurrency cap of 5 parallel agent calls
- **Chunking:** Speaker turns are natural units; long monologues (>300 words) split on sentence boundaries with 150-word windows and 50-word overlap

## Implementation Phases

- **Phase 1 (MVP):** Multi-format transcript parser, guide/codebook upload, embedding pre-filter, LLM deductive coding, guide coverage report, annotated transcript view
- **Phase 2 (Core):** Depth scoring, off-script classification, inductive discovery, cross-session heatmap, saturation tracker, codebook iteration, three-way gap analysis
- **Phase 3 (Advanced):** AI-generated insights, participant segmentation, interviewer behavior analysis, PII redaction pipeline, RAG Q&A, report generation, multi-format export
