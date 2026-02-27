# Insight Tool — Confirmed UX Flow & Project Plan

---

## Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| Guide input | Upload pre-written guide, AI reviews and recommends improvements | Researcher owns the guide; AI adds value through review, not generation |
| Theme approach | Start inductive (emergent), add deductive codebook later | Simpler MVP; themes emerge from data rather than pre-defined hypotheses |
| PII handling | Full anonymisation pipeline from day one | Privacy-first; participants must be protected before any AI processing |
| Architecture | Moderate — key agents, not full 12-agent orchestration | Lean enough to build, robust enough to handle batch uploads and multi-transcript synthesis |
| Transcript format | Markdown from Askable (primary), with extensible parser | Matches the team's actual workflow |
| Report framing | Customer pains, goals, and behaviours | User-centered framing that feeds directly into design work |
| Insight output | Structured JSON with full citation trail | Portable, traceable, machine-readable |

---

## UX Flow — Six Steps

```
STEP 1             STEP 2              STEP 3              STEP 4             STEP 5              STEP 6
Upload &           Upload Raw           Organise            Theme              Insight             Report
Review Guide       Transcripts          Transcripts         Extraction         Synthesis           Generation
    │                  │                    │                   │                  │                   │
Upload guide    Upload markdown      AI maps responses    AI surfaces       Combine all         Generate report:
    │           transcript(s)        against guide        emergent themes   transcripts         pains, goals,
    ▼           from Askable         sections + time      per transcript    and group           behaviours
AI reviews         │                 brackets             with quotes +     patterns across        │
structure,         ▼                    │                  traceability      themes                 ▼
flags issues,   PII scan +              ▼                    │                  │              Evidence-backed
recommends      anonymisation       Table view for           ▼                  ▼              deliverable
improvements    (full pipeline)     researcher review    Theme list with    JSON insights
    │              │                                     source trail       with hero quotes,
    ▼              ▼                                                        citations, and
Lock guide      Batch upload                                                participant counts
                supported
```

---

## Step 1 — Upload & Review Research Guide

**What the researcher does:**
- Creates a research plan and interview guide outside the tool (as they normally would)
- Uploads the guide file to start a new project
- The guide contains: research objective, research goals, and a conversation interview guide with questions organised under key sections that align with discovery goals
- Each section includes **rough time brackets** to aid organisation of data later

**What AI does:**
- Parses the guide structure — identifies sections, questions, objectives, and time brackets
- Reviews the guide for quality:
  - Flags leading or ambiguous questions
  - Checks question-to-objective coverage (any objectives without questions?)
  - Estimates session duration against time brackets
  - Suggests probe questions where depth may be needed
- Presents recommendations to researcher

**What the researcher decides:**
- Accept, edit, or dismiss AI recommendations
- Lock the guide — this becomes the framework for all downstream analysis

**Data model — Research Guide:**

```yaml
research_guide:
  project_name: str
  objective: str
  research_goals: str[]
  sections:
    - section_id: str
      section_name: str
      time_bracket: str              # e.g. "0:00–10:00"
      questions:
        - question_id: str
          question_text: str
          mapped_goal: str           # links to research_goals
          required: bool
          probes: str[]              # follow-up prompts
          ai_flags: AiFlag[]         # leading, ambiguous, etc.
  version: int
  locked: bool
```

**Interface:** Structured view with inline editing. Guide sections displayed as expandable cards. AI flags shown inline with accept/dismiss actions.

---

## Step 2 — Upload Raw Transcript Data

**What the researcher does:**
- Finishes an interview on Askable
- Uploads the raw markdown transcript file(s) to the project
- Can upload multiple transcripts at once (batch upload)

**What AI does:**
- Parses markdown into canonical speaker turns: `{speaker, text, timestamp, turn_index}`
- Runs full PII anonymisation pipeline (locally, before any LLM call):
  - Auto-redacts high-confidence PII (names, emails, phone numbers)
  - Flags low-confidence items for researcher review (third-party names, company names, locations)
  - Flags sensitive disclosures for exclusion
- Presents anonymisation review to researcher

**What the researcher decides:**
- Reviews each flagged PII item — redact or keep
- Confirms anonymisation
- Original transcript is permanently discarded after confirmation

**Anonymisation pipeline:**

```
Upload markdown transcript(s)
      │
      ▼
PII scan (local — Presidio — before any AI call)
      │
      ▼
Anonymisation review ← HUMAN GATE
  - Auto-redacted items shown for confirmation
  - Low-confidence items require researcher decision
      │
      ▼
Discard original ← PERMANENT
      │
      ▼
AI processing runs on anonymised text only
```

