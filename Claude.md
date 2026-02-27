# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Insight Tool is an AI-augmented research analysis platform that analyzes customer interview transcripts to produce evidence-backed insights for product design opportunities.

## Repository Status

- `projectplan.md` — Confirmed project plan — UX flow, data models, agent architecture, and build phases.
- `backend/` — FastAPI backend with Pydantic models, AI agents, and REST API.
- `frontend/` — React + TypeScript frontend with Vite.

## Commands

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev          # dev server on :5173
npx tsc --noEmit     # type check
```

## Codebase Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, router mounts
│   ├── config.py            # Settings (env vars: SUPABASE_URL, ANTHROPIC_API_KEY)
│   ├── models/              # Pydantic models (guide, session, theme, insight, project)
│   ├── api/                 # Route handlers (projects, guides, sessions, themes)
│   ├── agents/              # AI agents (guide_reviewer, transcript_organiser, theme_extractor)
│   ├── services/            # parser.py (markdown→turns), anonymiser.py (Presidio PII)
│   └── db/
│       ├── supabase.py       # Supabase client singleton
│       └── store.py          # Supabase-backed project store (JSONB serialisation)
├── supabase/migrations/      # SQL schema (001_initial_schema.sql)
├── tests/
├── .env                       # SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY (gitignored)
└── pyproject.toml

frontend/
├── src/
│   ├── App.tsx              # Router setup
│   ├── api/client.ts        # API client (all backend calls)
│   ├── types/models.ts      # TypeScript types mirroring backend models
│   └── pages/               # ProjectList, ProjectDetail, GuideReview,
│                              TranscriptUpload, SessionDetail, ThemesOverview
└── package.json
```

## Confirmed UX Flow (6 Steps)

1. **Upload & Review Guide** — Researcher uploads pre-written interview guide. AI parses structure (sections, questions, time brackets) and recommends improvements. Researcher locks guide.
2. **Upload Transcripts** — Markdown transcripts from Askable. Full PII anonymisation pipeline (Presidio, local) with human review gate before any AI processing. Batch upload supported.
3. **Organise Transcripts** — AI maps responses against guide sections and time brackets. Table view for researcher review.
4. **Theme Extraction** — AI surfaces emergent themes per transcript with full traceability (quotes, participant IDs, timestamps, guide sections). Purely inductive — no pre-defined codebook in MVP.
5. **Insight Synthesis** — Cross-transcript pattern grouping. JSON output with insight summaries, hero quotes, and full citation trails.
6. **Report Generation** — Structured around customer pains, goals, and behaviours. Evidence-backed.

## Architecture — Moderate (6 Key Agents)

| Agent | Role | LLM |
|---|---|---|
| Guide Reviewer | Parse guide structure, flag issues, recommend probes | Claude Sonnet |
| Transcript Organiser | Map responses to guide sections (table view) | Claude Sonnet |
| Theme Extractor | Surface emergent themes with evidence trail | Claude Sonnet (temp 0.3) |
| Insight Synthesiser | Group themes across transcripts, generate insights (JSON) | Claude Sonnet (extended thinking) |
| Report Generator | Pains / goals / behaviours report | Claude Sonnet |
| PII Anonymiser | Redact PII before any AI call | Presidio (local, no LLM) |

No full orchestrator — FastAPI backend manages agent sequencing.

## Technical Stack

**Backend:** FastAPI (Python), Pydantic (structured output validation)
**Database:** Supabase (PostgreSQL + Auth + Storage)
**Frontend:** React
**AI:** Claude API (Sonnet 4.6) — extended thinking for Insight Synthesiser only
**PII:** Presidio (local, pre-LLM)
**Transcript format:** Markdown from Askable (primary)

## Key Design Constraints

- **Privacy-first:** PII redacted locally via Presidio before any LLM call; originals permanently discarded after anonymisation confirmation
- **Human-in-the-loop:** All themes, insights, and reports require researcher review before acceptance
- **Traceability:** Every theme and insight must link to verbatim quotes with participant ID, timestamp, and guide section
- **Inductive themes:** MVP uses purely emergent themes; deductive codebook support deferred to Phase 3
- **Batch processing:** Multiple transcripts can be uploaded and processed in parallel after anonymisation
- **JSON outputs:** Insight synthesis produces structured JSON for portability

## Build Phases

- **Phase 1 (MVP):** Guide upload + AI review, markdown transcript parser, PII anonymisation pipeline, transcript organisation (table view), theme extraction with traceability
- **Phase 2 (Synthesis):** Cross-transcript insight synthesis (JSON), report generation (pains/goals/behaviours), batch upload with parallel processing, export (PDF, JSON)
- **Phase 3 (Enhancements):** Deductive codebook support, cross-session heatmap, saturation tracking, guide version tracking, RAG Q&A