**PII replacement tokens:**

| PII type | Token | Default |
|---|---|---|
| Participant name | `[PARTICIPANT]` | Auto-redact (high confidence) |
| Interviewer name | `[INTERVIEWER]` | Auto-redact always |
| Third-party names | `[NAME]` | Flag for review |
| Email | `[EMAIL]` | Auto-redact always |
| Phone | `[PHONE]` | Auto-redact always |
| Company names | `[COMPANY]` | Flag for review |
| Locations | `[LOCATION]` | Flag for review |

**Batch upload:** When multiple transcripts are uploaded at once, each runs through the anonymisation pipeline independently. Researcher reviews each before AI analysis begins. All transcripts in a batch can be processed in parallel after anonymisation is confirmed.

**Data model — Session:**

```yaml
session:
  session_id: str
  participant_id: str               # auto-generated: P01, P02...
  transcript: Turn[]                 # anonymised only
  anonymisation_log:
    auto_redacted: int
    researcher_reviewed: int
    exclusions: int
  upload_timestamp: datetime
  status: anonymised | organised | themed | complete
```

---

## Step 3 — AI Organises Transcripts Against Guide Sections

**What AI does:**
- Takes each anonymised transcript and maps participant responses to the corresponding guide sections and questions
- Uses the time brackets from the guide as a primary organising signal, supplemented by semantic matching
- Produces a structured table view per transcript

**What the researcher sees:**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Transcript: P01  ·  Session 1 of 6                                           │
│                                                                                │
│  Guide Section          Time Bracket   Covered?   Participant Responses        │
│  ─────────────────────────────────────────────────────────────────────────     │
│  1. Warm-up             0:00–5:00      Yes        "I've been using it for      │
│                                                    about 3 months now..."       │
│                                                                                │
│  2. Current Workflow    5:00–15:00     Yes        "Usually I start by          │
│                                                    opening the dashboard..."    │
│                                                    "The export thing is         │
│                                                    really frustrating..."       │
│                                                                                │
│  3. Pain Points         15:00–25:00    Partial    "I just kept clicking on      │
│                                                    different tabs..."           │
│                                                    [See 4 more responses]       │
│                                                                                │
│  4. Ideal State         25:00–35:00    No         —                            │
│     ⚠ Not covered — ran long on Pain Points                                   │
│                                                                                │
│  5. Wrap-up             35:00–40:00    Yes        "If I could change one       │
│                                                    thing it would be..."        │
│                                                                                │
│  Off-script responses (not mapped to guide):                                   │
│  [00:22:14] "My manager [NAME] actually showed me a workaround..."            │
│  [00:31:02] "I tried using [COMPANY]'s tool instead..."                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

**What the researcher decides:**
- Review the AI's mapping — are responses correctly assigned to sections?
- Drag/move misplaced responses to the correct section
- Note which guide sections were skipped or shallow

**Data model — Organised Transcript:**

```yaml
organised_transcript:
  session_id: str
  participant_id: str
  section_mappings:
    - section_id: str
      section_name: str
      time_bracket: str
      coverage_status: covered | partial | not_covered
      mapped_turns:
        - turn_index: int
          speaker: str
          text: str
          timestamp: str
          mapping_confidence: float
      coverage_notes: str             # AI explanation if not covered
  off_script_turns: Turn[]            # responses that don't map to any section
```

---

## Step 4 — AI Extracts Key Themes (Per Transcript)

**What AI does:**
- Works through each organised transcript individually
- Surfaces emergent themes — recurring patterns, notable observations, strong sentiments
- Every theme is grounded in specific quotes with full traceability (participant ID, timestamp, guide section)
- Themes are inductive — they emerge from the data, not from a pre-defined framework

**What the researcher sees:**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Themes: P01  ·  Session 1                                    4 themes found   │
│                                                                                │
│  ── Theme 1: Navigation Confusion ─────────────────────────────────────────   │
│  Participant repeatedly expressed difficulty finding features                   │
│  within the interface.                                                         │
│                                                                                │
│  Supporting evidence:                                                          │
│  • "I just kept clicking on different tabs hoping to find settings."           │
│    — P01, 00:12:34, Section 3 (Pain Points)                                   │
│  • "The menu doesn't make sense to me, I never know where things are."        │
│    — P01, 00:18:02, Section 3 (Pain Points)                                   │
│  • "I asked [NAME] where to find the export button."                          │
│    — P01, 00:22:14, Off-script                                                │
│                                                                                │
│  Instances: 3  ·  Guide sections: Pain Points, Off-script                     │
│                                                                                │
│  [Accept]  [Edit]  [Merge with...]  [Discard]                                 │
│                                                                                │
│  ── Theme 2: Workaround Reliance ──────────────────────────────────────────   │
│  ...                                                                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

**What the researcher decides:**
- Review each theme — accept, edit, merge, or discard
- Confirm that evidence is correctly attributed
- Add manual themes if something was missed

**Traceability contract:** Every theme must include:
- Theme name and description
- At least one verbatim quote
- Participant ID, timestamp, and guide section for every quote
- Instance count

**Data model — Themes:**

```yaml
session_themes:
  session_id: str
  participant_id: str
  themes:
    - theme_id: str
      theme_name: str
      theme_description: str
      evidence:
        - quote: str
          participant_id: str
          timestamp: str
          turn_index: int
          guide_section: str
          guide_question_id: str | null
      instance_count: int
      status: proposed | accepted | merged | discarded
      researcher_notes: str | null
```

---

## Step 5 — Cross-Transcript Insight Synthesis

**What AI does:**
- Combines all accepted themes across all transcripts
- Groups themes that share patterns — identifies common pains, shared behaviours, recurring observations
- Creates candidate insights from each grouping:
  - **Insight summary** — a paragraph capturing the finding
  - **Highlight quote** — the single best quote that represents the theme
  - **Full citation trail** — every supporting quote with participant ID, timestamp, session, and guide section
  - **Participant count** — how many participants exhibited this pattern
- Outputs structured JSON

**What the researcher sees:**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Candidate Insights                          Sort: Participant count ▼         │
│                                                                                │
│  ── Insight 1 ─────────────────────────────────────────────────────────────   │
│  Theme Group: Navigation Confusion + Workaround Reliance                      │
│                                                                                │
│  "Participants consistently struggle to locate core features within            │
│   the interface, leading them to develop their own workarounds rather          │
│   than engaging with the product's intended navigation. This suggests          │
│   a fundamental mismatch between the product's information architecture        │
│   and users' mental models of where things should be."                         │
│                                                                                │
│  Highlight quote:                                                              │
│  "I honestly just Googled it — I didn't think there was help in the app."     │
│  — P03, 00:13:15, Session 3, Section 3 (Pain Points)                          │
│                                                                                │
│  Evidence: 5/6 participants  ·  14 instances across 5 sessions                │
│  Sources: P01 (3), P02 (2), P03 (4), P04 (2), P05 (3)                        │
│                                                                                │
│  [Expand full evidence trail]                                                  │
│  [Accept]  [Edit]  [Reject]  [Merge with...]                                  │
│                                                                                │
│  ── Insight 2 ─────────────────────────────────────────────────────────────   │
│  ...                                                                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

**JSON output structure:**

```json
{
  "project_name": "Onboarding Research — Feb 2026",
  "generated_at": "2026-02-27T10:30:00Z",
  "total_sessions": 6,
  "total_participants": 6,
  "insights": [
    {
      "insight_id": "INS-001",
      "theme_group": ["Navigation Confusion", "Workaround Reliance"],
      "insight_summary": "Participants consistently struggle to locate core features within the interface, leading them to develop their own workarounds rather than engaging with the product's intended navigation. This suggests a fundamental mismatch between the product's information architecture and users' mental models of where things should be.",
      "highlight_quote": {
        "text": "I honestly just Googled it — I didn't think there was help in the app.",
        "participant_id": "P03",
        "timestamp": "00:13:15",
        "session_id": "S03",
        "guide_section": "Pain Points"
      },
      "supporting_evidence": [
        {
          "quote": "I just kept clicking on different tabs hoping to find settings.",
          "participant_id": "P01",
          "timestamp": "00:12:34",
          "session_id": "S01",
          "guide_section": "Pain Points"
        },
        {
          "quote": "I asked my colleague where to find the export button.",
          "participant_id": "P01",
          "timestamp": "00:22:14",
          "session_id": "S01",
          "guide_section": "Off-script"
        }
      ],
      "participant_count": 5,
      "total_instances": 14,
      "participants": ["P01", "P02", "P03", "P04", "P05"],
      "status": "proposed"
    }
  ]
}
```

**What the researcher decides:**
- Accept, edit, reject, or merge each insight
- Edit the summary paragraph and highlight quote selection
- Verify the evidence trail is accurate and complete
- Promote accepted insights to the report

---

## Step 6 — Report Generation (Pains, Goals, Behaviours)

**What AI does:**
- Compiles accepted insights into a structured report
- Organises findings around three lenses:
  - **Customer Pains** — friction, frustration, blockers
  - **Customer Goals** — what participants are trying to achieve, their motivations
  - **Customer Behaviours** — what they actually do (workarounds, patterns, habits)
- Each section is backed by evidence from the insight synthesis
- Generates observations and recommendations

**What the researcher sees:**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Research Report — Onboarding Feb 2026                                        │
│                                                                                │
│  CUSTOMER PAINS                                                                │
│  ────────────────────────────────────────────────────────────────────────      │
│  1. Navigation confusion is universal — 5/6 participants struggled to          │
│     locate core features, suggesting a fundamental IA mismatch.                │
│     Evidence: INS-001 (14 instances)  [View evidence]                         │
│                                                                                │
│  2. Export workflow creates significant friction — 4/6 participants             │
│     described the export process as their biggest pain point.                   │
│     Evidence: INS-003 (9 instances)  [View evidence]                          │
│                                                                                │
│  CUSTOMER GOALS                                                                │
│  ────────────────────────────────────────────────────────────────────────      │
│  1. Participants want self-service answers — they expect to find               │
│     help within the product without contacting support.                        │
│     Evidence: INS-002 (11 instances)  [View evidence]                         │
│                                                                                │
│  CUSTOMER BEHAVIOURS                                                           │
│  ────────────────────────────────────────────────────────────────────────      │
│  1. When stuck, participants default to external workarounds (Google,          │
│     colleagues) rather than in-product help.                                   │
│     Evidence: INS-001, INS-002 (12 instances)  [View evidence]                │
│                                                                                │
│  OBSERVATIONS                                                                  │
│  ────────────────────────────────────────────────────────────────────────      │
│  - Guide Section 4 (Ideal State) was skipped in 3/6 sessions                  │
│  - Export pain emerged organically — was not in original research goals        │
│                                                                                │
│  [Edit any section]  [Export PDF]  [Export JSON]                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

**What the researcher decides:**
- Edit any section of the report
- Reorder findings
- Add manual observations
- Finalise and export

---

## Agent Architecture (Moderate)

Six key agents, each owning a single concern. No full orchestrator — the backend manages sequencing.

```
                    ┌─────────────────────────────┐
                    │      BACKEND (FastAPI)       │
                    │                              │
                    │  - Manages project state     │
                    │  - Routes to agents          │
                    │  - Handles batch uploads     │
                    │  - Manages PII pipeline      │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  SETUP AGENTS              PER-SESSION AGENTS         SYNTHESIS AGENTS

  ┌──────────────┐     ┌─────────────────────┐    ┌──────────────────┐
  │ Guide        │     │ Transcript          │    │ Insight          │
  │ Reviewer     │     │ Organiser           │    │ Synthesiser      │
  │              │     │                     │    │                  │
  │ - Parse      │     │ - Map responses to  │    │ - Group themes   │
  │   structure  │     │   guide sections    │    │   across all     │
  │ - Flag       │     │ - Table view output │    │   transcripts    │
  │   issues     │     │                     │    │ - Generate       │
  │ - Recommend  │     └─────────────────────┘    │   insights       │
  │   probes     │                                │ - JSON output    │
  └──────────────┘     ┌─────────────────────┐    └──────────────────┘
                       │ Theme               │
                       │ Extractor           │    ┌──────────────────┐
                       │                     │    │ Report           │
                       │ - Emergent themes   │    │ Generator        │
                       │ - Quote extraction  │    │                  │
                       │ - Traceability      │    │ - Pains / Goals  │
                       └─────────────────────┘    │   / Behaviours   │
                                                  │ - Evidence links │
                                                  │ - Export         │
                                                  └──────────────────┘

  + PII Anonymiser (Presidio — runs locally, not an LLM agent)
```

**Agent details:**

| Agent | Input | Output | LLM | Notes |
|---|---|---|---|---|
| **Guide Reviewer** | Uploaded guide file | Parsed structure + quality flags + recommendations | Claude Sonnet | Runs once per project |
| **Transcript Organiser** | Anonymised transcript + locked guide | Section-mapped table view | Claude Sonnet | Runs per transcript; parallelisable for batch |
| **Theme Extractor** | Organised transcript | Emergent themes with evidence trail | Claude Sonnet (temp 0.3) | Runs per transcript after organisation |
| **Insight Synthesiser** | All accepted themes across transcripts | Candidate insights as JSON | Claude Sonnet (extended thinking) | Runs on-demand when researcher is ready |
| **Report Generator** | Accepted insights | Structured report (pains/goals/behaviours) | Claude Sonnet | Runs after insight review |
| **PII Anonymiser** | Raw transcript | Anonymised transcript + redaction log | Presidio (local) | No LLM — runs locally before any AI call |

**Batch upload handling:** When multiple transcripts are uploaded at once:
1. Each runs through PII Anonymiser independently
2. Researcher reviews anonymisation for each
3. After confirmation, Transcript Organiser runs in parallel for all confirmed transcripts
4. Theme Extractor runs in parallel for all organised transcripts
5. Insight Synthesiser waits until all transcripts are themed and reviewed

---

## Technical Stack

| Component | Technology | Why |
|---|---|---|
| **Backend** | FastAPI (Python) | Orchestrates agents, serves API, handles file uploads |
| **Database** | Supabase (PostgreSQL) | Project state, transcripts, themes, insights — with auth and row-level security |
| **File storage** | Supabase Storage | Guide and transcript uploads |
| **Auth** | Supabase Auth | Team login |
| **Frontend** | React | Table views, structured editing, report preview |
| **AI** | Claude API (Sonnet 4.6) | All analysis agents |
| **PII detection** | Presidio (local) | Anonymisation before any LLM call |
| **Validation** | Pydantic | Typed agent inputs/outputs |
| **Transcript parsing** | Custom markdown parser | Askable markdown format |

---

## Build Phases

### Phase 1 — MVP
*Goal: Upload guide + transcripts, organise against guide, extract themes*

- [ ] Guide upload + AI parsing of structure (sections, questions, time brackets)
- [ ] Guide review — AI flags and recommendations
- [ ] Markdown transcript parser (Askable format)
- [ ] PII anonymisation pipeline (Presidio + human review gate)
- [ ] Transcript organisation against guide sections (table view)
- [ ] Theme extraction per transcript with traceability
- [ ] Basic project/session management (create project, upload files, view results)

### Phase 2 — Synthesis & Reports
*Goal: Cross-transcript insights and report generation*

- [ ] Cross-transcript theme grouping and pattern detection
- [ ] Insight synthesis with JSON output (summary, hero quote, citations)
- [ ] Researcher review/edit of insights
- [ ] Report generation (pains, goals, behaviours)
- [ ] Report export (PDF, JSON)
- [ ] Batch transcript upload with parallel processing

### Phase 3 — Enhancements
*Goal: Codebook support, deeper analysis, polish*

- [ ] Deductive codebook support (upload or AI-seeded)
- [ ] Hybrid theme approach (deductive + inductive)
- [ ] Cross-session heatmap visualisation
- [ ] Saturation tracking
- [ ] Guide evolution tracking (version diffs across sessions)
- [ ] RAG-powered Q&A across all sessions

---

## Data Storage Model

```
┌───────────────────────────────────────────────────────────────────┐
│  STORED                               NOT STORED                  │
│                                                                   │
│  ✓ Anonymised transcript              ✗ Original transcript       │
│  ✓ Participant IDs (P01, P02...)      ✗ Participant real names    │
│  ✓ Organised transcript (table)       ✗ PII / personal data      │
│  ✓ Themes with evidence              ✗ Sensitive disclosures     │
│  ✓ Insights (JSON)                   ✗ ID-to-name mapping        │
│  ✓ Report                            ✗ Askable profile data      │
│  ✓ Research guide (versioned)                                     │
│  ✓ Anonymisation log                                              │
└───────────────────────────────────────────────────────────────────┘
```

---

## Navigation Structure

```
PROJECTS
└── [Project name]
    ├── Research Guide          (upload → AI review → lock)
    ├── Sessions
    │   ├── Session 1           (upload → anonymise → organise → theme)
    │   ├── Session 2
    │   └── ... (batch upload supported)
    ├── Themes                  (per-transcript, reviewable)
    ├── Insights                (cross-transcript synthesis, JSON)
    ├── Report                  (pains / goals / behaviours)
    └── Data & Privacy          (retention, delete study)
```
